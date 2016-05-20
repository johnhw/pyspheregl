from multiprocessing import Queue
from OSC import *
import time
import threading
import traceback

#  Private class for this library
class touch_sphere():

    initiated = False

    def __init__(self, port, ip, logging, fseq, frame_rate):
        self.ip = ip
        self.port = port
        self.logging = logging
        self.last_touch = 0
        self.drawing_q = Queue(maxsize=3)
        self.touchpoints = {}
        self.fseq = fseq  
        self.osc_server = 0 
        self.last_update = 0
        self.frame_rate = frame_rate
        
    def init_touch(self):
        #  Setup OSC Connections
        self.osc_server = OSCServer((self.ip,self.port))


    def add_handler(self, address, function):
        # bind addresses to functions 
        if self.osc_server is not 0: self.osc_server.addMsgHandler(address, function)

    def start_touch(self):
        st = threading.Thread(target=self.osc_server.serve_forever)
        st.start()

    def stop_touch(self):
         if self.osc_server is not 0: self.osc_server.close() 


#  Function for Handling TUIO OSC Messages
def osc_tuio(addr, tags, data, source):
    if touch_sphere is not None:
        
        global touch_sphere
        
        #  This message denotes the beginning of a touch frame - alive refers to unique touch points
        if data[0] == "alive":
            pass
        
        #  This message gives a variety of data about a particular touch point
        elif data[0] == "set":
            #print "ID: " , data[1] , " X: " , data[2] , " Y: " , data[3]
            touch_sphere.touchpoints[data[1]] = (data[2], 1.0-data[3])
            
        #  Denotes the end of a touch frame, should initiate a drawing    
        elif data[0] == "fseq":
            try:
                this_frame = time.time()
                if len(touch_sphere.touchpoints)>0:
                    touch_sphere.last_touch = this_frame*1000.0

                #  Add frame sequence number to touchpoints list with invalid touch_id -1 so it can be
                #  identified as the frame number
              
                touch_sphere.touchpoints[-1] = data[1]

                if this_frame - touch_sphere.last_update > touch_sphere.frame_rate:
                    # print "Adding to touch queue" , this_frame, touch_sphere.last_update, this_frame-touch_sphere.last_update, touch_sphere.frame_rate
                    touch_sphere.drawing_q.put(touch_sphere.touchpoints)
                    touch_sphere.last_update = this_frame

                touch_sphere.touchpoints = {}
            except Exception as e:
                # if logging:

                #     #  TODO add error logging code

                    pass


#  Public API for touch Sphere

#  Initiate the touch sphere class which manages reading in touch points.
#  port for listening for OSC messages
#  ip address for listening for OSC messages
#  logging (boolean) turns on error and touch point logging to a text file (not currently implemented)
#  fseq (boolean) turns on including the frame sequence number in the touchpoint list
def init(ip, port=3333, logging=False, fseq=False, frame_rate=0):
    try:
        global touch_sphere
        touch_sphere=touch_sphere(port, ip, logging, fseq, frame_rate)
        touch_sphere.init_touch()
        touch_sphere.initiated = True
        global last_touches
        last_touches = {}

    except:
        print traceback.print_exc()



# By default, adds the Sphere TUIO handler
def add_handler(address='/tuio/2Dcur', function=osc_tuio):
    global touch_sphere

    if touch_sphere.initiated:
        touch_sphere.add_handler(address, function)

def start():
    global touch_sphere

    if touch_sphere.initiated:
        touch_sphere.start_touch()

def stop():
    global touch_sphere

    if touch_sphere is not None:
        touch_sphere.stop_touch()

def get_touches():
    global touch_sphere, last_touches

    if touch_sphere.initiated:
        try:
            touches = {}

            # TODO FIX THIS WITH SPHERE
            # while not touch_sphere.drawing_q.empty():
            
            touches = touch_sphere.drawing_q.get_nowait()
                # print "Popping Old Touches, fseq=",  touches[-1]

            # print "Returning a touch dict, fseq=", touches[-1] 
            
            last_touches = touches           
            return touches

        except:
            return last_touches
    else:
        return {}

def is_up():
    return touch_sphere.initiated






