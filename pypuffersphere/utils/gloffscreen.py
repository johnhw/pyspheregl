import sys,time,os,random,cPickle, math
import traceback


from ctypes import *
import thread
from pyglet.gl import *

class OffscreenRenderer:
        
        
    def setup_texture(self, width, height, aspect=1.0):
        self.ftarget, self.fbuf, self.frender = GLuint(), GLuint(), GLuint()
        glGenTextures(1, self.ftarget)
        glGenFramebuffers(1 ,self.fbuf)
        

        # bind the texture and set its parameters
        # create a texture
        glBindTexture(GL_TEXTURE_2D, self.ftarget)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,GL_REPEAT)
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)        
        glTexImage2D(GL_TEXTURE_2D, 0,GL_RGBA,width,height,0,GL_RGBA,GL_UNSIGNED_INT, None)
        
        # bind the frame buffer to the texture as the color render target
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbuf)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.ftarget, 0)

        # create a depth buffer (as a render buffefr) and attach it        
        glGenRenderbuffers(1, self.frender)
        glBindRenderbuffer(GL_RENDERBUFFER, self.frender)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)                
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.fbuf)

        # unbind the framebuffer/renderbuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        self.width = width
        self.height = height
        self.aspect = aspect
        self.render_width = int(self.width*self.aspect)
        self.render_height = int(self.height)
       
        
    def __init__(self, width, height):
        self.setup_texture(width, height, aspect = float(width)/float(height))
        
    def draw(self,width,height):
        self.bind_offscreen_texture()
        glEnable(GL_TEXTURE_2D)
        self.fullscreen_quad(width,height)
        
    def fullscreen_quad(self, w, h):
          
          glBegin(GL_QUADS)          
          glTexCoord2f(0.0,0.0)
          glVertex3f(0,0,0) 
          
          glTexCoord2f(1.0,0.0)
          glVertex3f(w,0,0)          
          
          glTexCoord2f(1.0,1.0)
          glVertex3f(w,h,0)         
          
          glTexCoord2f(0.0,1.0)
          glVertex3f(0,h,0)          
          glEnd()

    
    def set_ortho(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()        
        glOrtho(0, self.render_width, 0, self.render_height, -1, 500)
        glMatrixMode(GL_MODELVIEW)
        
       

    def begin_offscreen(self):
        
        #enable render buffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbuf)
        
        # push the viewport and reset it 
        glPushAttrib(GL_VIEWPORT_BIT)
        glViewport(0, 0, self.width, self.height)
        
        
    def end_offscreen(self):
        # disable render buffer        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glPopAttrib()
        
        
        
    def bind_offscreen_texture(self):
        glBindTexture( GL_TEXTURE_2D, self.ftarget)
        
                
