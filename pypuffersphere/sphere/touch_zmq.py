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
import os


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
            lon, lat  = pos
            cz, cx, cy = sphere.spherical_to_cartesian((lon, -lat))
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

        # calibration line
        if self.calibration is not None:
            screen.print_at(self.calibration_name, 0, 1, colour=screen.COLOUR_MAGENTA, bg=screen.COLOUR_BLACK)
        else:
            screen.print_at("UNCALIBRATED", 0, 1, colour=screen.COLOUR_RED, bg=screen.COLOUR_BLACK)

        # exceptions while receiving packets
        screen.print_at(">"+self.last_exception, 0, 21, colour=screen.COLOUR_WHITE, bg=screen.COLOUR_RED)

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
            for i,(touch_id, (lon,lat)) in enumerate(touch_list.items()):                                    
                    
                    screen.print_at("(%05d) \t lon:%3.0f lat:%3.0f" % (i, np.degrees(lon), np.degrees(lat)), fseq_x, i+3, colour=screen.COLOUR_YELLOW)
                
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

    def convert_touch(self, x, y):
        # convert the touch, using calibration is possible
        if self.calibration is None:
            # no calibration, just use tuio_to_polar
            return sphere.tuio_to_polar(x,y)
        else:
            # must convert calibrated touch to plain float tuple
            lon, lat = self.calibration.get_calibrated_touch(x,y)
            return (float(lon), float(lat))

    # the actual message handler
    # reads OSC messages, broadcasts ZMQ back
    def handler(self, addr, tags, data, client_addr):
        self.last_packet = wall_clock()                
        # store a trace of recent packets
        
        if len(self.packet_trace)>10:
                self.packet_trace.pop(0)

        # we have data, decode it
        if len(data)>0:
            self.packet_trace.append(("%4.1f: "%(self.last_packet) + data[0]))
            # decode the OSC packet
            if data[0]=='fseq':
                # frame complete
                self.last_fseq = data[1]
                self.last_touch_list = self.touch_list
                self.touch_list = {}                
                # broadcast the raw touches themselves
                self.zmq_socket.send_multipart(["TOUCH", json.dumps({"touches":self.last_touch_list, 
                                                            "raw":self.raw_list,
                                                            "fseq":self.last_fseq, 
                                                            "stale":0,
                                                            "t":self.last_packet})])
                self.raw_list = {}
                
            
            # a single touch, accumulate into touch buffer
            if data[0]=='set':
                touch_id, x, y = data[1:4]
                lon, lat = self.convert_touch(x,y)
                self.touch_list[touch_id] = lon, lat
                self.raw_list[touch_id] = x,y
                
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
                self.zmq_socket.send_multipart(["TOUCH", (json.dumps({"touches":{}, "raw":{}, "fseq":-2, "stale":1, "t":wall_clock()}))])

                

    def _handler(self, *args, **kwargs):
        try:
            self.handler(*args, **kwargs)
        except Exception as err:
            # make sure we log exceptions to disk
            logger.exception(err)
            self.last_exception = str(err)

    
    def monitor(self, port=3333, zmq_port=4000, ip="127.0.0.1", msg="/tuio/2Dcur", timeout=0.2, full_trace=False, console=True, no_calibration=False):
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

        # try to import calibration
        # if not explicitly disabled with --no_calibration
        self.calibration = None
        if not no_calibration:
            try:
                import calibration
                self.calibration = calibration
            except ImportError:
                self.calibration = None
            
        if self.calibration is not None:
            self.calibration_name = calibration.calibration_file
        else:
            self.calibration_name = "UNCALIBRATED"

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
        self.raw_list = {}
       
        
        self.packet_trace = [] # short history of packet message strings

        # launch the monitor
        if self.monitor_enabled:
            Screen.wrapper(self.monitor_loop)
        else:
            self.monitor_loop(False)
                


if __name__ == "__main__":
   fire.Fire(OSCMonitor)

