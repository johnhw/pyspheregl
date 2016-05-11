import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *
import pygame,time,sys,random,math
import glskeleton, glutils, random
import gloffscreen
import sphere_sim
import sphere
import itertools
import shader


def spiral_layout(n, C=3.6, phi_range=[0, 2*np.pi/3.0]):
    """Return the spherical co-ordinates [phi, theta] for a uniform spiral layout
    on the sphere, with n points. 
    From Nishio et. al. "Spherical SOM With Arbitrary Number of Neurons and Measure of Suitability" 
    WSOM 2005 pp. 323-330"""    
    phis = []
    thetas = []
    for k in range(n):
        h = (2*k)/float(n-1) - 1
        phi = np.arccos(h)
        if k==0 or k==n-1:
            theta = 0
        else:
            theta = thetas[-1] + (C/np.sqrt(n*(1-h**2)))
            
        phis.append(phi)
        thetas.append(theta)        
    
    
            
    return phis, thetas

import transformations

def spherical_flat_circle(pt, rad, n=20):
    centre = sphere.spherical_to_cartesian(pt)
    rotate = transformations.rotation_matrix(2*np.pi/n,centre)[:3,:3]    
    pt = np.cross(np.array(centre), np.array([0,0,1]))
    pt = pt/np.linalg.norm(pt)
    pt = (pt-centre)*rad + centre
    pts = []
    norms = []
    for i in range(n):                
        pt = np.dot(pt, rotate)
        pts.append(pt)
        norms.append(np.array(centre))
    return pts, norms


if __name__ == "__main__":
    s = sphere_sim.make_viewer()
    size = s.size

    with open("shader_sphere_torus.vert") as v:
            v_shader = v.read()
    with open("shader_sphere.frag") as f:
            f_shader = f.read()     
        
    shader = shader.Shader(v_shader, f_shader)
    
    
    
    def draw_fn():
        global first
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
        glDisable(GL_DEPTH_TEST)
        glClearColor(1,1,1,1)
        glClear(GL_COLOR_BUFFER_BIT)

        def draw_polar(pts):
            for x,y in pts:
                x,y,z =  sphere.spherical_to_cartesian((x,y))                

        shader.bind()
        shader.uniformf("resolution", 1920)
        shader.uniformf("torus_rotate", time.clock())
        glPointSize(20.0)
        rad = 0.03 * np.pi
        phis,thetas = spiral_layout(100)


        for pt in zip(phis,thetas):
            lat, lon = pt
            lat -= np.pi/2
         
            pts, norms = spherical_flat_circle((lon, lat), rad)
            glColor4f(0.5, 0.5, 0.0, 0.5)                                
        
            glBegin(GL_POLYGON)
            for pt, norm in zip(pts, norms):
                x,y,z = pt
                nx,ny,nz = norm                 
                glNormal3f(nx,ny,nz)                                    
                glVertex3f(x,y,z)                                    

            glEnd()   

            pts, norms = spherical_flat_circle((lon+np.pi, lat), rad)
            glBegin(GL_POLYGON)
            for pt, norm in zip(pts, norms):
                x,y,z = pt
                nx,ny,nz = norm                 
                glNormal3f(-nx,-ny,-nz)                                    
                glVertex3f(x,y,z)                                    

            glEnd()                        
                            


        shader.unbind()

    s.draw_fn = draw_fn
    s.start()
