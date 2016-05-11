import numpy as np
import pyglet
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *
import pygame,time,sys,random,math
import random, sys

from . import glskeleton, glutils, gloffscreen

def subdivide_triangles(vertices, faces):
    """Subdivide triangles forming a polyhedron to produce a higher resolution result.
    Quadruples the number of triangles.
    
    Parameters:
        vertices: vertex array for the input triangles
        faces:    index array for the input triangles
        
    Returns:
        vertices, faces
        vertices: vertex array for the subdivided triangles
        faces:    index array for the subdivided triangles
    """       
    newfaces = []
    vertices = list(vertices)
    for face in faces:
        # face centroid
        v1 = (vertices[face[0]] + vertices[face[1]])/2
        v2 = (vertices[face[1]] + vertices[face[2]])/2
        v3 = (vertices[face[2]] + vertices[face[0]])/2
        # normalise
        v1 = v1/np.sqrt(np.sum(v1*v1))
        v2 = v2/np.sqrt(np.sum(v2*v2))
        v3 = v3/np.sqrt(np.sum(v3*v3))
        vindex1 = len(vertices)
        vindex2 = len(vertices)+1
        vindex3 = len(vertices)+2
        vertices.append(v1)
        vertices.append(v2)
        vertices.append(v3)
        # new face
        newfaces.append((vindex3, vindex1, vindex2))        
        newfaces.append((vindex3, face[0], vindex1))
        newfaces.append((vindex2, vindex1, face[1]))
        newfaces.append((face[2],vindex3,  vindex2))
    return np.array(vertices),  np.array(newfaces)
                
def gen_geosphere(iterations):
    """Generate a geosphere from an octahedron, by recursively subdividing
    the faces and normalising to a sphere surface.
    
    Parameters:
        iterations: number of subdivisions to apply. >4 will create very large results
        
    Returns:
        vertices, faces
        vertices:   vertex array for the sphere vertices
        faces:      index array for the triangular sphere faces.
    """
               
    vertices = np.array([
    [0,1.0,0.0],
    [-1.0,0.0,0],
    [.0,0.0,1.0],
    
    [1.0,0.0,.0],
    [0.0,0.0,-1.0],
    [0.0,-1.0,0.0],
    ])
    
    faces = np.array([[0,2,3],[0,1,2],[0,3,4],[0,4,1],
    [5,1,4],[5,3,2],[5,4,3],[5,2,1]])
    
    # normalise the vertices to force them onto the unit sphere
    vs = np.sqrt(np.sum(vertices*vertices, axis=1))
        
    # subdivide for higher resolution
    for i in range(iterations):
        vertices, faces = subdivide_triangles(vertices,  faces)
    
    return vertices, faces
    
def make_grid(resolution):
        """Draw a simple lat, lon grid on a spherical surface"""
        glColor4f(0,1,0,0.8)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(resolution/2,resolution/2)
        glVertex2f(resolution,resolution/2)
        glEnd()
        glLineStipple(1, 0xfff0)
        glEnable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(resolution/2,resolution/2)
        glVertex2f(0,resolution/2)
        glEnd()
        glLineStipple(1, 0xffff)
        glLineWidth(2.0)
        glColor4f(1,0,0,0.5)

        glColor4f(0,1,1,0.8)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(resolution/2,resolution/2)
        glVertex2f(resolution/2,resolution)
        glEnd()
        glLineStipple(1, 0xf0f0)
        glEnable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(resolution/2,resolution/2)
        glVertex2f(resolution/2,0)
        glEnd()
        glLineStipple(1, 0xffff)
        glLineWidth(2.0)
        glColor4f(1,0,0,0.5)


        glBegin(GL_LINE_LOOP)
        n = 60.0
        r = resolution/2
        for i in range(int(n)):
            x,y = 0.5*r*np.cos(2*np.pi*i/float(n)) + r, -0.5*r*np.sin(2*np.pi*i/float(n)) + r
            glVertex2f(x,y)
        glEnd()


        glColor4f(0,0,1,0.1)
        glBegin(GL_LINE_LOOP)
        n = 60.0
        for i in range(int(n)):
            x,y = 0.33333*r*np.cos(2*np.pi*i/float(n)) + r, -0.3333*r*np.sin(2*np.pi*i/float(n)) + r
            glVertex2f(x,y)
        glEnd()

        glColor4f(1,0,1,0.1)
        glBegin(GL_LINE_LOOP)
        n = 60.0
        for i in range(int(n)):
            x,y = 0.666666*r*np.cos(2*np.pi*i/float(n)) + r, -0.66666*r*np.sin(2*np.pi*i/float(n)) + r
            glVertex2f(x,y)
        glEnd()

        
        n = 60.0
        for j in range(36):
            glColor4f(0,0,0,0.02)
            glBegin(GL_LINES)
            glVertex2f(r,r)
            x,y = np.sin(2*np.pi*j/36.0)*r+r, np.cos(2*np.pi*j/36.0)*r+r
            glVertex2f(x,y)
            glEnd()
            glBegin(GL_LINE_LOOP)
            for i in range(int(n)):
                x,y = (j/18.0)*r*np.cos(2*np.pi*i/float(n)) + r, -(j/18.0)*r*np.sin(2*np.pi*i/float(n)) + r
                glVertex2f(x,y)
            glEnd()    

            
