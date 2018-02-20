import OSC
import timeit
wall_clock = timeit.default_timer

from pypuffersphere.sphere import sphere

# manage rotation of the simulated sphere
# and simulation of touches on this sphere via mouse presses

class RotationManager:
    def __init__(self, auto_spin=False, osc_port=3333):
        self.osc_client = OSC.OSCClient()
        self.osc_client.connect(('localhost', osc_port))

        self.auto_spin = auto_spin
        self.rotation = [-90,0]
        self.last_rotation = [0,0]
        self.rotate_scale = -0.2        
        self.frame_ctr = 0
        self.drag_start = None                
        self.last_touch = wall_clock()
        self.spin = 0
        self.touch_id = 0
        self.target_spin = 0
        self.auto_spin = False

        # manage simulated touches on the sphere
        self.touch_is_down = False
        self.touch_pos = (0,0)
        self._sphere_point = None # updated all the time in lon, lat format        
        self.sphere_point = (-1, -1)  # updated only while the (right) mouse is down

    def send_osc(self, addr, elements):
        """Send a message to the given address
        using the open OSC client connection"""
        oscmsg = OSC.OSCMessage()
        oscmsg.setAddress(addr)
        for elt in elements:
            oscmsg.append(elt)        
        self.osc_client.send(oscmsg)

    def send_touch(self, polar=None):
        """Send the simulated touches over OSC"""
        
        self.send_osc("/tuio/2Dcur", ['alive'])
        if polar:
            lon, lat = polar 
            tuio = sphere.polar_to_tuio(lon, lat)
            self.send_osc("/tuio/2Dcur", ['set', self.touch_id, tuio[0], 1.0-tuio[1]])        
        self.send_osc("/tuio/2Dcur", ['fseq', self.frame_ctr])
        self.frame_ctr += 1

    # left mouse down
    def press(self, x, y):
        self.drag_start = (x,y)
        self.last_rotation = list(self.rotation)
        self.last_touch = wall_clock()

    # left mouse drag; spin the sphere
    def drag(self, x, y):
        if self.drag_start is not None:
            new_pos = (x,y)
            self.rotation[0] = self.last_rotation[0] + (self.drag_start[0] - new_pos[0]) * self.rotate_scale
            self.rotation[1] = self.last_rotation[1] + (self.drag_start[1] - new_pos[1]) * self.rotate_scale * 0.5
            self.last_touch = wall_clock()
        else:
            # we started dragging without a press?!
            # just simulate the press
            self.press(x, y)

    # left mouse up; sphere relaxes
    def release(self,x,y):
        self.drag_start = None
        self.last_touch = wall_clock()

    # return active touch point
    def get_touch_point(self):
        if self.touch_is_down:
            return self._sphere_point 
        else:
            return None

    # get position of mouse in screen coords
    def get_mouse_pos(self):
        if self.touch_is_down:
            return self.touch_pos
        else:
            return None

    # simulated touch point down
    def touch_down(self, x, y):
        self.touch_is_down = True
        self.touch_pos = (x,y)
        
    # simulated touch point up
    def touch_release(self, x, y):
        self.touch_is_down = False
        self._sphere_point = None
        self.touch_id += 1 # make sure we have unique ids for each simulated touch

    # simulated touch point moves
    def touch_drag(self, x, y):
        self.touch_pos = (x,y)
        
        

    def tick(self):
        # autorotate the sphere if needed
        if wall_clock()-self.last_touch>3 and self.auto_spin:
                self.target_spin = 0.2        
        else:
            self.target_spin = 0.0
        
        # smooth out polar rotation
        self.spin = 0.9 *self.spin + 0.1*self.target_spin    
        self.rotation[0] += self.spin

        # relax sphere back towards equatorial alignment with horizontal
        if self.drag_start is None:
            self.rotation[1] *= 0.95

        # send tuio if the touch is down        
        if self.touch_is_down and self._sphere_point is not None:            
            self.send_touch(self._sphere_point)
        else:            
            self.send_touch(None)

    # return overall rotation of the sphere as lon,lat pair
    def get_rotation(self):
        return self.rotation

    def get_sphere_touch(self):
        if self.touch_is_down:
            return self._sphere_point
        else:
            return None

    def set_sphere_touch(self, lon, lat):
        # note: this should only be read while the mouse button is down
        # outside of a mouse down event, this will change as the sphere
        # is rotated, which won't be the desired effect!
        self._sphere_point = (lon, lat)
        