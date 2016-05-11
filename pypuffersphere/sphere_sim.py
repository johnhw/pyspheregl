import numpy as np
import pyglet
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *
import pygame,time,sys,random,math

from pypuffersphere.utils import glskeleton, glutils, gloffscreen

def subdivide_triangles(vertices, faces):
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
    vertices = np.array([
    [0,1.0,0.0],
    [-1.0,0.0,0],
    [.0,0.0,1.0],
    
    [1.0,0.0,.0],
    [0.0,0.0,-1.0],
    [0.0,-1.0,0.0],
    ])
    
   
    
    faces = np.array([
    [0,2,3],
    [0,1,2],
    [0,3,4],
    [0,4,1],
    [5,1,4],
    [5,3,2],
    [5,4,3],
    [5,2,1]])
    
    
    vs = np.sqrt(np.sum(vertices*vertices, axis=1))
        
    for i in range(iterations):
        vertices, faces = subdivide_triangles(vertices,  faces)
    
    return vertices, faces

def spiral_layout(n, C=3.6):
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
    return np.vstack((np.array(phis), np.array(thetas))).transpose()
        
def spherical_distance(p1, p2):
    """Given two points p1, p2 (in radians), return
    the great circle distance between the two points."""
    lon1, lat1 = p1
    lon2, lat2 = p2
    d=2*np.arcsin(np.sqrt((np.sin((lat1-lat2)/2))**2 + 
                 np.cos(lat1)*np.cos(lat2)*(np.sin((lon1-lon2)/2))**2))    
    return d
        
