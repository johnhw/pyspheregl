import numpy as np
import pyglet
from pyglet.gl import *

# sphere stuff
from ..sim.sphere_sim import getshader, resource_file
from  ..sim import sphere_sim
from ..sphere import sphere
from ..utils.graphics_utils import make_unit_quad_tile
from ..utils.shader import ShaderVBO, shader_from_file
from ..utils.np_vbo import VBuf, IBuf
from ..utils import transformations as tn

from ..touch.rotater import RotationHandler
from ..touch import rotater   

class DotsTest(object):
    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw, 
        tick_fn=self.tick,
        touch_fn=self.touch)
        self.rotater = RotationHandler()                

        self.pts = sphere.lon_ring(0, 200) + sphere.lon_ring(30, 200) + sphere.lon_ring(-30, 200) + sphere.lon_ring(90, 200) + sphere.lon_ring(60, 200) + sphere.lon_ring(-60, 200)
        self.pts += sphere.lat_ring(0, 200) + sphere.lat_ring(30, 200) + sphere.lat_ring(-30, 200) + sphere.lat_ring(90, 200) + sphere.lat_ring(60, 200) + sphere.lat_ring(-60, 200)
        self.pts = np.array(self.pts, dtype=float)
        
        point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])
        self.point_vbo = ShaderVBO(point_shader, IBuf(np.arange(len(self.pts))), 
                                    buffers={"position":VBuf(self.pts), },
                                    vars={"constant_size":10,                                    
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
        self.rotater.update(1/60.0)
        pass
        
                        

              
if __name__=="__main__":
    p = DotsTest()
    
    
   