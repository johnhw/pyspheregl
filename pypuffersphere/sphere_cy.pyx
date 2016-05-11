from __future__ import division

import numpy as np
cimport numpy as np
DTYPE = np.float64
ctypedef np.float64_t DTYPE_t
cimport cython

from libc.math cimport sin, cos, acos, exp, sqrt, fabs, M_PI, asin, atan2
cdef double pi = M_PI


def tuio_to_display(double tuio_x, double tuio_y, double resolution=1200):
    """tuio_to_polar takes an x/y coordinate given in TUIO format (values 0 to 1)
    where x measures rotation around the equator and y represents to angle between
    the north and south poles
    
    Returns Cartesian co-ordinates (i.e. ready to draw onscreen). resolution
    specifies the pixel resolution of the display (must be square).
    """
    cdef double lon, lat
    cdef int display_x, display_y
    lon, lat = tuio_to_polar(tuio_x, tuio_y)
    display_x, display_y = polar_to_display(lon, lat, resolution)
    return display_x, display_y


def tuio_to_polar(double tuio_x, double tuio_y):
    """tuio_to_polar takes an x/y coordinate given in TUIO format (values 0 to 1)
    where x measures rotation around the equator and y represents to angle between
    the north and south poles.  

    The returns these values as a long/lat pair, where long is a value between 0 and 2pi 
    (rotation around the equator) and lat as a value between -pi/2(south pole) and pi/2 (north pole)"""
    cdef lon, lat
    lon = tuio_x*2*pi
    lat = pi * tuio_y - (pi/2)
    return lon, lat
    
    
def az_to_polar(double x, double y):
    """Convert azimuthal x,y to polar co-ordinates"""
    cdef double lat, lon
    lat = -sqrt((x*x)+(y*y)) * pi + pi/2
    lon = atan2(y,x)
    return lon, lat
    
        
def polar_to_az(double lon, double lat):    
    """Convert polar to azimuthal x,y co-ordinates """
    cdef double r,x,y
    r = (pi/2-lat)/pi          
    x,y = r * cos(lon), r*sin(lon)
    return x,y    

def polar_to_display(double lon, double lat, double resolution=1200):
    """polar_to_display takes a lon,lat pair and returns an onscreen x,y co-ordinates
    in pixels.
    
    Returns Cartesian co-ordinates (i.e. ready to draw onscreen). resolution
    specifies the pixel resolution of the display (must be square).
    """
    cdef double r, w, x, y
    r = (pi/2-lat)/pi  
    w = resolution/2
    x,y = w + r * w * cos(lon), w - r*w*sin(lon)
    return x,y

def spherical_distance(p1, p2):
    """Given two points p1, p2 (in radians), return
    the great circle distance between the two points."""
    cdef double lat1, lon1, lat, lon2, a, c
    lat1, lon1 = p1
    lat2, lon2 = p2
    dlat = lat2-lat1
    dlon = lon2-lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2*atan2(sqrt(a), sqrt(1-a))    
    return c

# return initial heading between two points
def spherical_course(p1, p2):
    """Return the initial heading from point p1 (in radians) to point p2 (in radians)."""   
    cdef double lat1, lon1, lat2, lon2, tcl
    lat1, lon1 = p1
    lat2, lon2 = p2    
    if cos(lat1)<1e-10:
        if lat1>0:
            return pi
        else:
            return -pi        
    tc1=atan2(sin(lon1-lon2)*cos(lat2),
           cos(lat1)*sin(lat2)-sin(lat1)*cos(lat2)*cos(lon1-lon2))
    return tc1
    
def spherical_radial(p1, double distance, double radial):
     """Return a point distance units away from p1 (in radians) along the given
     radial (in radians)"""
     cdef double lon1, lat1, d, tc, lat, dlon, lon
     lon1, lat1 = p1
     d = distance
     tc = radial
     lat =asin(sin(lat1)*cos(d)+cos(lat1)*sin(d)*cos(tc))
     
     dlon=atan2(sin(tc)*sin(d)*cos(lat1),cos(d)-sin(lat1)*sin(lat))
     lon=((lon1-dlon +pi)%(2*pi) - pi)
     return lon, lat
     


