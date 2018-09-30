import math
import random
from random import randint
import datetime
import numpy as np
import pyglet
from pyglet.gl import *

# sphere stuff
from ..sim.sphere_sim import getshader, resource_file
from  ..sim import sphere_sim
from ..sphere import sphere
from ..utils.shader import ShaderVBO, shader_from_file
from ..utils.np_vbo import VBuf, IBuf
from ..utils import transformations as tn

from ..touch.rotater import RotationHandler

class AlignTest(object):
    spiral_amount = 256                                                             # Number of spirals to generate
    target_distance = 99                                                            # Initial dummy value for target distance

    target_threshold = 3.0                                                          # Threshold target in degrees before target timer starts
    threshold_flag = True
                                                                                    
    end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=3600)      # Dummy initial value
    time_within_ring = 3                                                            # Number of seconds to align dot within ring

    align_n = 31                                                                    # Dot position to display task dot    
    target_pt = np.array([[np.radians(180), np.radians(0)]], dtype=np.float32)       # Position of target on sphere
    
    reset = False
    flag = False


    # Generate a new random dot position from spiral amount
    def generate_random_dot_pt(self):
        t = self.align_n
        while t == self.align_n:
            t = randint(0, self.spiral_amount-1)
        return t


    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw, 
        tick_fn=self.tick,
        touch_fn=self.touch)
        self.rotater = RotationHandler()                

        self.point_colour = (1.0, 0.0, 0.0, 1.0)
        self.background_colour = (1.0, 1.0, 1.0, 1.0)

        # Generate random point
        self.pts = np.array(sphere.spiral_layout(256))    
        self.align_n = self.generate_random_dot_pt()               
        self.align_pts = self.pts[self.align_n : self.align_n + 1, :]

        self.origin = sphere.spherical_to_cartesian(self.pts[self.align_n])             # The point that we start at        
        self.target = sphere.spherical_to_cartesian(self.target_pt[0])                  # The point we want to align with

        # Point shader; simple coloured circles, with no spherical correction
        point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])
        self.point_vbo = ShaderVBO(point_shader, IBuf(np.arange(len(self.pts))), 
                                    buffers={"position":VBuf(self.pts), },
                                    vars={"constant_size":10.0,                                    
                                    },                                     
                                    primitives=GL_POINTS)


        # Point (dot) shader and VBO                                       
        align_point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])        
        self.align_point_vbo = ShaderVBO(align_point_shader, IBuf(np.arange(len(self.align_pts))), 
                                    buffers={"position":VBuf(self.align_pts), },
                                    vars={"constant_size":20.0,                                    
                                    },                                     
                                    primitives=GL_POINTS)


        # Target (ring) shader and VBO
        target_point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/ring.vert")], [getshader("user/ring.frag")])        
        self.target_point_vbo = ShaderVBO(target_point_shader, IBuf(np.arange(len(self.target_pt))), 
                                    buffers={"position":VBuf(self.target_pt), },
                                    vars={"constant_size":30.0,   
                                    "inner_size":20.0,                                 
                                    },                                     
                                    primitives=GL_POINTS)
        
        self.viewer.start()

    def touch(self, events):        
        for event in events:
            xyz = sphere.polar_to_cart(*event.touch.lonlat)
            if event.event=="DRAG":
                self.rotater.drag(event.touch.id, xyz)
            if event.event=="UP":
                self.rotater.up(event.touch.id, xyz)
            if event.event=="DOWN":
                self.rotater.down(event.touch.id, xyz)


    def draw(self):
        glClearColor(0.0,0.0,0.0,1)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)
        glEnable(GL_POINT_SPRITE)
        
        # Draw the background
        self.point_vbo.set_attrib("color", self.background_colour)
        self.point_vbo.draw(vars={"quat":self.rotater.orientation})
        # self.point_vbo.draw()                                                                                 # Modification
        
        # Draw the single moving target point
        self.align_point_vbo.set_attrib("color", self.point_colour)
        self.align_point_vbo.draw(vars={"quat":self.rotater.orientation})
        # self.align_point_vbo.draw()                                                                           # Modification

        # Draw the (fixed) target point w/o rotation
        self.target_point_vbo.set_attrib("color", (0.0, 0.0, 1.0, 1.0))        
        self.target_point_vbo.draw()

        # Compute distance between the points (must be in Cartesian space)
        quat = self.rotater.orientation        
        
        self.rotated_origin = sphere.rotate_cartesian(quat/np.linalg.norm(quat), np.array(self.origin))         # rotate the points with the quaternion                        
        
        # Compare distance, again directly in Cartesian space
        self.target_distance = sphere.spherical_distance_cartesian(self.rotated_origin, self.target)       

    def tick(self):        
        self.rotater.update(1/60.0)

        # If within target ring                
        if (np.degrees(self.target_distance) < self.target_threshold and np.degrees(self.target_distance) > (-1) * self.target_threshold and not self.flag):        

            # Start the timer for how long to remain within target ring                    
            if (self.threshold_flag):
                self.threshold_flag = False            
                self.end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=self.time_within_ring)
                self.point_colour = (0.0, 1.0, 0.0, 1.0)

            # Within target for valid time  
            if datetime.datetime.now() >= self.end_threshold: 
                self.background_colour = (0.0, 1.0, 0.0, 1.0)
                self.reset = True
                self.flag = True                                                 
        else:
            # Outside of threshold so reset flag
            self.threshold_flag = True                        
            if (np.degrees(self.target_distance) < self.target_threshold and np.degrees(self.target_distance) > (-1) * self.target_threshold):
                self.point_colour = (0.0, 1.0, 0.0, 1.0)    
            else:
                self.point_colour = (1.0, 0.0, 0.0, 1.0)    


        # Iteration completed so set time beteen iterations time (i.e. wait 5 seconds until reset and start next iteration)       
        if self.reset:
            self.end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=5)
            self.reset = False


        # Reset and start next iteration
        if datetime.datetime.now() >= self.end_threshold and self.flag:
            # Reset misc. dummy values and flags
            self.target_distance = 999   
            self.end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=360000)                       
            self.flag = False 

            # Reset orientation and colours
            self.rotater.orientation = np.array([0,0,0,1], dtype=np.float)
            self.rotater.angular_velocity = np.array([0,0,0,0.0], dtype=np.float)            
            self.background_colour = (1.0, 1.0, 1.0, 1.0)
            self.point_colour = (1.0, 0.0, 0.0, 1.0)

            # Get next target point
            self.align_n = self.generate_random_dot_pt()               
            self.align_pts = self.pts[self.align_n : self.align_n + 1, :]
            self.origin = sphere.spherical_to_cartesian(self.pts[self.align_n])

            # Draw next target point                    
            align_point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])        
            self.align_point_vbo = ShaderVBO(align_point_shader, IBuf(np.arange(len(self.align_pts))), 
                                buffers={"position":VBuf(self.align_pts), },
                                vars={"constant_size":20.0,                                    
                                },                                     
                                primitives=GL_POINTS)
        pass                
              
if __name__=="__main__":
    p = AlignTest()
    
    
   