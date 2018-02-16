import zmq
import json
import OSC
from asciimatics.screen import Screen
import fire
import timeit
import sphere
import numpy as np
wall_clock = timeit.default_timer

# logger for debug messages, when handling socket comms
import logging
logging.basicConfig(filename='touch_zmq.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

# convert raw frame positions into a stream of events
# either up, drag or down
class TouchManager:
    def __init__(self):
        self.touches = {}
        self.frame_touches = {}
        # stable, but low numbered slots
        self.slots = {}        
        

    def touch(self, id, x, y):
        lon, lat = sphere.tuio_to_polar(x,y)
        self.frame_touches[id] = (lon, lat)

    def touch_frame(self, fseq, t):
        # a new complete frame is issued
        existing, this_frame = set(self.touches.keys()), set(self.frame_touches.keys())        
        down, move, up = this_frame-existing, this_frame&existing, existing-this_frame

        events = {}
        for touch in down:
            # new touch down

            # find a slot
            slot = 0
            while slot in self.slots:
                slot += 1
            self.slots[slot] = True

            # create the event
            events[touch] = {"event":"DOWN",                                 
                            "lonlat":self.frame_touches[touch],
                            "slot":slot,
                            "duration":0.0}
            
            self.touches[touch] = {"lonlat":self.frame_touches[touch], "t":t, "fseq":fseq, "slot":slot}
            
            
        for touch in move:
            # touch move
            events[touch] = {"event":"DRAG",                                 
                             "lonlat":self.frame_touches[touch],
                             "slot":self.touches[touch]["slot"],
                             "origin":self.touches[touch]["lonlat"],
                             "duration":t-self.touches[touch]["t"]
                             }

        for touch in up:
            # touch up
            events[touch] = {"event":"UP", 
                            "slot":self.touches[touch]["slot"],
                            "lonlat":self.touches[touch]["lonlat"],
                            "duration":t-self.touches[touch]["t"]}       
            
            # remove the slot it was using            
            del self.slots[self.touches[touch]["slot"]]
            del self.touches[touch]

        self.frame_touches = {}
        
        return {"events":events, "t":t, "fseq":fseq}

    def all_up(self):
        self.frame_touches = {}        





# Nice sphere :)
ascii_sphere = """    
    
    ____
  .X+.   .
.Xx+-.     .
XXx++-..
XXxx++--..  
`XXXxx+++--'
  `XXXxxx'
     ""       """

class OSCMonitor:
    
    def render_sphere(self, screen, touch_list):
        touches = sorted(touch_list.keys())
        sphere_1x = 44
        sphere_2x = 66
        sphere_y = 8
        sphere_rad = 6
        # print the sphere
        for i,line in enumerate(ascii_sphere.splitlines()):
            screen.print_at(line, sphere_1x, sphere_y+i, colour=screen.COLOUR_BLUE)
            
            screen.print_at(line, sphere_2x, sphere_y+i, colour=screen.COLOUR_MAGENTA)
        screen.print_at("BACK", sphere_1x+4, sphere_y+1, colour=screen.COLOUR_BLUE)
        screen.print_at("FRONT", sphere_2x+3, sphere_y+1, colour=screen.COLOUR_MAGENTA)
        
        # print the touch positions
        for touch in touches:
            pos = touch_list.get(touch)
            x, y = pos
            lon, lat = sphere.tuio_to_polar(x,y)
            cz, cx, cy = sphere.spherical_to_cartesian((lon, lat))
            # compute ASCII coordinates
            sphere_cy = sphere_y+sphere_rad
            if cz<0:
                sphere_cx = sphere_1x+sphere_rad                 
            else:
                sphere_cx = sphere_2x+sphere_rad
            px = sphere_cx - cx * sphere_rad
            py = sphere_cy + cy * sphere_rad * 0.6
            
            screen.print_at("X", int(px), int(py),  colour=screen.COLOUR_WHITE, bg=screen.COLOUR_CYAN)



    def update_display(self, screen):
        t = wall_clock()
        delta_t = t - self.last_packet

        # limit update rate
        if t-self.last_frame<0.2:
            return
        
        self.last_frame = t 

        # status line
        screen.print_at("MSG: %15s" % self.msg, 0, 0, colour=screen.COLOUR_CYAN)
        screen.print_at("OSC: %10s:%5d" % (self.osc_ip, self.osc_port), 25, 0, colour=screen.COLOUR_YELLOW)        
        screen.print_at("ZMQ: %5d" % self.zmq_port, 66, 0, colour=screen.COLOUR_MAGENTA)

        # exceptions while receiving packets
        screen.print_at(self.last_exception, 0, 1, colour=screen.COLOUR_WHITE, bg=screen.COLOUR_RED)

        # fseq and ntouches
        fseq_x = 44
        screen.print_at("FSEQ:%8d" % self.last_fseq, fseq_x, 2, colour=screen.COLOUR_CYAN)
        screen.print_at("NTOUCH:%2d" % len(self.last_touch_list), 66, 2, colour=screen.COLOUR_BLUE)        

        if self.full_trace:
            # dump the last packets to come through        
            for i,packet in enumerate(self.packet_trace):      
                if "fseq" in packet:
                    fg = screen.COLOUR_CYAN
                if "alive" in packet:
                    fg = screen.COLOUR_WHITE
                if "set" in packet:
                    fg = screen.COLOUR_YELLOW
                screen.print_at(packet+" "*35, 0, 6+i, colour=fg, bg=screen.COLOUR_BLACK)
                
            touch_list = dict(self.last_touch_list)

            # clear the touches
            for i in range(20):
                screen.print_at(" "*50, fseq_x, i+3)

            # copy the touch list and print it out        
            for i,(touch_id, (x,y)) in enumerate(touch_list.items()):                                    
                    lon, lat = sphere.tuio_to_polar(x,y)
                    screen.print_at("(%05d) %+1.4f %+1.4f \t lon:%3.0f lat:%3.0f" % (i, x, y, np.degrees(lon), np.degrees(lat)), fseq_x, i+3, colour=screen.COLOUR_YELLOW)
                
            # render the sphere view
            self.render_sphere(screen, touch_list)

        # print out the heartbeat status
        bg = screen.COLOUR_BLACK
        fg = screen.COLOUR_WHITE
        # danger...
        if delta_t>1.0:
            fg = screen.COLOUR_RED
        # it's gone; go full red
        if delta_t>5:
            fg = screen.COLOUR_BLACK
            bg = screen.COLOUR_RED
            
        screen.print_at("HEART:%5.1f" % delta_t, 0,2, colour=fg, bg=bg)
        screen.refresh()
    
    # the actual message handler
    # reads OSC messages, broadcasts ZMQ back
    def handler(self, addr, tags, data, client_addr):
        self.last_packet = wall_clock()        
        
        # store a trace of recent packets
        self.packet_trace.append(("%4.1f: "%self.last_packet) + "\t".join([str(d) for d in data]))
        if len(self.packet_trace)>10:
                self.packet_trace.pop(0)

        # we have data, decode it
        if len(data)>0:
            
            # decode the OSC packet
            if data[0]=='fseq':
                # frame complete
                self.last_fseq = data[1]
                self.last_touch_list = self.touch_list
                self.touch_list = {}                
                # broadcast the raw touches themselves
                self.zmq_socket.send_multipart(["TOUCH", json.dumps({"touches":self.last_touch_list, 
                                                            "fseq":self.last_fseq, 
                                                            "stale":0,
                                                            "t":self.last_packet})])
                
                events = self.touch_manager.touch_frame(self.last_fseq, self.last_packet)
                
                if len(events["events"])>0:                    
                    # broadcast the events (UP/DOWN/DRAG)
                    print(events)
                    self.zmq_socket.send_multipart(["TOUCH_EVENT", json.dumps(events)])
                                    
            
            # a single touch, accumulate into touch buffer
            if data[0]=='set':
                touch_id, x, y = data[1:]
                self.touch_list[touch_id] = x, y
                self.touch_manager.touch(touch_id, x, y)
                
            # system is alive
            if data[0]=='alive':
                pass
        
        # advertise that we are still alive
        self.zmq_socket.send("ALIVE %f"%self.last_packet)

    def monitor_loop(self, screen):
        """Enter an infinite loop, handling OSC requests and broadcasting
        them over ZMQ"""
        if screen:
            screen.clear()
        while True:
            # blocking wait, for up to timeout seconds
            self.osc_server.handle_request()
            if screen:
                self.update_display(screen)

            # clear touch list if it gets stale
            if wall_clock()-self.last_packet>self.timeout*2:                
                self.last_touch_list = {}            
                self.last_fseq = -1
                
                # broadcast a stale touch so subscribers know
                # that touches aren't good any more
                self.zmq_socket.send_multipart(["TOUCH", (json.dumps({"touches":{}, 
                                                            "fseq":-2, 
                                                            "stale":1,
                                                            "t":wall_clock()}))])

                # make sure any touches are up
                self.touch_manager.all_up()
                self.zmq_socket.send_multipart(["TOUCH_EVENT", (json.dumps(self.touch_manager.touch_frame(fseq=-2, t=wall_clock())))])


    def _handler(self, *args, **kwargs):
        try:
            self.handler(*args, **kwargs)
        except Exception as err:
            # make sure we log exceptions to disk
            logger.exception(err)
            self.last_exception = str(err)

    
    def monitor(self, port=3333, zmq_port=4000, ip="127.0.0.1", msg="/tuio/2Dcur", timeout=0.2, full_trace=False, console=True):
        """Listen to OSC messages on 3333. 
        Broadcast on the ZMQ PUB stream on the given TCP port."""        
        
        self.monitor_enabled = console
        self.msg = msg
        self.osc_port = port
        self.osc_ip = ip
        self.zmq_port = zmq_port
        self.timeout = timeout        
        self.full_trace = full_trace
        self.last_exception = ""

        # reset the timeouts
        self.last_packet = wall_clock() # last time a packet came in
        self.last_frame = wall_clock() # last time screen was redrawn
        

        # create a ZMQ port to broadcast on
        context = zmq.Context()
        self.zmq_socket = context.socket(zmq.PUB)
        self.zmq_socket.bind("tcp://*:%s" % zmq_port)

        # listen for OSC events
        self.osc_server = OSC.OSCServer((ip, port))  
        self.osc_server.addMsgHandler(msg, self._handler)   
        self.osc_server.timeout = timeout

        # clear the touch status
        self.last_fseq = -1
        self.touch_list = {}
        self.last_touch_list = {}

        # touches currently down, including their down location and current location
        self.touch_manager = TouchManager()
        
        self.packet_trace = [] # short history of packet message strings

        # launch the monitor
        if self.monitor_enabled:
            Screen.wrapper(self.monitor_loop)
        else:
            self.monitor_loop(False)
                


if __name__ == "__main__":
   fire.Fire(OSCMonitor)

