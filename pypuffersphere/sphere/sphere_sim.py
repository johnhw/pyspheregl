import numpy as np
import pyglet
from pyglet.gl  import *
import time,sys,random,math,os

import timeit
wall_clock = timeit.default_timer

from pypuffersphere.utils import glskeleton,  gloffscreen, np_vbo, shader


from pypuffersphere.utils.graphics_utils import make_unit_quad_tile

import os 

def resource_file(fname):
    dir_path = os.path.dirname(os.path.realpath(__file__))        
    return os.path.join(dir_path, "..", fname)


class RotationManager:
    def __init__(self):
        self.rotation = [0,0]
        self.last_rotation = [0,0]
        self.rotate_scale = -0.2        
        self.frame_ctr = 0
        self.drag_start = None                
        self.last_touch = wall_clock()
        self.spin = 0
        self.target_spin = 0

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

    def tick(self):
        if wall_clock()-self.last_touch>3 and self.auto_spin:
                self.target_spin = 0.2        
        else:
            self.target_spin = 0.0
        
        self.spin = 0.9 *self.spin + 0.1*self.target_spin    
        self.rotation[0] += self.spin

        if wall_clock()-self.last_touch>0.1:
            self.rotation[1] *= 0.95

    def get_rotation(self):
        return self.rotation

class SphereViewer:

    def make_quad(self):
        # create the vertex buffers that will be used to reproject the sphere
        self.fbo = gloffscreen.FBOContext(self.size, self.size)
        self.quad_shader = shader.shader_from_file(verts=[resource_file("shaders/sphere_map.vert")], frags=[resource_file("shaders/sphere_map.frag")])        
        n_subdiv = 128        
        quad_indices, quad_verts, quad_texs = make_unit_quad_tile(n_subdiv)    
        qverts = np_vbo.VBuf(quad_verts, id=0)        
        #self.qverts = qverts
        #self.qibo = np_vbo.create_elt_buffer(quad_indices)
        #self.vao = np_vbo.create_vao([self.qverts])

        self.quad = shader.ShaderVBO(self.quad_shader, quad_indices, 
                                         buffers={"position":qverts},
                                         textures={"quadTexture":self.fbo.texture})

        


    def __init__(self, sphere_resolution=1024, window_size=(800,600), background=None, exit_fn=None, color=(1.0,1.0,1.0,1.0), simulate=True, auto_spin=False, draw_fn=None, tick_fn=None):
        self.simulate = simulate
        
        self.size = sphere_resolution
        self.draw_fn = draw_fn
        self.exit_fn = exit_fn
        self.tick_fn = tick_fn
        self.auto_spin = auto_spin
        self.window_size = window_size

        
        self.world_texture = pyglet.image.load(resource_file("data/azworld.png"))
        self.rotation_manager = RotationManager()
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
        if event=="press":    
            self.rotation_manager.press(x,y)                
        if event=="drag":
           self.rotation_manager.drag(x,y)    
        if event=="release":
           self.rotation_manager.release(x,y)    
            
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
            self.quad.draw(n_prims=0, vars={"rotate":np.radians(rotate), "tilt":np.radians(tilt)})
            
       
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