class SphereRenderer(object):
    """Class to render a texture onto a spherical surface, used to provide
        simulated sphere visualisation"""

    def recompute_normals(self):
        self.normals = self.compute_normals(self.vertices, self.faces)

    def compute_normals(self, vertices, faces):
        # compute the surface normals for each face, and assign them to the vertices around the face
        # vertex normals are averages from the three faces connected to them
        normals = np.zeros(vertices.shape)
        
        vn0 = vertices[faces[:,0],:]
        vn1 = vertices[faces[:,1],:]
        vn2 = vertices[faces[:,2],:]
        
        nna = vn1 - vn0
        nnb = vn1 - vn2
        nn1 = np.cross(nna,nnb)
        
        mag_nn1 = np.sqrt(np.sum(nn1*nn1, axis=1))
        nn1[:,0] /= mag_nn1
        nn1[:,1] /= mag_nn1
        nn1[:,2] /= mag_nn1
        
        inverses = np.array([np.dot(nn1[i],vertices[faces[i,0]]) for i in range(len(nn1))])
        
        nn1[np.nonzero(inverses<0)] = -nn1[np.nonzero(inverses<0)]
                        
        normals[faces[:,0]] += nn1
        normals[faces[:,1]] += nn1
        normals[faces[:,2]] += nn1
        
        mag_normals = np.sqrt(np.sum(normals*normals, axis=1))
        normals[:,0] /= mag_normals
        normals[:,1] /= mag_normals
        normals[:,2] /= mag_normals
        return normals
        
        
    def compute_uv(self, vertices, faces):
        """Compute UV co-ordinates for the triangles for an azimuthal equidistant projection"""
        uv = np.zeros((vertices.shape[0], 2))
        
        lat = np.arccos(vertices[:,2])/np.pi
        lon = np.arctan2(vertices[:,0], vertices[:,1])
        uv[:,0] = (np.cos(lon) * lat) / 2  + 0.5
        uv[:,1] = (-np.sin(lon)*lat) / 2 + 0.5
        return uv
        
    def make_grid(self):
        make_grid(self.size)
              
    def __init__(self,size=1024,background=None, color=(1.0,1.0,1.0,1.0)):
       self.vertices,self.faces = gen_geosphere(6)       
       self.normals = self.compute_normals(self.vertices, self.faces)
       self.uv = self.compute_uv(self.vertices, self.faces)
       self.offscreen = gloffscreen.OffscreenRenderer(size,size)              
       self.size = size
       self.offscreen.begin_offscreen()    
       glClearColor(*color)
       glClear(GL_COLOR_BUFFER_BIT)         
       glLoadIdentity()    
       if background:
            background_tex,_,_ = glutils.load_texture(background)
            self.offscreen.set_ortho()                    
            glBindTexture(GL_TEXTURE_2D, background_tex)
            self.offscreen.fullscreen_quad(self.size, self.size)                                   
       glClearColor(0.0, 0.0, 0.0, 1.0)
       
       self.offscreen.end_offscreen()
            
    def begin(self):
        # reroute all draw calls to the offscreen texture buffer
        self.offscreen.begin_offscreen()
        
    def end(self):
        # reroute draw calls back to the screen
        self.offscreen.end_offscreen()
        
    def render(self):
        # render the sphere, with lighting and texturing
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        
        self.offscreen.bind_offscreen_texture()
        glVertexPointerf(self.vertices.astype(np.float32))
        glNormalPointerf(self.normals.astype(np.float32))
        glTexCoordPointerf(self.uv.astype(np.float32))
        glColor4f(1,1,1,1)
        glEnable(GL_LIGHTING)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawElementsui(GL_TRIANGLES, self.faces.astype(np.uint32))    
