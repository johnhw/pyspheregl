import numpy as np
import pyglet
from pyglet.gl  import *
import time,sys,random,math,os
import OSC

import timeit
wall_clock = timeit.default_timer

from pypuffersphere.utils import glskeleton,  gloffscreen, np_vbo, shader
from pypuffersphere.sphere import sphere
from pypuffersphere.utils.graphics_utils import make_unit_quad_tile

import os 

def resource_file(fname):
    dir_path = os.path.dirname(os.path.realpath(__file__))        
    return os.path.join(dir_path, "..", fname)



 


class RotationManager:
    def __init__(self, auto_spin=False, osc_port=3333):
        self.osc_client = OSC.OSCClient()
        self.osc_client.connect(('localhost', osc_port))

        self.auto_spin = auto_spin
        self.rotation = [0,0]
        self.last_rotation = [0,0]
        self.rotate_scale = -0.2        
        self.frame_ctr = 0
        self.drag_start = None                
        self.last_touch = wall_clock()
        self.spin = 0
        self.target_spin = 0
        self.auto_spin = False

        # manage simulated touches on the sphere
        self.touch_is_down = False
        self.touch_pos = (0,0)
        self._sphere_point = (-1, -1) # updated all the time
        self.sphere_point = (-1, -1)  # updated only while the (right) mouse is down

    def send_osc(self, addr, elements):
        """Send a message to the given address
        using the open OSC client connection"""
        oscmsg = OSC.OSCMessage()
        oscmsg.setAddress(addr)
        for elt in elements:
            oscmsg.append(elt)
        self.osc_client.send(oscmsg)

    def send_touch(self, polar):
        """Send the simulated touches over OSC"""
        lat, lon = polar 
        tuio = sphere.polar_to_tuio(lon, lat)
        self.send_osc("/tuio/2Dcur", ['alive'])
        self.send_osc("/tuio/2Dcur", ['set', 0, tuio[0], tuio[1]])
        self.send_osc("/tuio/2Dcur", ['fseq', self.frame_ctr])
        self.frame_ctr += 1

    def press(self, x, y):
        self.drag_start = (x,y)
        self.last_rotation = list(self.rotation)
        self.last_touch = wall_clock()

    def drag(self, x, y):
        if self.drag_start is not None:
            new_pos = (x,y)
            self.rotation[0] = self.last_rotation[0] + (self.drag_start[0] - new_pos[0]) * self.rotate_scale
            self.rotation[1] = self.last_rotation[1] + (self.drag_start[1] - new_pos[1]) * self.rotate_scale * 0.5
            self.last_touch = wall_clock()

    def release(self,x,y):
        self.drag_start = None
        self.last_touch = wall_clock()

    def get_mouse_pos(self):
        return self.touch_pos

    def touch_down(self, x, y):
        self.touch_is_down = True
        self.touch_pos = (x,y)
        self.sphere_point = self._sphere_point
        print(self.sphere_point)
        
    def touch_release(self, x, y):
        self.touch_is_down = False

    def touch_drag(self, x, y):
        self.touch_pos = (x,y)
        self.sphere_point = self._sphere_point
        

    def tick(self):
        if wall_clock()-self.last_touch>3 and self.auto_spin:
                self.target_spin = 0.2        
        else:
            self.target_spin = 0.0
        
        self.spin = 0.9 *self.spin + 0.1*self.target_spin    
        self.rotation[0] += self.spin

        if self.drag_start is None:
            self.rotation[1] *= 0.95

        # send tuio if the touch is down
        if self.touch_is_down:
            self.send_touch(self.sphere_point)

    def get_rotation(self):
        return self.rotation

    def set_sphere_touch(self, lat, lon):
        # note: this should only be read while the mouse button is down
        # outside of a mouse down event, this will change as the sphere
        # is rotated, which won't be the desired effect!
        self._sphere_point = (lat,lon)

def getshader(f):
    return resource_file(os.path.join("shaders", f))

# have touch input monitor program
# using asciimatics and zmq to broadcast the data

