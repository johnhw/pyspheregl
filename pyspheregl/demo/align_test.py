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
    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw, 
        tick_fn=self.tick,
        touch_fn=self.touch)
        self.rotater = RotationHandler()                

        pts = np.array(sphere.spiral_layout(256))
        
        align_n = 31
        target_n = 95

               
        align_pts = pts[align_n:align_n+1,:]
        target_pts = pts[target_n:target_n+1,:]

        self.origin = sphere.spherical_to_cartesian(pts[align_n]) # the point we start at

        print pts[target_n]

        self.target = sphere.spherical_to_cartesian(pts[target_n]) # the point we want to dock with


        # point shader; simple coloured circles, with no spherical correction
        point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])
        self.point_vbo = ShaderVBO(point_shader, IBuf(np.arange(len(pts))), 
                                    buffers={"position":VBuf(pts), },
                                    vars={"constant_size":10.0,                                    
                                    },                                     
                                    primitives=GL_POINTS)

                      
                
        align_point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])        
        self.align_point_vbo = ShaderVBO(align_point_shader, IBuf(np.arange(len(align_pts))), 
                                    buffers={"position":VBuf(align_pts), },
                                    vars={"constant_size":20.0,                                    
                                    },                                     
                                    primitives=GL_POINTS)

        target_point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/ring.vert")], [getshader("user/ring.frag")])        
        
        self.target_point_vbo = ShaderVBO(target_point_shader, IBuf(np.arange(len(target_pts))), 
                                    buffers={"position":VBuf(target_pts), },
                                    vars={"constant_size":40.0,   
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
        
        # draw the background
        self.point_vbo.set_attrib("color", (1.0, 1.0, 1.0, 1.0))
        self.point_vbo.draw(vars={"quat":self.rotater.orientation})
        # self.point_vbo.draw()                                                     # Modification
        
        # draw the single moving target point, locked to the background
        self.align_point_vbo.set_attrib("color", (1.0, 0.0, 0.0, 1.0))
        self.align_point_vbo.draw(vars={"quat":self.rotater.orientation})
        # self.align_point_vbo.draw()                                               # Modification

        # draw the (fixed) target point w/o rotation
        self.target_point_vbo.set_attrib("color", (0.0, 0.0, 1.0, 1.0))        
        self.target_point_vbo.draw()
        # self.target_point_vbo.draw(vars={"quat":self.rotater.orientation})        # Modification

        # compute distance between the points (must be in Cartesian space)
        quat = self.rotater.orientation
        
        self.rotated_origin = sphere.rotate_cartesian(quat/np.linalg.norm(quat), np.array(self.origin)) # rotate the points with the quaternion        
                
        # compare distance, again directly in Cartesian space
        target_distance = sphere.spherical_distance_cartesian(self.rotated_origin, self.target)
        
        print(np.degrees(target_distance))
        

    def tick(self):        
        self.rotater.update(1/60.0)
        pass
        
                        

              
if __name__=="__main__":
    p = AlignTest()
    
    
   