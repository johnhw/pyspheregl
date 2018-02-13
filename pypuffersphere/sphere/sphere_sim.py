import numpy as np
import pyglet
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import time,sys,random,math,os

import timeit
wall_clock = timeit.default_timer

from pypuffersphere.utils import glskeleton,  gloffscreen, np_vbo, shader



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

                

    def __init__(self,size=1024,background=None,color=(1.0,1.0,1.0,1.0)):
       self.vertices,self.faces = gen_geosphere(6)       
       self.normals = self.compute_normals(self.vertices, self.faces)
       self.uv = self.compute_uv(self.vertices, self.faces)
       self.offscreen = gloffscreen.OffscreenRenderer(size,size)              
       self.size = size
       self.offscreen.begin_offscreen()    
       glClearColor(*color)
       glClear(GL_COLOR_BUFFER_BIT)         
       glLoadIdentity()    
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


quad_vert = """
#version 330 core

// These are sent to the fragment shader
out vec2 texCoord;      // UV coordinates of texture
out float alpha;        // Mask to remove out of circle texture
out float illumination; // brightness of point
out vec2 sphere;        // polar sphere coords
layout(location=0) in vec2 position;
uniform float rotate, tilt;

#define M_PI 3.1415926535897932384626433832795

vec2 az_to_polar(vec2 az)
{
    vec2 latlon;
    latlon.x = -sqrt((az.x*az.x)+(az.y*az.y)) * M_PI + M_PI/2;
    latlon.y = atan(az.y,az.x);
    return latlon;    
}

vec3 spherical_to_cartesian(vec2 latlon)
{
    // Convert a lat, lon co-ordinate to an a Cartesian x,y,z point on the unit sphere.
    vec3 cart;
    float lon, lat;
    lat = latlon.x;
    lon = latlon.y;
    lat += M_PI/2;
    float st = sin(lat);
    cart.x = cos(lon) * st;
    cart.y = sin(lon) * st;
    cart.z = -cos(lat);    
    return cart;
}   

// From https://gist.github.com/neilmendoza/4512992
mat4 rotationMatrix(vec3 axis, float angle)
{
    axis = normalize(axis);
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    
    return mat4(oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s,  oc * axis.z * axis.x + axis.y * s,  0.0,
                oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,           oc * axis.y * axis.z - axis.x * s,  0.0,
                oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s,  oc * axis.z * axis.z + c,           0.0,
                0.0,                                0.0,                                0.0,                                1.0);

                
}

void main()
{
    

    vec2 polar = az_to_polar(position);
    sphere = polar;
    polar.y -= rotate;
    
    
    vec4 pos = vec4(spherical_to_cartesian(polar),1);


    gl_Position.xy = position;
    gl_Position.z = 1;
    gl_Position.xzy = (rotationMatrix(vec3(1,0,0), tilt) * pos).xyz;


    // cut off all portions outside of the circle
    float radius = sqrt((position.x*position.x)+(position.y*position.y));
    alpha = 1.0-smoothstep(0.8,0.95, radius);
    // cutoff the rear of the sphere
    alpha *= smoothstep(0.0, 0.1, gl_Position.z);

    illumination = gl_Position.z;

    //if(gl_Position.z<0) alpha=0.0;
    gl_Position.w = 1;
    texCoord = position / 2.0 + 0.5;
}
"""

quad_frag = """
#version 330 core
#define M_PI 3.1415926535897932384626433832795


// from the vertex shader
in vec2 texCoord;
in vec2 sphere;
in float alpha, illumination;
uniform sampler2D quadTexture;

void main(void)
{          
     // look up the texture at the UV coordinates, with the given animation frame     
     vec4 tex_color = texture2D(quadTexture, texCoord);
     tex_color.rgb *= illumination;
     gl_FragColor = tex_color;

    float grid_space = 10;
    float grid_bright = 0.1;
    float ycoord = sphere.y * grid_space;
    float xcoord = sphere.x * grid_space;
    // Compute anti-aliased world-space grid lines
    float yline = abs(fract(ycoord - 0.5) - 0.5) / fwidth(ycoord);

    // Compute anti-aliased world-space grid lines
    float xline = abs(fract(xcoord - 0.5) - 0.5) / fwidth(xcoord);

    // Just visualize the grid lines directly
    gl_FragColor.rgb += grid_bright * (vec3(1.0 - min(xline, 1.0)) + vec3(1.0 - min(yline, 1.0)));
    
    gl_FragColor.a *= alpha;
     
     
}

"""
from pypuffersphere.utils.graphics_utils import make_unit_quad_tile

import os 

