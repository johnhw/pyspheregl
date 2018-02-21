import numpy as np
import pyglet
from pyglet.gl import *

# sphere stuff
from pypuffersphere.sim.sphere_sim import getshader, resource_file
import pypuffersphere.sim.sphere_sim as sphere_sim
import pypuffersphere.sphere.sphere as sphere
from pypuffersphere.utils.shader import ShaderVBO, shader_from_file

import time
from pypuffersphere.utils.np_vbo import VBuf, IBuf
from pypuffersphere.utils.graphics_utils import make_unit_quad_tile
import pypuffersphere.utils.transformations as tn
from pypuffersphere.utils.graphics_utils import wall_clock

from pypuffersphere.touch.rotater import RotationHandler



class RotationTest(object):
    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw, 
        tick_fn=self.tick,
        touch_fn=self.touch)
        self.rotater = RotationHandler()                

        pts = np.array(sphere.spiral_layout(256))
        
        # point shader; simple coloured circles, with no spherical correction
        point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])
        self.point_vbo = ShaderVBO(point_shader, IBuf(np.arange(len(pts))), 
                                    buffers={"position":VBuf(pts), },
                                    vars={"constant_size":10.0,                                    
                                    }, 
                                    attribs={"color":(1,1,1,1)},
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
        
        self.point_vbo.draw(vars={"quat":self.rotater.orientation})

    def tick(self):        
        self.rotater.update()
        pass
        
                        

              
if __name__=="__main__":
    p = RotationTest()
    
    
   