cdef c_spherical_radial(double lon1, double lat1, double distance, double radial):
     """Return a point distance units away from p1 (in radians) along the given
     radial (in radians)"""
     cdef double  d, tc, lat, dlon, lon     
     d = distance
     tc = radial
     lat =asin(sin(lat1)*cos(d)+cos(lat1)*sin(d)*cos(tc))     
     dlon=atan2(sin(tc)*sin(d)*cos(lat1),cos(d)-sin(lat1)*sin(lat))
     lon=((lon1-dlon +pi)%(2*pi) - pi)
     return lon, lat     
     
def spherical_line(p1, p2, int n=20):
    """Given two points p1, p2 (in radians), return a series of points 
    equispaced along the great circle connecting them. n specifies
    the number of points to use"""
    pts = []
    cdef double d, lat1, lon1, lat2, lon2
    p1 = (-(p1[1]-pi), p1[0])
    p2 = (-(p2[1]-pi), p2[0])
    d = spherical_distance(p1, p2)
    # print d
    lat1, lon1 = p1
    lat2, lon2 = p2
    if d<=0:
        return []
        
    cdef double f, A, B, x, y, z, lat, lon
    cdef int i
    for i in range(n):
        f = i/float(n-1)
        A=sin((1-f)*d)/sin(d)
        B=sin(f*d)/sin(d)
        x = A*cos(lat1)*cos(lon1) +  B*cos(lat2)*cos(lon2)
        y = A*cos(lat1)*sin(lon1) +  B*cos(lat2)*sin(lon2)
        z = A*sin(lat1)           +  B*sin(lat2)
        lat=atan2(z,sqrt(x**2+y**2))
        lon=atan2(y,x)        
        pts.append((lon, -(lat-pi)))        
    return pts

def spherical_circle(p1, double rad, int n=20):
    """Given a point p1 (in radians), return a series of points 
    equispaced along a circle around that point. n specifies the number of 
    points to use. """
    pts = []    
    cdef int i
    cdef double f, lon, lat
    for i in range(n):
        f = i/float(n)
        lon,lat = p1
        lon, lat = c_spherical_radial(lon,lat, rad, f*2*pi)
        pts.append((lon,lat))
    return pts

def spherical_arc(p1, double radius, double arc_1, double arc_2, int n=20):
    """Given a point p1 (in radians), return a series of points 
    equispaced along an arc around that point. n specifies the number of 
    points to use. """
    pts = []    
    cdef double start, end, angle, increment, lon, lat, lon1, lat1
    # Determine where n number of points will fall
    start=arc_1
    end = arc_2
    if arc_1 > arc_2:
        start,end = end,start 

    angle = end - start
    increment = angle/float(n)
    lon,lat = p1
    while start < end:        
        lon1, lat1 = c_spherical_radial(lon, lat, radius, start)
        pts.append((lon1,lat1))
        start += increment
    return pts
    
    
def spherical_midpoint(p1, p2):
    """Return the midpoint of p1, p2, in lot, lat format"""
    p1 = (-(p1[1]-pi), p1[0])
    p2 = (-(p2[1]-pi), p2[0])
    cdef d, lon1, lat1, lon2, lat2
    d = spherical_distance(p1, p2)
    lat1, lon1 = p1
    lat2, lon2 = p2
    if d<=0:
        return None
        
    cdef f, A, B, x, y, z, lat, lon
    f = 0.5
    A=sin((1-f)*d)/sin(d)
    B=sin(f*d)/sin(d)
    x = A*cos(lat1)*cos(lon1) +  B*cos(lat2)*cos(lon2)
    y = A*cos(lat1)*sin(lon1) +  B*cos(lat2)*sin(lon2)
    z = A*sin(lat1)           +  B*sin(lat2)
    lat=atan2(z,sqrt(x**2+y**2))
    lon=atan2(y,x)    
    return (lon, -(lat-pi))
        
