import sys,time,os,random,cPickle, math
import traceback

import pygame, thread
from pygame.locals import *

import thread
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import pyglet

def create_sprite_list(texture, width, height, center=False):
    newList = glGenLists(1)
    glNewList(newList,GL_COMPILE);
    glBindTexture(GL_TEXTURE_2D, texture)
    glBegin(GL_QUADS)
    if center:
        glTexCoord2f(0, 0); glVertex2f(-width/2, -height/2)    # Bottom Left Of The Texture and Quad
        glTexCoord2f(0, 1); glVertex2f(-width/2, height/2)    # Top Left Of The Texture and Quad
        glTexCoord2f(1, 1); glVertex2f( width/2,  height/2)    # Top Right Of The Texture and Quad
        glTexCoord2f(1, 0); glVertex2f(width/2, -height/2)    # Bottom Right Of The Texture and Quad
    else:
        glTexCoord2f(0, 0); glVertex2f(0,0)    # Bottom Left Of The Texture and Quad
        glTexCoord2f(0, 1); glVertex2f(0, height)    # Top Left Of The Texture and Quad
        glTexCoord2f(1, 1); glVertex2f( width,  height)    # Top Right Of The Texture and Quad
        glTexCoord2f(1, 0); glVertex2f(width, 0)    # Bottom Right Of The Texture and Quad
    glEnd()
    glEndList()    
    return newList


def gen_texture():
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    return texture

# load a texture and return it
def load_texture(surface, texture):    
    textureData = pygame.image.tostring(surface, "L", 1)    
    width = surface.get_width()
    height = surface.get_height()    
    glTexImage2D( GL_TEXTURE_2D, 0, GL_L, width, height, 0, GL_L, GL_UNSIGNED_BYTE, textureData)  
    
         
def basic_lighting():
    ambient = [0.05, 0.05, 0.05,1.0]
    ambient_color = [1,1,1,1]
    position = [-18.5, -21.0, 10.0, 1.0]
    mat_diffuse = [0.4, 0.6, 0.5, 1.0]
    mat_specular = [1.0, 1.0, 1.0, 1.0]
    mat_shininess = [100.0]

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, ambient)
    glLightfv(GL_LIGHT0, GL_POSITION, position)

    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, ambient_color)
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)
    glLightModelfv(GL_LIGHT_MODEL_TWO_SIDE, 1.0)
    glShadeModel(GL_SMOOTH)

    