def make_grid(size):
        glColor4f(0,1,0,0.8)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(size/2,size/2)
        glVertex2f(size,size/2)
        glEnd()
        glLineStipple(1, 0xfff0)
        glEnable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(size/2,size/2)
        glVertex2f(0,size/2)
        glEnd()
        glLineStipple(1, 0xffff)
        glLineWidth(2.0)
        glColor4f(1,0,0,0.5)

        glColor4f(0,1,1,0.8)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(size/2,size/2)
        glVertex2f(size/2,size)
        glEnd()
        glLineStipple(1, 0xf0f0)
        glEnable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(size/2,size/2)
        glVertex2f(size/2,0)
        glEnd()
        glLineStipple(1, 0xffff)
        glLineWidth(2.0)
        glColor4f(1,0,0,0.5)


        glBegin(GL_LINE_LOOP)
        n = 60.0
        r = size/2
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

    def recompute_normals(self):
        self.normals = self.compute_normals(self.vertices, self.faces)

    def compute_normals(self, vertices, faces):
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

                

    def __init__(self,size=1024,background="azworld.png", color=(1.0,1.0,1.0,1.0)):
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
            print("Init bg")
       glClearColor(0.0, 0.0, 0.0, 1.0)
       
       self.offscreen.end_offscreen()
            
    def begin(self):
        self.offscreen.begin_offscreen()
        
    def end(self):
        self.offscreen.end_offscreen()
        
    def render(self):
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
        
        
class SphereViewer:
    def __init__(self, sphere_resolution=1024, window_size=(800,600), background="azworld.png", exit_fn=None, color=(1.0,1.0,1.0,1.0), simulate=True, auto_spin=False, draw_fn=None):
        self.simulate = simulate
        self.size = sphere_resolution
        self.draw_fn = draw_fn
        self.exit_fn = exit_fn
        self.auto_spin = auto_spin
        if self.simulate:
            self.skeleton = glskeleton.GLSkeleton(draw_fn = self.redraw, resize_fn = self.resize, tick_fn=self.tick, mouse_fn=self.mouse, key_fn=self.key, window_size=window_size)
            self.sphere_renderer = SphereRenderer(size=sphere_resolution, background=background, color=color)
            self.sphere_renderer.begin()
        else:
            self.skeleton = glskeleton.GLSkeleton(draw_fn = self.redraw, resize_fn=self.resize, tick_fn=self.tick, mouse_fn=self.mouse, key_fn=self.key, window_size=window_size)            
            cx = window_size[0] - sphere_resolution
            cy = window_size[1] - sphere_resolution            
            glViewport(cx/2,0,sphere_resolution,sphere_resolution)
            self.skeleton.auto_clear = False
        
        self.rotation = [0,0]
        self.last_rotation = [0,0]
        self.rotate_scale = -0.2        
        self.frame_ctr = 0
        self.drag_start = None                
        self.last_touch = time.clock()
        self.spin = 0
        self.target_spin = 0
      
    def resize(self, w, h):
        if not self.simulate:
            cx = w - self.size
            cy = h - self.size            
            glViewport(cx/2,cy/2,self.size,self.size)
        else:
            print(w,h)
            glViewport(0,0,w,h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, w, 0, h, -1, 500)
            glMatrixMode(GL_MODELVIEW)
            
            
    def start(self):
        self.skeleton.main_loop()
        
    def mouse(self, event, x=None, y=None, dx=None, dy=None, buttons=None, modifiers=None, **kwargs):
        if event=="press":        
            self.drag_start = (x,y)
            self.last_rotation = list(self.rotation)
            self.last_touch = time.clock()
        if event=="drag":
            if self.drag_start is not None:
                new_pos = (x,y)
                self.rotation[0] = self.last_rotation[0] + (self.drag_start[0] - new_pos[0]) * self.rotate_scale
                self.rotation[1] = self.last_rotation[1] + (self.drag_start[1] - new_pos[1]) * self.rotate_scale * 0.5
                self.last_touch = time.clock()
        if event=="release":
            self.drag_start = None
            self.last_touch = time.clock()

            
    def key(self, event, symbol, modifiers):
        if symbol==pyglet.window.key.ESCAPE:
            if self.exit_fn:
                self.exit_fn()
            sys.exit(0)
                        
    
    def tick(self):
        if self.simulate:
            self.sphere_renderer.begin()
        if self.draw_fn:
            self.draw_fn()        
        if not self.simulate:
            return
        self.sphere_renderer.end()
        self.redraw()        
        
        if time.clock()-self.last_touch>3 and self.auto_spin:
            self.target_spin = 0.2        
        else:
            self.target_spin = 0.0
        
        self.spin = 0.9 *self.spin + 0.1*self.target_spin    
        self.rotation[0] += self.spin
        
        
    
                        
    def redraw(self):  
            
        if not self.simulate:
            return 

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, float(self.skeleton.w)/float(self.skeleton.h), 1, 2000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # turn on some lights
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.1, 0.1, 0.1,1])
        glLightfv(GL_LIGHT0, GL_POSITION, [0,0,1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [1,1,1,1])        
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1,1,1,1])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, [50.0])        
        glShadeModel(GL_SMOOTH)
        glEnable(GL_CULL_FACE)
        if self.drag_start is None:
            self.rotation[1] = self.rotation[1] * 0.95
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_LIGHTING)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gluLookAt(0,0,-2.5,0,0,0,0,1,0)        
        self.frame_ctr += 1
       
        latitude = self.rotation[1]
        longitude = self.rotation[0]
        
        glRotatef(-90+latitude, 1, 0,0)
        glRotatef(longitude, 0, 0, 1)                
        self.sphere_renderer.render()
        glPopAttrib()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        

SPHERE_WIDTH = 2560
SPHERE_HEIGHT = 1600
SPHERE_SIZE = 1920 # estimated to compensate for the partial sphere coverage

def make_viewer(**kwargs):
    sim = False
    if "--test" in sys.argv:
        sim = True

    if sim:
        s = SphereViewer(sphere_resolution=1600, window_size=(800, 800), background='azworld.png', simulate=True, **kwargs)
        print("Simulating")
    else:
        s = SphereViewer(sphere_resolution=SPHERE_SIZE, window_size=(SPHERE_WIDTH,SPHERE_HEIGHT), background='azworld.png', simulate=False, **kwargs)
        print("Non-simulated")
    return s
        
if __name__=="__main__":    

    s = make_viewer()
    size = s.size
    
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, size, 0, size, -1, 500)
    glMatrixMode(GL_MODELVIEW)    
    glLoadIdentity()
    glEnable(GL_POINT_SMOOTH)
    glPointSize(10.0)
    glColor4f(1,0,0,1)
    
    def draw_fn():           
        glClearColor(1,1,1,1)
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glBegin(GL_POINTS)
        glVertex2f(512,100)
        glEnd()
        
    s.draw_fn = draw_fn
    s.start()
    
    