class SphereViewer:
    def make_quad(self):
        self.fbo = gloffscreen.FBOContext(self.size, self.size)
        self.quad_shader = shader.Shader(vert=[quad_vert], frag=[quad_frag])        
        n_subdiv = 64
        
        quad_indices, quad_verts, quad_texs = make_unit_quad_tile(n_subdiv)    

        qverts = np_vbo.VBuf(quad_verts, id=0)
        
        self.qverts = qverts
        self.qibo = np_vbo.create_elt_buffer(quad_indices)
        self.vao = np_vbo.create_vao([self.qverts])

        self.quad = shader.ShaderVBO(self.quad_shader, quad_indices, 
                                         buffers={"position":qverts},
                                         textures={"quadTexture":self.fbo.texture})

        


    def __init__(self, sphere_resolution=1024, window_size=(800,600), background=None, exit_fn=None, color=(1.0,1.0,1.0,1.0), simulate=True, auto_spin=False, draw_fn=None, tick_fn=None):
        self.simulate = simulate
        
        dir_path = os.path.dirname(os.path.realpath(__file__))        
        self.world_texture = pyglet.image.load(os.path.join(dir_path, ("../data/azworld.png")))
        
        self.size = sphere_resolution
        self.draw_fn = draw_fn
        self.exit_fn = exit_fn
        self.tick_fn = tick_fn
        self.auto_spin = auto_spin
        self.window_size = window_size

        

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
        self.make_quad()
        self.rotation = [0,0]
        self.last_rotation = [0,0]
        self.rotate_scale = -0.2        
        self.frame_ctr = 0
        self.drag_start = None                
        self.last_touch = wall_clock()
        self.spin = 0
        self.target_spin = 0

      
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
        if event=="press":        
            self.drag_start = (x,y)
            self.last_rotation = list(self.rotation)
            self.last_touch = wall_clock()
        if event=="drag":
            if self.drag_start is not None:
                new_pos = (x,y)
                self.rotation[0] = self.last_rotation[0] + (self.drag_start[0] - new_pos[0]) * self.rotate_scale
                self.rotation[1] = self.last_rotation[1] + (self.drag_start[1] - new_pos[1]) * self.rotate_scale * 0.5
                self.last_touch = wall_clock()
        if event=="release":
            self.drag_start = None
            self.last_touch = wall_clock()

            
    def key(self, event, symbol, modifiers):
        if symbol==pyglet.window.key.ESCAPE:            
            if self.exit_fn:
                self.exit_fn()
            pyglet.app.exit()
            sys.exit(0)
                        
    
    def tick(self):
        
        if self.tick_fn:
            self.tick_fn()
        
            
        if wall_clock()-self.last_touch>3 and self.auto_spin:
            self.target_spin = 0.2        
        else:
            self.target_spin = 0.0
        
        self.spin = 0.9 *self.spin + 0.1*self.target_spin    
        self.rotation[0] += self.spin

        if wall_clock()-self.last_touch>0.1:
            self.rotation[1] *= 0.95
        
    
                        
    def redraw(self):  
        
        
        glEnable(GL_BLEND)        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # clear the screen
        glClearColor(0.1, 0.1, 0.1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glViewport(0,0,self.window_size[0],self.window_size[1])

        with self.fbo as f:
            self.draw_fn()

        #glEnable(GL_DEPTH_TEST)
        
        self.quad.draw(n_prims=0, vars={"rotate":np.radians(self.rotation[0]), "tilt":float(np.radians(self.rotation[1]))})
        #glDisable(GL_DEPTH_TEST)
 
        return
       

   
        

SPHERE_WIDTH = 2560
SPHERE_HEIGHT = 1600
SPHERE_SIZE = 1920 # estimated to compensate for the partial sphere coverage

def make_viewer(**kwargs):
    sim = False
    if "--test" in sys.argv:
        sim = True
    
    if sim:
        s = SphereViewer(sphere_resolution=1600, window_size=(800, 800), background=None, simulate=True, **kwargs)
        print("Simulating")
    else:
        s = SphereViewer(sphere_resolution=1600, window_size=(800, 800), background=None, simulate=False, **kwargs)
        #s = SphereViewer(sphere_resolution=SPHERE_SIZE, window_size=(SPHERE_WIDTH,SPHERE_HEIGHT), background=None, simulate=False, **kwargs)
        print("Non-simulated")
    return s
        
if __name__=="__main__":    

    s = make_viewer()
    size = s.size
    
    def draw_fn():           
        glClearColor(1,0,1,1)        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
    s.draw_fn = draw_fn
    s.start()
    
    
