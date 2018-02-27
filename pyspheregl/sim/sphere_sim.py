import os 
import numpy as np
import pyglet
from pyglet.gl  import *
import time,sys,random,math,os
import timeit
wall_clock = timeit.default_timer

from ..utils import glskeleton,  gloffscreen, np_vbo, shader
from ..sphere import sphere
from ..utils.graphics_utils import make_unit_quad_tile
from ..sim.sim_rotation_manager import RotationManager
from ..sim.touch_manager import ZMQTouchHandler



def resource_file(fname):
    dir_path = os.path.dirname(os.path.realpath(__file__))        
    return os.path.normpath(os.path.join(dir_path, "..", fname))

def getshader(f):
    return resource_file(os.path.join("shaders", f))


def mkshader(verts, frags, geoms=None):
    geoms = geoms or []
    return shader.shader_from_file([getshader(c) for c in verts], 
    [getshader(c) for c in frags], 
    geoms=[getshader(c) for c in geoms])

class TouchFeedback(object):
        def __enter__(self):                
            glColorMaski(1, GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE) 
            
        def __exit__(self, a, b, c):
            glColorMaski(1, GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE) 
  

class SphereViewer:

    def get_whole_sphere_shader_vbo(self, shader):
        # return a shadervbo that will render across the entire
        # sphere. Assumes an input attribute vec2 called position
        return shader.ShaderVBO(shader, self.sphere_quad_ibuf,
                        buffers={"position":self.sphere_quad_vbuf})


    def make_quad(self):
        # create the vertex buffers that will be used to reproject the sphere
        self.fbo = gloffscreen.FBOContext(self.size, self.size)
        self.touch_fbo = gloffscreen.FBOContext(self.window_size[0], self.window_size[1], texture=False)

        self.finger_point_shader = mkshader(["sphere.vert", "sphere_sim/finger_point_nice.vert"], 
        ["sphere_sim/finger_point_nice.frag"])     
        self.finger_line_shader = mkshader(["sphere.vert", "sphere_sim/finger_line.vert"],  
        ["user/line.frag"], geoms=["sphere.vert", "user/line.gs"])     
        self.sphere_map_shader = mkshader(["sphere.vert", "sphere_sim/sphere_map.vert"],
         ["sphere_sim/sphere_map.frag"])        
        self.touch_shader = mkshader(["sphere.vert", "sphere_sim/sphere_touch.vert"], 
        ["sphere_sim/sphere_touch.frag"])                
        self.whole_shader = mkshader(["sphere.vert", "user/whole_sphere.vert"], 
                                    ["user/whole_sphere_tex.frag"])        
        
        n_subdiv = 128        
        quad_indices, quad_verts, _ = make_unit_quad_tile(n_subdiv)    
        qverts = np_vbo.VBuf(quad_verts)      
        qixs = np_vbo.IBuf(quad_indices)
        self.sphere_quad_ibuf = qixs
        self.sphere_quad_vbuf = qverts
        
        self.sphere_render = shader.ShaderVBO(self.sphere_map_shader, qixs, 
                                         buffers={"position":qverts},
                                         textures={"quadTexture":self.fbo.texture},
                                         vars={"grid_bright":self.debug_grid})


        

        # this will hold positions of active touches for drawing
        self.touch_pts = np.zeros((256, 3))        
        self.touch_buf = np_vbo.VBuf(self.touch_pts)

        # whols ecreen shader
        quad_indices, quad_verts, _ = make_unit_quad_tile(1)            

        screen_shader =mkshader(["sphere_sim/screen_quad.vert"], ["sphere_sim/screen_quad.frag"]) 
        self.screen_render = shader.ShaderVBO(screen_shader, np_vbo.IBuf(quad_indices),
            buffers={"position":np_vbo.VBuf(quad_verts)},
            textures={"quadTexture":self.fbo.texture})

        touch_ibuf = np_vbo.IBuf(np.arange(len(self.touch_pts)))
        self.touch_render = shader.ShaderVBO(self.finger_point_shader, 
                                         touch_ibuf, 
                                         buffers={"position":self.touch_buf},
                                         primitives=GL_POINTS)
        self.touch_line_render = shader.ShaderVBO(self.finger_line_shader, 
                                         touch_ibuf, 
                                         buffers={"position":self.touch_buf},
                                         primitives=GL_LINES)
        # simple quad render for testing
        world_indices, world_verts, world_texs = make_unit_quad_tile(64)            
        

        self.world_render = shader.ShaderVBO(self.whole_shader, np_vbo.IBuf(world_indices), 
                                         buffers={"quad_vtx":np_vbo.VBuf(world_verts),},
                                         textures={"tex":self.world_texture.texture})
        # for getting touches back
        self.sphere_touch = shader.ShaderVBO(self.touch_shader, qixs, 
                                            buffers={"position":qverts})

        
    def test_render(self):
        self.world_render.draw(n_prims=0)
      

    def __init__(self,  product, exit_fn=None,  auto_spin=False, draw_fn=None, 
        tick_fn=None, debug_grid=0.1, test_render=False, show_touches=True,
        zmq_address="tcp://localhost:4000", touch_fn=None, simulate_touches = True):
        
    
        self.product = product
        self.simulate = product["test_mode"]
        self.show_touches = show_touches
        self.debug_grid = debug_grid # overlaid grid on sphere simulation        
        if not test_render:            
            self.draw_fn = draw_fn
        else:
            self.draw_fn = self.test_render # simple test function to check rendering        
        self.tick_fn = tick_fn                
        self.touch_fn = touch_fn
        self.exit_fn = exit_fn
        self.world_texture = pyglet.image.load(resource_file("data/azworld.png"))
        self.rotation_manager = RotationManager(auto_spin=auto_spin)
        sphere_resolution = product["virtual_resolution"]
        self.size = sphere_resolution
        if self.simulate:
            window_size = (800, 800)
        else:
            window_size = (product["width"], product["height"])

        self.window_size = window_size
        self.skeleton = glskeleton.GLSkeleton(draw_fn = self.redraw, resize_fn = self.resize, 
                                              tick_fn=self.tick, mouse_fn=self.mouse, key_fn=self.key, exit_fn=self._exit, window_size=window_size)

        # texture read back from the GPU representing touchable objects
        self.feedback_buf = np.zeros((self.size, self.size), dtype=np.uint32)
        
        self.touch_manager = ZMQTouchHandler(zmq_address, feedback_buf=self.feedback_buf)
        self.simulate_touches = simulate_touches

        
        if not self.simulate:
            cx = window_size[0] - sphere_resolution
            cy = window_size[1] - sphere_resolution                        
            glViewport(cx/2,0,sphere_resolution,sphere_resolution)
            self.simulate_touches = False

        # used for FPS limiting
        self.last_frame_time = wall_clock()
        self.make_quad()

    def _exit(self):
        if self.exit_fn is not None:
            self.exit_fn()
        
    # called to exit the simulator
    def exit(self):
        self.skeleton.exit()
      
    # return all touches currently down
    def get_touches(self):
        return self.touch_manager.active_touches

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
        if buttons is not None:
            # drag sphere with left mouse
            if buttons & pyglet.window.mouse.LEFT:
                if event=="press":    
                    self.rotation_manager.press(x,y)                
                if event=="drag":
                    self.rotation_manager.drag(x,y)    
                if event=="release":
                    self.rotation_manager.release(x,y)    
            
            # simulated touches with right mouse
            if buttons & pyglet.window.mouse.RIGHT:
                if event=="press":    
                    self.rotation_manager.touch_down(x,y)
                if event=="drag":
                    self.rotation_manager.touch_drag(x,y)
                if event=="release":
                    self.rotation_manager.touch_release(x,y)
                
                
    def key(self, event, symbol, modifiers):
        if event=='press' and symbol==pyglet.window.key.LSHIFT:
            self.rotation_manager.lock_rotation()
        if event=='release' and symbol==pyglet.window.key.LSHIFT:
            self.rotation_manager.unlock_rotation()        
        if symbol==pyglet.window.key.ESCAPE:       
            self.exit()     
                        
    
    def tick(self):        
        if self.tick_fn:
            self.tick_fn()
        if self.simulate_touches:
            self.rotation_manager.tick() # simulation rotation
        self.touch_manager.tick(self.touch_fn) # touch handling
            
    def draw_touch_points(self):
        # draw the touch points
        pt = self.rotation_manager.get_touch_point()
        
        # clear the buffer
        self.touch_pts[:] = 0
        self.touch_pts[:,1] = -np.pi
    
        # force the simulated touch to be drawn
        self.touch_pts[0:2,0:2] = pt        
        self.touch_pts[0:2,1] = -self.touch_pts[0:2,1]
        self.touch_pts[0:2,2] = 1.0
        
        # we write in the touches in order:
        # current position (xy), brightness (z)
        # origin poisition (xy), 0 (z)
        # this means the point shader will draw only the active positions
        # but the line shader will draw lines connecting them
        i = 2
        for touch_id, touch in self.touch_manager.active_touches.items():
            if i>=len(self.touch_pts): # make sure we don't overrun the touch buffer
                break            
            self.touch_pts[i, 0:2] = touch.lonlat
            self.touch_pts[i, 2] = min(1.0, touch.duration*40)  - min(1.0, touch.dead_time*2)
            self.touch_pts[i+1, 0:2] = touch.origin
            self.touch_pts[i+1, 2] = 0            
            i += 2

        self.touch_buf.set(self.touch_pts)
        self.touch_line_render.draw()      
        self.touch_render.draw()
                        
    
    def redraw(self):          
        self.last_frame = wall_clock()
        glEnable(GL_BLEND)        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # clear the screen
        glClearColor(0.1, 0.1, 0.1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # enable point drawing for touch point        
        glPixelStorei(GL_PACK_ALIGNMENT, 1)     
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SPRITE)
        glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)

        with self.fbo as f:         
            # clear the touch buffer
            
            # write layout 0 to the color buffer
            # write layout 1 to the touch feedback buffer
            bufs = (GLuint * 2)(GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1)                
            glDrawBuffers(2, bufs)            
            # enable writing to the touch buffer
            with TouchFeedback():
                glClearColor(0.0, 0.0, 0.0, 0.0)
                glClear(GL_COLOR_BUFFER_BIT)
            
            if self.draw_fn is not None:      
                # enable writing to the touch buffer                
                self.draw_fn()   

                        
            if self.show_touches:                   
                self.draw_touch_points()          

        if self.simulate:
            # render onto the screen using the sphere distortion shader    
            rotate, tilt = self.rotation_manager.get_rotation()
            self.sphere_render.draw(vars={"rotate":np.radians(rotate),
                     "tilt":np.radians(tilt)})
                        
            # render the image for the touch point look up
            # this is colour map mapping each screen coordinate to a lat lon position
            touch_pos = self.rotation_manager.get_mouse_pos()

            if touch_pos:
                with self.touch_fbo as f:                
                    self.sphere_touch.draw(vars={"rotate":np.radians(rotate), "tilt":np.radians(tilt)})                    
                    pixel_data = (GLubyte * 4)()
                    # get window coordinates
                    mx, my = touch_pos                    
                    # read the pixels, convert back to radians (from unsigned bytes)
                    glReadPixels(mx, my, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, pixel_data)                                                
                    sphere_lon, sphere_lat =  ((pixel_data[0]/255.0)-0.5)*2*np.pi, ((pixel_data[1] / 255.0) -0.5) * np.pi,
                    # tell the touch manager where the touch is
                    self.rotation_manager.set_sphere_touch(sphere_lon, sphere_lat)
        else:
            # render onto a flat quad
            self.screen_render.draw()

        # retrieve the feedback buffer
        glBindTexture(self.fbo.touch_texture.target, self.fbo.touch_texture.id)
           
        glGetTexImage(self.fbo.touch_texture.target, 0, GL_RED_INTEGER, 
        GL_UNSIGNED_INT, self.feedback_buf.ctypes.data)        
        
            

        
    
from .products import get_product

def make_viewer(**kwargs):    
    product = get_product(product=kwargs.get("product"), test_mode=kwargs.get("sim"))
    print("Using %s device" % product["product"])
    sim = product["test_mode"]
    s = SphereViewer(product=product, **kwargs)
    return s

