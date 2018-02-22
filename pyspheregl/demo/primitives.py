import numpy as np
import pyglet
from pyglet.gl import *

# sphere stuff
from ..sim.sphere_sim import getshader, resource_file
from  ..sim import sphere_sim
from ..sphere import sphere
from ..utils.shader import ShaderVBO, shader_from_file

import time
from ..utils.np_vbo import VBuf, IBuf
from ..utils.graphics_utils import make_unit_quad_tile, make_circle_fan
from ..utils import transformations as tn

    

class Primitives(object):
    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw, touch_fn=self.touch)


        refs = {'npole':[0.0, np.pi/2-0.0001], 'spole':[0,-np.pi/2+1e-2], 'gmq':[0,0], 'wmq':[np.pi/2,0], 'emq':[-np.pi/2,0], 'rmq':[np.pi,0], 'cm':[0, 0.25*np.pi],
        'em':[-np.pi/2,0.125*np.pi], 'wm':[np.pi/2,0.125*np.pi],}
        colors = {'npole':[0,0,1,1], 'spole':[1,0,0,1], 'gmq':[0,1,0.5,1], 
        'rmq':[0.5,0,1,1], 'emq':[1,1,0,1], 'wmq':[0,1,1,1], 'cm':[0,1,0.5,1], 'em':[1,1,0,1], 'wm':[0,1,1,1]}

        ks = refs.keys()
        pts = np.array([refs[k] for k in ks], dtype=np.float32)
        colors = np.array([colors[k] for k in ks], dtype=np.float32)
        
        line_pts = np.array([refs['npole'], refs['gmq'], refs['gmq'], refs['wmq'], refs['gmq'], refs['emq']])
        
        # point shader; simple coloured circles, with no spherical correction
        point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])
        self.point_vbo = ShaderVBO(point_shader, IBuf(np.arange(len(pts))), 
                                    buffers={"position":VBuf(pts), "color":VBuf(colors)},
                                    vars={"constant_size":30.0}, 
                                    primitives=GL_POINTS)
        
        # line drawing (correct spherical lines)
        line_shader = shader_from_file([getshader("sphere.vert"), getshader("user/line.vert")], [getshader("user/line.frag")], 
                                        geoms=[getshader("sphere.vert"), getshader("user/line.gs")])

        self.line_vbo = ShaderVBO(line_shader, IBuf(np.arange(len(line_pts))), 
                            buffers={"position":VBuf(line_pts)},
                            vars={"constant_color":[1.0,1.0,1.0,1.0], "subdiv":32}, 
                            primitives=GL_LINES)

        # create a subdivided quad to be drawn
        ixs, quad, texs = make_unit_quad_tile(64)
        
        
        # grid shader, across the whole sphere
        whole_shader = shader_from_file([getshader("sphere.vert"), getshader("user/whole_sphere.vert")], [getshader("user/whole_sphere_grid.frag")])        
        self.whole_vbo = ShaderVBO(whole_shader, IBuf(ixs), 
                            buffers={"quad_vtx": VBuf(quad)})


       

        # simple flat quad shader
        quad_shader = shader_from_file([getshader("sphere.vert"), getshader("user/quad.vert")], [getshader("user/quad_color.frag")])               
        self.quad_vbo = ShaderVBO(quad_shader, IBuf(ixs), 
                            buffers={"quad_vtx": VBuf(quad, divisor=0),
                                    "position":VBuf(pts, divisor=1)}, 
                            attribs={"fcolor":(0.5, 1.0, 0.2, 0.25),
                                    "up_vector":(0.0,0.0,1.0)},
                            vars={"scale":0.5})

        
        # simple circle shader    
        # uses same shader as the quads
        # works for any planar polygon
        circle_ixs, circle_verts = make_circle_fan(64)   
        self.circle_vbo = ShaderVBO(quad_shader, IBuf(circle_ixs), 
                            buffers={"quad_vtx": VBuf(circle_verts, divisor=0),
                                    "position":VBuf(pts, divisor=1)}, 
                            attribs={"fcolor":(0.5, 1.0, 0.2, 0.25)},
                            vars={"scale":0.5}, primitives=GL_TRIANGLE_FAN)



        # whole sphere gradient, from an image texture
        grad_shader = shader_from_file([getshader("sphere.vert"), getshader("user/whole_sphere.vert")], [getshader("user/whole_sphere_gradient.frag")])
        grad_image = pyglet.image.load(resource_file("data/gradient_aquatic.png"))
        self.grad_vbo = ShaderVBO(grad_shader, IBuf(ixs),         
                    buffers={"quad_vtx": VBuf(quad)},
                    vars={"gradient_axis":(0.0,0.0,1.0)},
                    textures={"tex":grad_image.texture})

        
        
        self.touch_pt = [0,0]
        self.viewer.start()

    def touch(self, events):        
        for event in events:
            if event.event=="DRAG":
                self.touch_pt = event.touch.lonlat

    def draw(self):
        glClearColor(0.1,0.1,0.1,1)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)
        glEnable(GL_POINT_SPRITE)
        x, y, z = sphere.polar_to_cart(self.touch_pt[0], self.touch_pt[1])
        self.grad_vbo.draw(vars={"gradient_axis":(x,-y,-z)})
        self.quad_vbo.draw(n_prims=8)
        self.whole_vbo.draw()
        self.point_vbo.draw()
        self.line_vbo.draw()
        self.circle_vbo.draw(n_prims=8)
        
        
        

              
if __name__=="__main__":
    p = Primitives()
    
    
   