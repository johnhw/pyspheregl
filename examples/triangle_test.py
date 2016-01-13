import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *
import pygame,time,sys,random,math
import glskeleton, glutils, random
import gloffscreen
# import sphere_sim_shader as sphere_sim
from sphere_sim import make_grid
import sphere_cy as sphere
import itertools
import pyglet
import sphere_sim
t = 0
if __name__ == "__main__":
    
    
    size = 1920   
    s = sphere_sim.make_viewer()
    cat_image = pyglet.image.load("leaf.png")
    cat_texture = cat_image.texture.id

    vs = []
    
    def redraw():
        global t
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_LIGHTING)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, size, 0, size, -1, 500)
        glMatrixMode(GL_MODELVIEW)    
        glLoadIdentity()
        glEnable(GL_POINT_SMOOTH)
        glPointSize(2.0)
        glColor4f(1,0,1,1)
        glDisable(GL_TEXTURE_2D)
        glLineWidth(2.0)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)


        glClearColor(1,1,1,1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)
        make_grid(size)
        
        """
        vertices = [[0.1, 0.3], [0.9, 1.4], [-0.9, 0.35]]
        vertices, faces, uv = sphere.spherical_triangle(vertices, iter=4)
        glColor4f(1,0,0,1)
        vertices = [sphere.polar_to_display(v[0], v[1], resolution=size) for v in vertices]
        glLineWidth(0.5)
        for face in faces:
            glBegin(GL_LINE_LOOP)
            glVertex2f(*vertices[face[0]])
            glVertex2f(*vertices[face[1]])
            glVertex2f(*vertices[face[2]])            
            glEnd()
        
        vertices = [[0.1, 0.1], [0.1, 1.0], [0.5, 1.0], [0.5, 0.1]]
        vertices, faces, uv = sphere.spherical_quad(vertices, iter=3)
        glColor4f(0,1,0,1)
        vertices = [sphere.polar_to_display(v[0], v[1], resolution=size) for v in vertices]
        glLineWidth(0.5)
        for face in faces:
            glBegin(GL_LINE_LOOP)
            glVertex2f(*vertices[face[0]])
            glVertex2f(*vertices[face[1]])
            glVertex2f(*vertices[face[2]])            
            glVertex2f(*vertices[face[3]])            
            glEnd()
        """
        
        t += 0.01
        k = np.sin(t)
        
        if k<0:
            center = [np.cos(t)/2, np.sin(t)/2]
            up = [0.0, 0.0]
        else:
            center = [np.cos(t)/2, np.sin(t)/2]
            up = [0.0, np.pi/2]
        width  = 0.5
        height = 0.5
        
        print center, width, height, up
        
        vertices, faces, uv = sphere.spherical_rectangle(center, width, height, up, iter=3)
     
        glBindTexture(GL_TEXTURE_2D, cat_texture)
        glEnable(GL_TEXTURE_2D)
        glColor4f(1,1,1,1)
        vertices = [sphere.polar_to_display(v[0], v[1], resolution=size) for v in vertices]
        glLineWidth(0.5)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointerf(vertices)
        glTexCoordPointerf(uv)
        glDrawElementsus(GL_QUADS, faces)        
        
            
        glDisable(GL_TEXTURE_2D)
        connector = sphere.spherical_line(center, up)
        glColor4f(0,1,1,1)
        glLineWidth(1.0)
        glBegin(GL_LINE_STRIP)
        for pt in connector:
            glVertex2f(*sphere.polar_to_display(pt[0], pt[1], resolution=size))            
        glEnd()

        circle = sphere.spherical_circle((np.radians(0), np.radians(0)), np.radians(10))
        glColor4f(1,0,0,1)
        glBegin(GL_POLYGON)
        for pt in circle:
            glVertex2f(*sphere.polar_to_display(pt[0], pt[1], resolution=size))            
        glEnd()

    s.draw_fn = redraw
    s.start()