# Skeleton class                                          
class GLSkeleton:

    #initialize opengl with a simple ortho projection
    def init_opengl(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.w, 0, self.h, -1, 500)
        glMatrixMode(GL_MODELVIEW)
        
        #enable texturing and alpha
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_LINE_SMOOTH)
    
    # Initialise pygame, and load the fonts
    # NOTE not used now
    def init_pygame(self,w,h, fullscreen=False): 
        pygame.init()
        
        #nb: find biggest display mode
        modes = pygame.display.list_modes(32)
        if not modes:
            modes = pygame.display.list_modes(24)
        pygame.display.gl_set_attribute(pygame.locals.GL_MULTISAMPLESAMPLES,4)    
        if fullscreen:
            self.screen = pygame.display.set_mode((w,h),pygame.OPENGL|pygame.DOUBLEBUF|pygame.FULLSCREEN)                  
        else:  
          self.screen = pygame.display.set_mode((w,h),pygame.OPENGL|pygame.DOUBLEBUF)                  
         
        #store screen size
        self.w = self.screen.get_width()
        self.h = self.screen.get_height()
        self.init_opengl()
       
      
    def init_pyglet(self, size):
        width, height= size
        config = None
        # windows only
        if os.name == 'nt':
            config = pyglet.gl.Config(sample_buffers=1, samples=8)
        screens= pyglet.window.get_platform().get_default_display().get_screens()
        self.window = None
        for screen in screens:
            if screen.width==width and screen.height==height:
                self.window = pyglet.window.Window(config=config, fullscreen=True, screen=screen)
        if not self.window:
            self.window = pyglet.window.Window(config=config, fullscreen=False, width=width, height=height)        
        self.window.set_handler("on_draw", self.on_draw)    
        
        self.window.set_handler("on_key_press", self.on_key_press)
        self.window.set_handler("on_key_release", self.on_key_release)
        self.window.set_handler("on_mouse_motion", self.on_mouse_motion)
        self.window.set_handler("on_mouse_press", self.on_mouse_press)
        self.window.set_handler("on_mouse_release", self.on_mouse_release)
        self.window.set_handler("on_mouse_drag", self.on_mouse_drag)  
        self.window.set_handler("on_resize", self.on_resize)      
        self.w, self.h = self.window.width, self.window.height
        self.init_opengl()
        

    def on_resize(self, w, h):            
            if self.resize_fn:
                    self.resize_fn(w,h)
            return pyglet.event.EVENT_HANDLED

    def on_draw(self):
        if self.draw_fn:
            self.draw_fn()
            
    def on_key_press(self, symbol, modifiers):
        if self.key_fn:
            self.key_fn("press", symbol, modifiers)
    
    def on_key_release(self, symbol, modifiers):
        if self.key_fn:
            self.key_fn("release", symbol, modifiers)
            
    def on_mouse_motion(self, x, y, dx, dy):
        if self.mouse_fn:
            self.mouse_fn("move", x=x,y=y,dx=dx,dy=dy)
            
    def on_mouse_drag(self, x,y, dx, dy, buttons, modifiers):
        if self.mouse_fn:
            self.mouse_fn("drag", x=x,y=y,dx=dx,dy=dy,buttons=buttons,modifiers=modifiers)
                        
    def on_mouse_press(self, x,y, buttons, modifiers):
        if self.mouse_fn:
            self.mouse_fn("press", x=x,y=y,buttons=buttons,modifiers=modifiers)
            
    def on_mouse_release(self, x,y, buttons, modifiers):
        if self.mouse_fn:
            self.mouse_fn("release", x=x,y=y,buttons=buttons, modifiers=modifiers)
            
    def on_mouse_scroll(self, x,y, scroll_x, scroll_y):
        if self.mouse_fn:
            self.mouse_fn("scroll", x=x,y=y,scroll_x=scroll_x, scroll_y=scroll_y)
    
        
    # init routine, sets up the engine, then enters the main loop
    def __init__(self, draw_fn = None, tick_fn = None, event_fn = None, key_fn=None, resize_fn = None, mouse_fn = None, window_size=(800,600), fullscreen=False):    
        #self.init_pygame(window_size[0], window_size[1], fullscreen)
        self.init_pyglet(window_size)
        self.fps = 60
        self.clock = pygame.time.Clock()
        self.start_time = time.clock()
        self.resize_fn = resize_fn
        self.draw_fn = draw_fn
        self.tick_fn = tick_fn        
        self.key_fn = key_fn
        self.mouse_fn = mouse_fn        
        self.running = True
        
    # handles shutdown
    def quit(self):
        self.running = False
        pyglet.app.exit()
        
    # this is the redraw code. Add drawing code between the "LOCK" and "END LOCK" sections
    def flip(self):
          # clear the transformation matrix, and clear the screen too
          glMatrixMode(GL_MODELVIEW)
          glLoadIdentity()          
          if self.draw_fn:
            self.draw_fn()
          
       
            
           
    #frame loop. Called on every frame. all calculation shpuld be carried out here     
    def tick(self, delta_t):  
        time.sleep(0.002)                
        if self.tick_fn:
            self.tick_fn()
      
   
                    
         
    #main loop. Just runs tick until the program exits     
    def main_loop(self):
        pyglet.clock.schedule_interval(self.tick, 1.0/60.0)
        pyglet.app.run()
         
     
