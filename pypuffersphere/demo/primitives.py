import numpy as np
import pyglet
from pyglet.gl import *

# sphere stuff
from pypuffersphere.sim.sphere_sim import getshader
import pypuffersphere.sim.sphere_sim as sphere_sim
import pypuffersphere.sphere.sphere as sphere
from pypuffersphere.utils.shader import ShaderVBO, shader_from_file

import time
from pypuffersphere.utils.np_vbo import VBuf, IBuf
from pypuffersphere.utils.graphics_utils import make_unit_quad_tile

class Primitives(object):
    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw)

        refs = {'npole':[0, np.pi/2], 'spole':[0,-np.pi/2], 'gmq':[0,0], 'wmq':[np.pi/2,0], 'emq':[-np.pi/2,0], 'rmq':[np.pi,0]}
        colors = {'npole':[0,0,1,1], 'spole':[1,0,0,1], 'gmq':[0,1,0.5,1], 'rmq':[0.5,0,1,1], 'emq':[1,1,0,1], 'wmq':[0,1,1,1]}

        ks = refs.keys()
        pts = np.array([refs[k] for k in ks], dtype=np.float32)
        colors = np.array([colors[k] for k in ks], dtype=np.float32)
        
        line_pts = np.array([refs['npole'], refs['gmq'], refs['gmq'], refs['wmq'], refs['gmq'], refs['emq']])
        
        
        whole_shader = shader_from_file([getshader("sphere.vert"), getshader("user/whole_sphere.vert")], [getshader("user/whole_sphere_rgb.frag")])

        point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])
        line_shader = shader_from_file([getshader("sphere.vert"), getshader("user/line.vert")], [getshader("user/line.frag")], 
                                        geoms=[getshader("sphere.vert"), getshader("user/line.gs")])
        self.point_vbo = ShaderVBO(point_shader, IBuf(np.arange(len(pts))), buffers={"position":VBuf(pts), "color":VBuf(colors)},
         vars={"constant_size":30.0}, primitives=GL_POINTS)

        self.line_vbo = ShaderVBO(line_shader, IBuf(np.arange(len(line_pts))), buffers={"position":VBuf(line_pts)},
         vars={"constant_color":[1.0,1.0,1.0,1.0], "subdiv":32}, primitives=GL_LINES)

        ixs, quad, _ = make_unit_quad_tile(64)
        
        self.whole_vbo = ShaderVBO(whole_shader, IBuf(ixs), buffers={"quad_vtx": VBuf(quad)})
        self.viewer.start()

    def draw(self):
        glClearColor(0.1,0.1,0.1,1)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)
        glEnable(GL_POINT_SPRITE)
        self.whole_vbo.draw()
        self.point_vbo.draw()
        self.line_vbo.draw()


              
if __name__=="__main__":
    p = Primitives()
    
    
   