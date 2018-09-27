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

from ..utils.graphics_utils import make_unit_quad_tile, make_circle_fan

class TextureRotationTest(object):
    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw, 
        tick_fn=self.tick,
        touch_fn=self.touch)
        self.rotater = RotationHandler()                

        ixs, quad, texs = make_unit_quad_tile(1)
        
        world_shader= shader_from_file([getshader("sphere.vert"), getshader("user/whole_sphere.vert")], [getshader("sphere.vert"), getshader("user/whole_sphere_tex_rotatable.frag")])

        world_image = pyglet.image.load(resource_file("data/azworld.png"))

        self.world_vbo = ShaderVBO(world_shader, IBuf(ixs),
                        buffers={"quad_vtx": VBuf(quad)},
                        textures={"tex":world_image.texture})

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
    
        self.world_vbo.draw(vars={"quat":self.rotater.orientation})

    def tick(self):        
        self.rotater.update(1/60.0)
        pass                            
              
if __name__=="__main__":
    p = TextureRotationTest()
    
   