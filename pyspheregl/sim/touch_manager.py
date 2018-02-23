import zmq
import numpy as np
import json
import attr

from ..sphere import sphere

@attr.s
class TouchEvent(object):
    event = attr.ib(default="NONE")
    touch = attr.ib(default=None)

@attr.s
class Touch(object):
    lonlat = attr.ib()
    origin = attr.ib()
    orig_t = attr.ib()
    raw = attr.ib() # raw TUIO coordinates
    t = attr.ib()
    fseq = attr.ib(default=0)
    duration = attr.ib(default=0.0)
    dead_time =attr.ib(default=0.0)
    active_touch =attr.ib(default=0)
    id = attr.ib(default=-1)
    alive = attr.ib(default=False)    
    siblings = attr.ib(default=None)
    feedback = attr.ib(default=-1)


def np_spherical_distance(p1, p2):
    """Given two points p1, p2 (in radians), return
    the great circle distance between the two points."""
    dlon = p2[0] - p1[0]        
    lat1, lat2 = p1[1], p2[1]
    return np.arccos(np.sin(lat1)*np.sin(lat2) + np.cos(lat1)*np.cos(lat2) * np.cos(dlon))
    
from scipy.spatial.distance import pdist, squareform

def cluster_touches(touches, threshold):
    distances = squareform(pdist(np.array(touches), np_spherical_distance))
    ixs = np.tril(np.where(distances<threshold,1 ,0), -1)
    return np.nonzero(ixs)
    

# convert raw frame positions into a stream of events
# either up, drag or down. Remembers origin of drags, and
# tracks duration. Also provides a stable, dense numbering of active touches

class TouchManager:
    def __init__(self, linger_time=5.0, feedback_buf=None):
        self.touches = {}        
        self.feedback_buf = feedback_buf
        # stable, but low numbered slots
        self.active_touches = {}     
        self.graveyard = {}
        self.clusters = {}
        self.touch_linger_time = linger_time

    def cluster_fingers(self):
        touches = []
        for touch in self.active_touches:
            touches.append(self.active_touches[touch].lonlat)
        tfrom, tto = cluster_touches(np.array(touches))

    def feedback(self, lonlat):
        # using the feedback array, look up 
        # the object id underneath this touch point
        if self.feedback_buf is not None:
            size = self.feedback_buf.shape[0]
            # feedback buffers must be square!        
            x, y = sphere.polar_to_display(lonlat[0], lonlat[1], size)            
            return self.feedback_buf[int(y),int(x)]
        else:
            return -1


        
    def touch_frame(self, frame_touches, raw, fseq, t):

        # a new complete frame is issued
        existing, this_frame = set(self.touches.keys()), set(frame_touches.keys())        
        down, move, up = this_frame-existing, this_frame&existing, existing-this_frame

        #self.cluster_fingers()

        events = []
        for touch in down:
            # new touch down

            # find a slot
            active_touch = 0
            while active_touch in self.active_touches:
                active_touch += 1

            # read the value under the finger (i.e. what is being touched)
        
                                    
            self.touches[touch] = Touch(origin=frame_touches[touch], lonlat=frame_touches[touch], orig_t=t,
                                        t=t, fseq=fseq, duration=0.0, dead_time=0.0, active_touch=active_touch, id=touch, alive=True,
                                        raw=raw[touch], feedback=self.feedback(frame_touches[touch]))            
            self.active_touches[active_touch] = self.touches[touch]
            
            # create the event
            events.append(TouchEvent(event="DOWN", touch=self.touches[touch]))
                        
        for touch in move:
            # touch move
            self.touches[touch].lonlat = frame_touches[touch]
            self.touches[touch].t = t
            self.touches[touch].raw = raw[touch]
            self.touches[touch].duration = t-self.touches[touch].orig_t
            self.touches[touch].feedback = self.feedback(frame_touches[touch])
            
            events.append(TouchEvent(event="DRAG", touch=self.touches[touch]))
            
        for touch in up:
            # touch up
            events.append(TouchEvent(event="UP", touch=self.touches[touch]))      
            self.touches[touch].alive= False            
            self.graveyard[touch] = self.touches[touch]
            del self.touches[touch]

        # clean up touches that have been dead for too long
        for touch in list(self.graveyard.keys()):
            touch_obj = self.graveyard[touch]
            dead_time = t - touch_obj.t
            touch_obj.dead_time = dead_time
            if dead_time>self.touch_linger_time:
                # remove the slot it was using            
                del self.active_touches[touch_obj.active_touch]
                del self.graveyard[touch]
        return {"events":events, "t":t, "fseq":fseq}


# Listen to incoming ZMQ events and parse into
# up/down/drag events 
class ZMQTouchHandler:
    def __init__(self, zmq_address, feedback_buf):
        self.active_touches = {}
        # create a zmq receiver and subscribe to touches
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.SUBSCRIBE, "TOUCH")
        socket.connect(zmq_address)
        self.socket = socket
        self.manager = TouchManager(feedback_buf = feedback_buf)
        
        
        
    def tick(self, touch_fn=None):
        # receive any waiting touch events, and dispatch 
        # to the touch handling function
        waiting = self.socket.poll(zmq.NOBLOCK)
        while waiting != 0:
            parts = self.socket.recv_multipart(zmq.NOBLOCK)       
            if len(parts)==2:
                json_data = parts[-1]
                touch_data = json.loads(json_data)                
                
                # construct events
                events = self.manager.touch_frame(touch_data["touches"], 
                                                touch_data["raw"],
                                                fseq=touch_data["fseq"],
                                                t = touch_data["t"])
                # take a copy of the touches
                self.active_touches = self.manager.active_touches
                
                # call the callback

                if touch_fn is not None and len(events["events"])>0:
                    touch_fn(events["events"])                    
                    
            waiting = self.socket.poll(zmq.NOBLOCK)


if __name__=="__main__":
    touches = [[0,0], [0.1,0], [-0.1, 0], [0,np.pi/4], [0, -np.pi/4], [-1,1], [-1.1, 1]]
    print np.nonzero(cluster_touches(np.array(touches), 0.2))
