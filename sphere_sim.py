import numpy as np
import pyglet
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *
import pygame,time,sys,random,math
import utils.glskeleton as glskeleton
import utils.glutils as glutils
import random
import utils.gloffscreen as gloffscreen
import sys
from utils.sphere_render import SphereRenderer, make_grid
import OSC
from sphere import cartesian_to_spherical, polar_to_display

class TouchSim(object):
    # Manage sending simulated OSC events as touches on the sphere
    # are registered
    def __init__(self, ip, port):
        self.client = OSC.OSCClient()
        self.client.connect((ip, port))
        self.lat = 0
        self.lon = 0
        self.id = 1
        self.active = False
        
    def touch_up(self):
        self.id += 1
        self.active = False        
        
    def touch_down(self):
        self.active = True
        
    def set_position(self, lon, lat):
        self.lon = lon
        self.lat = lat
        
    def send_msg(self, msg):
        m = OSC.OSCMessage("/tuio/2dcur")
        m.append(msg)       
        self.client.send(m)
    
    def send_touches(self):
        if self.active:            
            self.transmit()
    
    def transmit(self):
        # send the OSC message for the touch position
        # converting from radians lat, lon to the TUIO
        # 0-1 x,y format before sending
        self.send_msg(["alive"])
        tuio_x = (self.lon % (2*np.pi)) / (2*np.pi)        
        if tuio_x<0.0:
            tuio_x += 1.0
        tuio_y = (self.lat + (np.pi/2)) / np.pi       
        self.send_msg(["set", self.id, tuio_x, tuio_y])
        self.send_msg(["fseq"])
        
     
def ray_sphere(origin, dir):
    # compute the intersection of a ray from origin along the direction dir
    # and a unit sphere at the origin. Returns None if no interesection, or
    # the hit point, if there is one
    a = 1.0
    b = np.sum(dir * (2 * origin))
    c = np.sum(origin**2)  - 1;
    d = b**2 + (-4)*a*c    
    if d<0:
        return None
    d = np.sqrt(d)    
    t = -0.5 * (b+d)/a    
    if t>0:
        distance = np.sqrt(a) * t
        hit = origin + t * dir
        return hit
    else:
        return None
    
     
        
