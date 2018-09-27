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

class SearchTest(object):
    spiral_amount = 256                                                             # Number of spirals to generate
    target_distance = 99                                                            # Initial dummy value for target distance

    target_threshold = 3.0                                                          # Threshold target in degrees before target timer starts
    threshold_flag = True
                                                                                    
    end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=3600)      # Dummy initial value
    time_within_ring = 3                                                            # Number of seconds to align dot within ring

    align_n = 31                                                                    # Dot position to display task dot    
    target_pt = np.array([[np.radians(180), np.radians(0)]], dtype=np.float)       # Position of target on sphere

    reset = False
    touched_point = False
    complete = False

    # Generate a new random dot position from spiral amount
    def generate_random_dot_pt(self):
        t = self.align_n
        while t == self.align_n:
            t = randint(0, self.spiral_amount-1)
        return t


    # Check if two points are within some threshold degree of each other
    def check_pts(self, xyz, rotated_origin):    
        if (np.degrees(self.target_distance) < self.target_threshold and np.degrees(self.target_distance) > (-1) * self.target_threshold):            
            return True
        else:
            return False

    def xyz_to_lonlat(self, xyz):
        return sphere.cart_to_polar(xyz[0], xyz[1], xyz[2])


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

        self.finger_pts = np.array([[0.0, 0.0]], dtype=np.float)

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
        
        self.viewer.start()

    def touch(self, events):        
        for event in events:
            xyz = sphere.polar_to_cart(*event.touch.lonlat)
            
            if event.event=="DRAG":
                self.rotater.drag(event.touch.id, xyz)
            
            if event.event=="UP":
                self.rotater.up(event.touch.id, xyz)

                if not self.complete:
                    self.end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=360000)
                    self.point_colour = (1.0, 0.0, 0.0, 1.0)
                self.touched_point = False
            
            if event.event=="DOWN":
                self.rotater.down(event.touch.id, xyz)
                
                self.finger_pts = np.array([self.xyz_to_lonlat(xyz)], dtype=np.float)

                if (self.check_pts(xyz, self.rotated_origin)):                    
                    self.end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=2)                    
                    self.touched_point = True
                    self.point_colour = (0.0, 1.0, 0.0, 1.0) 


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

        # Compute distance between the points (must be in Cartesian space)
        quat = self.rotater.orientation        
        
        self.rotated_origin = sphere.rotate_cartesian(quat/np.linalg.norm(quat), np.array(self.origin))         # rotate the points with the quaternion                        
        
        # Compare distance, again directly in Cartesian space

        self.target_distance = sphere.spherical_distance(sphere.cart_to_polar(self.rotated_origin[0], self.rotated_origin[1], -self.rotated_origin[2]) , self.finger_pts[0])

        # self.target_distance = sphere.spherical_distance_cartesian(self.rotated_origin, self.target)       

    def tick(self):        
        self.rotater.update(1/60.0)

        if (datetime.datetime.now() >= self.end_threshold and self.touched_point):
            self.touched_point = False
            self.complete = True

            # Change background dots to indicate success
            self.background_colour = (0.0, 1.0, 0.0, 1.0)            
            self.reset = True
        
        # Set and start timer between iterations
        if self.reset:
            self.end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=5)
            self.reset = False

            # Start next iteration
        if datetime.datetime.now() >= self.end_threshold:                        
            # Reset flags and dummy value
            self.touched_point = False
            self.complete = False
            self.end_threshold = datetime.datetime.now() + datetime.timedelta(seconds=360000)
                
                # Reset colours and orientation
            self.background_colour = (1.0, 1.0, 1.0, 1.0)
            self.point_colour = (1.0, 0.0, 0.0, 1.0)
            self.rotater.orientation = np.array([0,0,0,1], dtype=np.float)
            self.rotater.angular_velocity = np.array([0,0,0,0.0], dtype=np.float) 
            
                # Get next target point
            self.align_n = self.generate_random_dot_pt()               
            self.align_pts = self.pts[self.align_n : self.align_n + 1, :]
            self.origin = sphere.spherical_to_cartesian(self.pts[self.align_n])

            align_point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])        
            self.align_point_vbo = ShaderVBO(align_point_shader, IBuf(np.arange(len(self.align_pts))), 
                                buffers={"position":VBuf(self.align_pts), },
                                vars={"constant_size":20.0,                                    
                                },                                     
                                primitives=GL_POINTS)
    pass
              
if __name__=="__main__":
    p = SearchTest()
    
    
   