def spherical_to_cartesian(pt):
    """Convert a lat, lon co-ordinate to an a Cartesian x,y,z point on the unit sphere."""
    cdef double lon, lat, st, x, y, z
    lon, lat = pt 
    lat += pi/2
    st = sin(lat)
    x = cos(lon) * st
    y = sin(lon) * st
    z = cos(lat)
    return x,y,z
    
    
def cartesian_to_spherical(pt):
    """Convert a Cartesian 3D point to lon, lat co-ordinates of the projection
    onto the unit sphere."""
    cdef double n, lon, lat    
    n = sqrt(pt[0]**2+ pt[1]**2+pt[2]**2)    
    lat = acos(pt[2]/n) - pi/2
    lon = atan2(pt[1]/n, pt[0]/n) 
    return lon, lat
    
def tangent_coord_system(origin, up_point):
    """Given a pair of points in Cartesian co-ordinates on a unit sphere,
    return three vectors representing an orthogonal co-ordinate system,
    which touches the sphere at origin, and has an up vector pointing towards
    the projection of up_point out from the sphere onto the tangent plane 
    which touches origin. """
    v = origin - up_point
    
    normal = origin / np.sqrt(origin.dot(origin))
    d = np.dot(up_point, origin)    
    proj = up_point - d*normal        
    # form the co-ordinate system via the cross product
    up = proj / np.sqrt(proj.dot(proj))    
    forward = normal
    right = np.cross(up, forward)
    return up, right, forward
    


def subdivide_spherical_triangles(vertices, faces, uv=None):
    # should also generate UV co-ordinates...
    newfaces = []
    vertices = list(vertices)
    def midpoint(p1, p2):
        return ((p1[0]+p2[0])/2,(p1[1]+p2[1])/2)
    cdef int vindex1, vindex2, vindex3
    
    for face in faces:        
        v1 = spherical_midpoint(vertices[face[0]],vertices[face[1]])
        v2 = spherical_midpoint(vertices[face[1]],vertices[face[2]])
        v3 = spherical_midpoint(vertices[face[2]],vertices[face[0]])        
        
        if uv:
            uv1 = midpoint(uv[face[0]], uv[face[1]])
            uv2 = midpoint(uv[face[1]], uv[face[2]])
            uv3 = midpoint(uv[face[2]], uv[face[0]])
            uv += [uv1,uv2,uv3]
            
        
        vindex1 = len(vertices)
        vindex2 = vindex1+1
        vindex3 = vindex1+2
        vertices += [v1,v2,v3]
        
        # new face
        newfaces.append((vindex3, vindex1, vindex2))        
        newfaces.append((vindex3, face[0], vindex1))
        newfaces.append((vindex2, vindex1, face[1]))
        newfaces.append((face[2],vindex3,  vindex2))
    return vertices, newfaces, uv
    
def subdivide_spherical_quads(vertices, faces, uv=None):
    # should also generate UV co-ordinates...
    newfaces = []
    vertices = list(vertices)
    def midpoint(p1, p2):
        return ((p1[0]+p2[0])/2,(p1[1]+p2[1])/2)
        
    cdef int vindex1, vindex2, vindex3, vindex5
    
    for face in faces:        
        v1 = spherical_midpoint(vertices[face[0]],vertices[face[1]])
        v2 = spherical_midpoint(vertices[face[1]],vertices[face[2]])
        v3 = spherical_midpoint(vertices[face[2]],vertices[face[3]])        
        v4 = spherical_midpoint(vertices[face[3]],vertices[face[0]])        
        v7 = spherical_midpoint(v2,v4)
        
        if uv:            
            uv1 = midpoint(uv[face[0]], uv[face[1]])
            uv2 = midpoint(uv[face[1]], uv[face[2]])
            uv3 = midpoint(uv[face[2]], uv[face[3]])
            uv4 = midpoint(uv[face[3]], uv[face[0]])            
            uv5 = midpoint(uv4, uv2)
            uv += [uv1,uv2,uv3, uv4, uv5]
            
        
        vindex1 = len(vertices)
        vindex2 = vindex1+1
        vindex3 = vindex1+2
        vindex4 = vindex1+3
        vindex5 = vindex1+4
        vertices += [v1,v2,v3,v4,v7]
        
        # new face
        newfaces.append((face[0], vindex1, vindex5, vindex4))        
        newfaces.append((vindex1, face[1], vindex2, vindex5))        
        newfaces.append((vindex5, vindex2, face[2], vindex3))        
        newfaces.append((vindex4, vindex5, vindex3, face[3]))        
    
    return vertices, newfaces, uv
    
