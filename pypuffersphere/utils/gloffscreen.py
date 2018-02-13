import sys,time,os,random, math
import traceback
from ctypes import *
import thread
from pyglet.gl import *

from pypuffersphere.utils import np_vbo, shader

class OffscreenRenderer:
        
    def __init__(self, width, height):
        aspect = float(width)/float(height)

        self.fbo_texture, self.fbo_buffer, self.fbo_renderbuffer = GLuint(), GLuint(), GLuint()
        glGenTextures(1, self.fbo_texture)
        glGenFramebuffers(1 ,self.fbo_buffer)
        
        # bind the texture and set its parameters
        # create a texture
        glBindTexture(GL_TEXTURE_2D, self.fbo_texture)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,GL_REPEAT)
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)        
        glTexImage2D(GL_TEXTURE_2D, 0,GL_RGBA,width,height,0,GL_RGBA,GL_UNSIGNED_INT, None)
        
        # bind the frame buffer to the texture as the color render target
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_buffer)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.fbo_texture, 0)

        # create a depth buffer (as a render buffefr) and attach it        
        glGenRenderbuffers(1, self.fbo_renderbuffer)
        glBindRenderbuffer(GL_RENDERBUFFER, self.fbo_renderbuffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)                
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.fbo_buffer)

        # unbind the framebuffer/renderbuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        self.width = width
        self.height = height
        self.aspect = aspect
        self.render_width = int(self.width*self.aspect)
        self.render_height = int(self.height)
        
    

    def __enter__(self):        
        #enable render buffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_buffer)        
        self.real_viewport = (GLuint * 4)()
        glGetIntegerv(GL_VIEWPORT, viewport)
        glViewport(0, 0, self.width, self.height)
        
        
    def __exit__(self, exc_type, exc_value, traceback):
        # disable render buffer        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(*self.real_viewport)
        
      