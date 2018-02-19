import zmq
import numpy as np
import json

import attr

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


# convert raw frame positions into a stream of events
# either up, drag or down. Remembers origin of drags, and
# tracks duration. Also provides a stable numbering of active touches

class TouchManager:
    def __init__(self, min_latitude=-np.pi, linger_time=5.0):
        self.touches = {}        
        # stable, but low numbered slots
        self.active_touches = {}     
        self.graveyard = {}
        self.min_latitude = min_latitude
        self.touch_linger_time = linger_time
        
    def touch_frame(self, frame_touches, raw, fseq, t):

        # filter out touches which are too low on the sphere
        frame_touches = {id:pos for id,pos in frame_touches.items() if pos[1]>self.min_latitude}

        # a new complete frame is issued
        existing, this_frame = set(self.touches.keys()), set(frame_touches.keys())        
        down, move, up = this_frame-existing, this_frame&existing, existing-this_frame

        events = []
        for touch in down:
            # new touch down

            # find a slot
            active_touch = 0
            while active_touch in self.active_touches:
                active_touch += 1
            
            self.touches[touch] = Touch(origin=frame_touches[touch], lonlat=frame_touches[touch], orig_t=t,
                                        t=t, fseq=fseq, duration=0.0, dead_time=0.0, active_touch=active_touch, id=touch, alive=True,
                                        raw=raw[touch])            
            self.active_touches[active_touch] = self.touches[touch]
            
            # create the event
            events.append(TouchEvent(event="DOWN", touch=self.touches[touch]))
                        
        for touch in move:
            # touch move
            self.touches[touch].lonlat = frame_touches[touch]
            self.touches[touch].t = t
            self.touches[touch].raw = raw[touch]
            self.touches[touch].duration = t-self.touches[touch].orig_t
            
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
    def __init__(self, zmq_address):
        # create a zmq receiver and subscribe to touches
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.SUBSCRIBE, "TOUCH")
        socket.connect(zmq_address)
        self.socket = socket
        self.manager = TouchManager()
        self.active_touches = {}
        
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