def spherical_triangle(pts,uv=None, int iter=2):
    """Return a triangle mesh for the triangle given by pts (in (lon,lat) pair form).
    Triangle is subdivied iter times; don't use more than 3 or 4!
    """
    vertices = pts
    faces = [[0,1,2]]
    for i in range(iter):
        vertices, faces,uv = subdivide_spherical_triangles(vertices, faces, uv)
    return vertices, faces, uv
   

def spherical_quad(pts, int iter=2, uv=None, **kwargs):
    """Return a quad mesh for the quadrilateral given by pts (in (lon,lat) pair form).
    Triangle is subdivied iter times; don't use more than 3 or 4!
    """    
    vertices = pts
    faces = [[0,1,2,3]]
    for i in range(iter):
        vertices, faces, uv = subdivide_spherical_quads(vertices, faces, uv)
    return vertices, faces, uv
   

cdef c_tangent_coord_system(np.ndarray[DTYPE_t, ndim=1] origin, np.ndarray[DTYPE_t, ndim=1] up_point):
    """Given a pair of points in Cartesian co-ordinates on a unit sphere,
    return three vectors representing an orthogonal co-ordinate system,
    which touches the sphere at origin, and has an up vector pointing towards
    the projection of up_point out from the sphere onto the tangent plane 
    which touches origin. """    
    cdef np.ndarray[DTYPE_t, ndim=1] v, normal, proj, up, forward, right
    cdef double d
    
    v = origin - up_point    
    normal = origin / sqrt(origin.dot(origin))
    d = np.dot(up_point, origin)    
    proj = up_point - d*normal        
    # form the co-ordinate system via the cross product
    up = proj / np.sqrt(proj.dot(proj))    
    forward = normal
    right = np.cross(up, forward)
    return up, right, forward    
   
def spherical_rectangle(centre, double width, double height, up, double x_ratio=1, double y_ratio=1, **kwargs):
    """
    Return a spherical rectangle given by rect and up vector.
    lat, lon give the centre of the rectangle
    w, h give the width and height of the rectangle in cartesian units
    up_lat, up_lon, give the direction of the up vector of the rectangle 
    
    Drawing procedes as follows:
    Position is converted to Cartesian co-ordinates on the sphere's surface
    Up vector is converted to Cartesian co-ordinates on the sphere's surface
    Up vector is projected onto tangent plane by shooting a ray from the up point to the tangent plane
    Right vector is produced from the cross product of the up vector and the normal vector
    Rectangle is drawn on tangent plane using up and right vector
    Rectangle is projected onto sphere by normalising the co-ordinates
    Cartesian rectangle co-ordinates are converted back to spherical co-ordinates
    
    All other arguments are passed directly onto spherical_quad, which
    forms the great circle sections to make up the square patch.    
    """
    
    # convert to cartesian
    orig = np.array(spherical_to_cartesian(centre))
    upv = np.array(spherical_to_cartesian(up))
    
    # form co-ordinate system
    up, right, forward = c_tangent_coord_system(orig, upv)
        
    # create rectangle
    p1 = orig - right*width - up*height
    p2 = orig + right*width - up*height
    p3 = orig + right*width + up*height
    p4 = orig - right*width + up*height
    
    # project onto sphere and convert to spherical
    pts = [cartesian_to_spherical(p) for p in [p1,p2,p3,p4]]
    
    
    uv = [[0.0,0.0], [x_ratio,0.0], [x_ratio,y_ratio], [0.0,y_ratio]]
    return spherical_quad(pts, uv=uv, **kwargs)
    
     
# tests
# distance measure
# line pointing at second finger
# orbit around finger
# line between two fingers