class SphereViewer(object):
    def __init__(self, sphere_resolution=1024, window_size=(800,600), background=None, exit_fn=None, color=(1.0,1.0,1.0,1.0), simulate=True, auto_spin=False, draw_fn=None, touch_port=3333, touch_ip='127.0.0.1', simulate_touches=True):
        
        self.simulate = simulate
        self.size = sphere_resolution
        self.draw_fn = draw_fn
        self.exit_fn = exit_fn
        self.auto_spin = auto_spin
        if self.simulate:
            # create a simulation object and render to the offscreen texture
            self.skeleton = glskeleton.GLSkeleton(draw_fn = self.redraw, resize_fn = self.resize, tick_fn=self.tick, mouse_fn=self.mouse, key_fn=self.key, window_size=window_size)
            self.sphere_renderer = SphereRenderer(size=sphere_resolution, background=background, color=color)
            self.sphere_renderer.begin()
        else:
            # draw directly to the screen, using a viewport centred so that the centre pixel is at the North pole of the sphere
            self.skeleton = glskeleton.GLSkeleton(draw_fn = self.redraw, resize_fn=self.resize, tick_fn=self.tick, mouse_fn=self.mouse, key_fn=self.key, window_size=window_size)            
            # compute centering and assign viewport
            cx = window_size[0] - sphere_resolution
            cy = window_size[1] - sphere_resolution            
            glViewport(cx/2,0,sphere_resolution,sphere_resolution)
            self.skeleton.auto_clear = False
        
        # initialise the mouse rotation
        self.rotation = [0,0]
        self.last_rotation = [0,0]
        self.rotate_scale = -0.2        
        self.frame_ctr = 0
        self.drag_start = None                
        self.last_touch = time.clock()
        self.spin = 0
        self.target_spin = 0
        self.relax = False
        
        # initialise OSC
        self.simulate_touches = simulate_touches
        self.touch_sim = TouchSim(touch_ip,touch_port)
        self.touch_position = (0,0)
        self.display_touch_position = None
        
    def resize(self, w, h):
        if not self.simulate:
            # no simulation, just recenter the viewport
            cx = w - self.size
            cy = h - self.size            
            glViewport(cx/2,cy/2,self.size,self.size)
        else:            
            # simulation window resized, adjust the projection matrix
            glViewport(0,0,w,h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, w, 0, h, -1, 500)
            glMatrixMode(GL_MODELVIEW)
           
            
    def start(self):
        # begin the sphere loop
        self.skeleton.main_loop()
        
  
                
    def mouse(self, event, x=None, y=None, dx=None, dy=None, buttons=0, modifiers=None, **kwargs):
    
            if buttons & pyglet.window.mouse.MIDDLE:
                print event
                if event=="press":        
                    self.relax = True
                if event=="release":        
                    self.relax = False
                
                
    
            if buttons & pyglet.window.mouse.LEFT:
                if event=="press":        
                    self.touch_sim.touch_down()
                    self.touch_position = (x,y)
                if event=="drag":
                    self.touch_position = (x,y)
                if event=="release":
                    self.touch_sim.touch_up()
                                    
            # respond to mouse events, to allow dragging of the sphere simulation
            if buttons & pyglet.window.mouse.RIGHT:
                if event=="press":        
                    self.drag_start = (x,y)
                    self.last_rotation = list(self.rotation)
                    self.last_touch = time.clock()
                if event=="drag":
                    if self.drag_start is not None:
                        new_pos = (x,y)
                        self.rotation[0] = self.last_rotation[0] + (self.drag_start[0] - new_pos[0]) * self.rotate_scale
                        self.rotation[1] = self.last_rotation[1] + (self.drag_start[1] - new_pos[1]) * self.rotate_scale * 0.5
                        self.last_touch = time.clock()
                if event=="release":
                    self.drag_start = None
                    self.last_touch = time.clock()
                    
                
            
    def key(self, event, symbol, modifiers):
        # quit on escape
        if symbol==pyglet.window.key.ESCAPE:
            if self.exit_fn:
                self.exit_fn()
            exit()
                        
                        
    def update_rotations(self):
        # update dragging motions, *if* we are in simulation mode
        if time.clock()-self.last_touch>3 and self.auto_spin:
            self.target_spin = 0.2        
        else:
            self.target_spin = 0.0
        
        self.spin = 0.9 *self.spin + 0.1*self.target_spin    
        self.rotation[0] += self.spin
        
        # reduce the tilt if the relax button (middle mouse) is held down
        if self.relax:
            self.rotation[1] = self.rotation[1] * 0.8
        
        
    def tick(self):       
        if self.simulate:
            self.sphere_renderer.begin()
            self.draw_fn()        
            glPointSize(8.0)
            glDisable(GL_TEXTURE_2D)
            glBegin(GL_POINTS)
            glColor4f(1,1,0,1)            
            if self.display_touch_position:                
                glVertex2f(*self.display_touch_position)
            glEnd()
            
            self.sphere_renderer.end()
            self.update_rotations()
            self.redraw()      
            if self.simulate_touches:
                self.touch_sim.send_touches()
        else:
            self.draw_fn()
            return        
               
    
    def update_touch_point(self):
        # must be called when the viewport, modelview and projection matrices are set
        # correctly for sim rendering
        x,y = self.touch_position
        # find the mouse ray
        r1 = np.array(gluUnProject(x,y,0.0))
        r2 = np.array(gluUnProject(x,y,1.0))
        # normalize
        ray = (r1-r2)
        ray = -ray / np.sqrt(np.sum(ray**2))
        # compute ray/sphere intersection
        hit = ray_sphere(r1, ray)
        if hit is not None and self.touch_sim.active:
            x,y,z = hit
            # convert to polar co-ordinates
            lon, lat = cartesian_to_spherical((x,y,z))
            self.display_touch_position = polar_to_display(np.pi/2-lon, -lat, self.size/2)
            self.touch_sim.set_position(np.pi/2-lon, -lat)
        
                                  
    def redraw(self):  
        # redraw the simulated sphere
        if not self.simulate:
            return 
       
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        gluPerspective(60.0, float(self.skeleton.w)/float(self.skeleton.h), 1, 2000)
        w,h = self.skeleton.w, self.skeleton.h
        #glOrtho(-1.5, 1.5, -1.5/(w/h), 1.5/(w/h), -1, 500)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # turn on some lights
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.1, 0.1, 0.1,1])
        glLightfv(GL_LIGHT0, GL_POSITION, [0,0,1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [1,1,1,1])        
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1,1,1,1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, [50.0])        
        glShadeModel(GL_SMOOTH)
        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_LIGHTING)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gluLookAt(0,0,-2.5,0,0,0,0,1,0)        
        self.frame_ctr += 1
        
        latitude = self.rotation[1]
        longitude = self.rotation[0]
                
        
        glRotatef(-90+latitude, 1, 0,0)
        glRotatef(longitude, 0, 0, 1)     
        
        self.update_touch_point()
        
        
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        
        self.sphere_renderer.render()
                                
        glPopAttrib()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        
# defaults for rendering the sphere
SPHERE_WIDTH = 2560
SPHERE_HEIGHT = 1600
SPHERE_SIZE = 1920 # estimated to compensate for the partial sphere coverage

def make_viewer(**kwargs):
    sim = False
    # check the command line arguments -- if we got a --test, then start in simulation mode
    if "--test" in sys.argv:
        sim = True

    if sim:
        s = SphereViewer(sphere_resolution=1600, window_size=(800, 800), background=None, simulate=True, **kwargs)
        print("Simulating")
    else:
        s = SphereViewer(sphere_resolution=SPHERE_SIZE, window_size=(SPHERE_WIDTH,SPHERE_HEIGHT), background=None, simulate=False, **kwargs)
        print("Non-simulated")
    return s
        
        
# test function
if __name__=="__main__":    

    s = make_viewer()
    size = s.size
    
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, size, 0, size, -1, 500)
    glMatrixMode(GL_MODELVIEW)    
    glLoadIdentity()
    glEnable(GL_POINT_SMOOTH)
    glPointSize(10.0)
    glColor4f(1,0,0,1)
    
    def draw_fn():           
        glClearColor(1,1,1,1)
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        make_grid(800)
        
    s.draw_fn = draw_fn
    s.start()
    
    
