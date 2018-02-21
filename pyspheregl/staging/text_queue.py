import pyglet
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
from fader import Fader
from glyph import TextRender

class TextLabel(object):
    def __init__(self, text,glyph_text, tx=0, ty=0, sphere_mode=False, **kwargs):
        self.fader = Fader(in_time=0.05, out_time=0.2)
        self.size, self.indices, self.vertices, self.texcoords, self.normals, self.colors = glyph_text.generate_geometry(text, **kwargs)
        
        self.tx = tx
        self.ty = ty        
        
        # scale and rearrange vertices for the shader        
        self.sphere_mode = sphere_mode
        if not sphere_mode:
            self.vertices = np.hstack([self.vertices[:,1][:,None], -self.vertices[:,0][:,None]])
        else:
            self.vertices = np.hstack([-self.vertices[:,1][:,None], self.vertices[:,0][:,None]])
        self.fadein()
        
    def fadein(self):
        self.fader.fadein()
        
    def fadeout(self):
        self.fader.fadeout()
        
    def isalive(self):
        return self.fader.fadestate != self.fader.FADEOFF
        
    def update(self, dt):
        self.fader.update(dt)
        
    def draw(self, shader):
        # must have valid client state set and shader bound!
        # draw the points
        glColor4f(1,1,1,self.fader.get())
        glPushMatrix()
        if not self.sphere_mode:
            glTranslatef(self.tx, self.ty, 0)
        else:
            # TODO better way of fixing this?
            glRotatef(180, 0, 0, 1)

        pyglet.gl.glVertexPointer(2, GL_FLOAT, 0, self.vertices.ctypes.data)           
        pyglet.gl.glColorPointer(4, GL_FLOAT, 0, self.colors.ctypes.data)
        pyglet.gl.glTexCoordPointer(2, GL_FLOAT, 0, self.texcoords.ctypes.data)                   
        pyglet.gl.glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, self.indices.ctypes.data)
        glPopMatrix()
        
class TextQueue(object):
    def __init__(self, font):
        self.texts = []
        self.glyph_text = TextRender(font)
        self.glyph_text.load_pages()
        self.texture_id = self.glyph_text.texture().id
        
    def create_label(self, text, **kwargs):
        l = TextLabel(text, self.glyph_text, **kwargs)
        self.texts.append(l)
        l.fadein()
        return l
        
    def clear(self):
        self.texts = []

    def remove_label(self, l):        
        self.texts.remove(l)
        l.fadeout()
        
    def update(self, dt):
        kills = []
        # update the faders
        for l in self.texts:
            l.update(dt)
            if not l.isalive:
                kills.add(l)
                
        # remove all dead labels
        for k in kills:
            self.texts.remove(k)
            
    def draw(self, shader):
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        for l in self.texts:
            l.draw(shader)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