class SphereViewer:

    def make_quad(self):
        # create the vertex buffers that will be used to reproject the sphere
        self.fbo = gloffscreen.FBOContext(self.size, self.size)
        self.touch_fbo = gloffscreen.FBOContext(self.window_size[0], self.window_size[1], texture=False)
        self.sphere_map_shader = shader.shader_from_file(verts=[getshader("sphere.vert"), getshader("sphere_map.vert")], 
                                                   frags=[getshader("sphere_map.frag")])        

        self.touch_shader = shader.shader_from_file(verts=[getshader("sphere.vert"), getshader("sphere_touch.vert")], 
                                                   frags=[getshader("sphere_touch.frag")])        
        

        self.quad_shader = shader.shader_from_file(verts=[getshader("sphere.vert"), getshader("quad.vert")], 
                                                   frags=[getshader("quad.frag")])        

        n_subdiv = 128        
        quad_indices, quad_verts, _ = make_unit_quad_tile(n_subdiv)    
        qverts = np_vbo.VBuf(quad_verts)      
        
        self.sphere_render = shader.ShaderVBO(self.sphere_map_shader, quad_indices, 
                                         buffers={"position":qverts},
                                         textures={"quadTexture":self.fbo.texture},
                                         vars={"grid_bright":self.debug_grid})


        # simple quad render for testing
        world_indices, world_verts, world_texs = make_unit_quad_tile(1)            

        self.world_render = shader.ShaderVBO(self.quad_shader, world_indices, 
                                         buffers={"position":np_vbo.VBuf(world_verts),
                                         "tex_coord":np_vbo.VBuf(world_texs)},
                                         textures={"quadTexture":self.world_texture.texture})

        # for getting touches back
        self.sphere_touch = shader.ShaderVBO(self.touch_shader, quad_indices, 
                                            buffers={"position":qverts})

        
    def test_render(self):
        self.world_render.draw(n_prims=0)
      

    def __init__(self, sphere_resolution=1024, window_size=(800,600), background=None, exit_fn=None, simulate=True, auto_spin=False, draw_fn=None, tick_fn=None, 
        debug_grid=0.1, test_render=False):
        self.simulate = simulate
        self.debug_grid = debug_grid # overlaid grid on sphere simulation
        self.size = sphere_resolution
        if not test_render:            
            self.draw_fn = draw_fn
        else:
            self.draw_fn = self.test_render # simple test function to check rendering
        self.exit_fn = exit_fn
        self.tick_fn = tick_fn        
        self.window_size = window_size

        
        self.world_texture = pyglet.image.load(resource_file("data/azworld.png"))
        self.rotation_manager = RotationManager(auto_spin=auto_spin)
        self.skeleton = glskeleton.GLSkeleton(draw_fn = self.redraw, resize_fn = self.resize, 
        tick_fn=self.tick, mouse_fn=self.mouse, key_fn=self.key, window_size=window_size)

        

        if not self.simulate:
            cx = window_size[0] - sphere_resolution
            cy = window_size[1] - sphere_resolution            
            glViewport(cx/2,0,sphere_resolution,sphere_resolution)
            
        self.make_quad()
      
    def resize(self, w, h):
        if not self.simulate:
            cx = w - self.size
            cy = h - self.size            
            glViewport(cx/2,cy/2,self.size,self.size)
        else:            
            glViewport(0,0,w,h)
                        
    def start(self):
        self.skeleton.main_loop()
        
    def mouse(self, event, x=None, y=None, dx=None, dy=None, buttons=None, modifiers=None, **kwargs):
        
        if buttons is not None:
            # drag sphere with left mouse
            if buttons & pyglet.window.mouse.LEFT:
                if event=="press":    
                    self.rotation_manager.press(x,y)                
                if event=="drag":
                    self.rotation_manager.drag(x,y)    
                if event=="release":
                    self.rotation_manager.release(x,y)    
            
            # simulated touches with right mouse
            if buttons & pyglet.window.mouse.RIGHT:
                if event=="press":    
                    self.rotation_manager.touch_down(x,y)
                if event=="drag":
                    self.rotation_manager.touch_drag(x,y)
                if event=="release":
                    self.rotation_manager.touch_release(x,y)
                
                
    def key(self, event, symbol, modifiers):
        if symbol==pyglet.window.key.ESCAPE:            
            if self.exit_fn:
                self.exit_fn()
            pyglet.app.exit()
            sys.exit(0)
                        
    
    def tick(self):        
        if self.tick_fn:
            self.tick_fn()
                
        self.rotation_manager.tick()
            
    
                        
    def redraw(self):  
        glEnable(GL_BLEND)        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # clear the screen
        glClearColor(0.1, 0.1, 0.1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

                 
        
        if not self.simulate:
            self.draw_fn()
        else:
            # draw onto the FBO texture
            with self.fbo as f:
                self.draw_fn()
                

            # render onto the screen using the sphere distortion shader    
            rotate, tilt = self.rotation_manager.get_rotation()
            self.sphere_render.draw(n_prims=0, vars={"rotate":np.radians(rotate), "tilt":np.radians(tilt)})
            
            
            # render the image for the touch point look up
            with self.touch_fbo as f:
            
                self.sphere_touch.draw(n_prims=0, vars={"rotate":np.radians(rotate), "tilt":np.radians(tilt)})
                
                pixel_data = (GLubyte * 4)()
                # get window coordinates
                mx, my = self.rotation_manager.get_mouse_pos()                
                
                # read the pixels, convert back to radians (from unsigned bytes)
                glReadPixels(mx, my, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel_data)                                
                
                sphere_lat, sphere_lon = ((pixel_data[0] / 255.0) -0.5) * np.pi, ((pixel_data[1]/255.0)-0.5)*2*np.pi                
                # tell the touch manager where the touch is
                self.rotation_manager.set_sphere_touch(sphere_lat, sphere_lon)

        
    
SPHERE_WIDTH = 2560
SPHERE_HEIGHT = 1600
SPHERE_SIZE = 1920 # estimated to compensate for the partial sphere coverage

def make_viewer(**kwargs):
    sim = False
    if "--test" in sys.argv:
        sim = True
    
    if sim:
        s = SphereViewer(sphere_resolution=1600, window_size=(800, 800), background=None, simulate=True, **kwargs)
        print("Simulating")
    else:        
        s = SphereViewer(sphere_resolution=SPHERE_SIZE, window_size=(SPHERE_WIDTH,SPHERE_HEIGHT), background=None, simulate=False, **kwargs)
        print("Non-simulated")
    return s

