import sys,time,os,random,cPickle, math
import traceback

import pygame, thread
from pygame.locals import *
from ctypes import *
import thread
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import glutils

#from OpenGL.GL.ARB.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_object import *
from OpenGL.GL.EXT.framebuffer_multisample import *

class OffscreenRenderer:
        
        
    def setup_texture(self, width, height, aspect=1.0):
        self.ftarget= glGenTextures(1)
        self.fbuf = glGenFramebuffersEXT(1)
        self.frender = glGenRenderbuffersEXT(1)

        # bind the texture and set its parameters
        glBindTexture( GL_TEXTURE_2D, self.ftarget)
        glTexEnvf( GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE )
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,GL_REPEAT)
        glTexParameterf( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        # allocate 512x512 
        glTexImage2D(GL_TEXTURE_2D, 0,GL_RGBA,width,height,0,GL_RGBA,GL_UNSIGNED_INT, None)
        
        # bind the frame buffer
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.fbuf)
        
        # create a depth buffer        
        
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, self.frender)
        glRenderbufferStorageEXT( GL_RENDERBUFFER_EXT, GL_DEPTH_COMPONENT24, width, height)
        
        # unbind the framebuffer/renderbuffer
        glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_RENDERBUFFER_EXT, self.fbuf)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, 0)
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
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, self.frender)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.fbuf)
        
        
        # bind the framebuffer
        glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT,GL_TEXTURE_2D, self.ftarget, 0)                
        glFramebufferRenderbufferEXT( GL_FRAMEBUFFER_EXT, GL_DEPTH_ATTACHMENT_EXT, GL_RENDERBUFFER_EXT, self.frender)
        
        # push the viewport and reset it 
        glPushAttrib(GL_VIEWPORT_BIT)
        glViewport(0, 0, self.width, self.height)
        
        
    def end_offscreen(self):
        # disable render buffer        
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
        glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, 0)
        
        # restore viewport and transform matrix
        glPopAttrib()
        
        
        
    def bind_offscreen_texture(self):
        glBindTexture( GL_TEXTURE_2D, self.ftarget)
        
                
