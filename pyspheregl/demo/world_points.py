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

import zipfile

def load_cities():
    city_zip = resource_file("data/cities1000.zip")
    lonlats_radians = []
    with zipfile.ZipFile(city_zip) as z:
        all_cities = z.open("cities1000.txt")
        for line in all_cities:
            fields = line.split("\t")
            lat, lon = float(fields[4]), -float(fields[5])
            lonlats_radians.append([np.radians(lon), np.radians(lat)])

    return np.array(lonlats_radians, dtype=np.float32)
            
    

class WorldPoints(object):
    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw, 
        tick_fn=self.tick,
        touch_fn=self.touch)
        self.rotater = RotationHandler(rotater.EQUATORIAL)                
        
        world_indices, world_verts, world_texs = make_unit_quad_tile(1)            
        world_texture = pyglet.image.load(resource_file("data/azworld.png"))
        whole_shader = shader_from_file([getshader("sphere.vert"), getshader("user/whole_sphere.vert")], [getshader("user/whole_sphere_tex.frag")]) 
        self.world_render = ShaderVBO(whole_shader, IBuf(world_indices), 
                                         buffers={"quad_vtx":VBuf(world_verts),},
                                         textures={"tex":world_texture.texture})
        pts = load_cities()
        
        # point shader; simple coloured circles, with no spherical correction
        point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])
        self.point_vbo = ShaderVBO(point_shader, IBuf(np.arange(len(pts))), 
                                    buffers={"position":VBuf(pts), },
                                    vars={"constant_size":1,                                    
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
        self.world_render.draw()
        self.point_vbo.draw(vars={"quat":self.rotater.orientation})

    def tick(self):        
        self.rotater.update(1/60.0)
        pass
        
                        

              
if __name__=="__main__":
    p = WorldPoints()
    
    
   