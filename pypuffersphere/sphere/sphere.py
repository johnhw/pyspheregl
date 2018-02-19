from math import *
import numpy as np

def tuio_to_display(tuio_x, tuio_y, resolution=1200):
    """tuio_to_polar takes an x/y coordinate given in TUIO format (values 0 to 1)
    where x measures rotation around the equator and y represents to angle between
    the north and south poles
    
    Returns Cartesian co-ordinates (i.e. ready to draw onscreen). resolution
    specifies the pixel resolution of the display (must be square).
    """
    lon, lat = tuio_to_polar(tuio_x, tuio_y)
    display_x, display_y = polar_to_display(lon, lat, resolution)
    return display_x, display_y

def polar_to_tuio(lon, lat):
    """polar_to_tuio takes a long/lat pair, where long is a value between 0 and 2pi 
    (rotation around the equator) and lat as a value between -pi/2(south pole) and pi/2 (north pole)
    Returns corresponding tuio x,y co-ordinates
    """
    x = (lon % (2*np.pi)) / (2*np.pi)
    y = (lat + (np.pi/2)) / np.pi    
    return x, y

def az_to_polar(x, y):
    """Convert azimuthal x,y to polar co-ordinates"""
    lat = -np.sqrt((x**2)+(y**2)) * np.pi + np.pi/2
    lon = np.arctan2(y,x)
    return lon, lat
    
def polar_to_az(lon, lat):    
    """Convert polar to azimuthal x,y co-ordinates """
    r = (np.pi/2-lat)/np.pi          
    x,y = r * np.cos(lon), r*np.sin(lon)
    return x,y


def rawaz_to_polar(theta, r):
    """Convert azimuthal x,y to polar co-ordinates"""
    lat = -r * np.pi + np.pi/2
    lon = theta
    return lon, lat
    
def polar_to_rawaz(lon, lat):    
    """Convert polar to azimuthal x,y co-ordinates """
    r = (np.pi/2-lat)/np.pi              
    return lon, r
        
    
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
            
        phis.append(phi-np.pi/2)
        thetas.append(theta)        
    return list(zip(thetas, phis))
 
    
def tuio_to_polar(tuio_x, tuio_y):
    """tuio_to_polar takes an x/y coordinate given in TUIO format (values 0 to 1)
    where x measures rotation around the equator and y represents to angle between
    the north and south poles.  

    The returns these values as a long/lat pair, where long is a value between 0 and 2pi 
    (rotation around the equator) and lat as a value between -pi/2(south pole) and pi/2 (north pole)"""
    lon = tuio_x*2*pi
    lat = pi * tuio_y - (pi/2)
    return lon, lat

def polar_to_display(lon, lat, resolution=1200):
    """polar_to_display takes a lon,lat pair and returns an onscreen x,y co-ordinates
    in pixels.
    
    Returns Cartesian co-ordinates (i.e. ready to draw onscreen). resolution
    specifies the pixel resolution of the display (must be square).
    """

    r = (pi/2-lat)/pi  
    w = resolution/2
    x,y = w + r * w * cos(lon), w - r*w*sin(lon)
    return x,y
    
def polar_adjust_scale(lon, lat, s=1):    
    """Rescale lon, lat by contracting or expanding from the north pole. 
    This is necessary to compensate for the not quite complete coverage of the projection
    For the test PufferSphere, s=0.833 is a good compensation
    s sets the scaling factor. """
    r = (np.pi/2-lat)/np.pi          
    x,y = r * np.cos(lon)*s, r*np.sin(lon)*s    
    lat = -np.sqrt((x**2)+(y**2)) * np.pi + np.pi/2
    lon = np.arctan2(y,x)
    return lon, lat    

def spherical_distance(p1, p2):
    """Given two points p1, p2 (in radians), return
    the great circle distance between the two points."""
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
    lat1, lon1 = p1
    lat2, lon2 = p2    
    if cos(lat1)<1e-10:
        if lat>0:
            return pi
        else:
            return -pi        
    tc1=atan2(sin(lon1-lon2)*cos(lat2),
           cos(lat1)*sin(lat2)-sin(lat1)*cos(lat2)*cos(lon1-lon2))
    return tc1
    
def spherical_radial(p1, distance, radial):
     """Return a point distance units away from p1 (in radians) along the given
     radial (in radians)"""
     lon1, lat1 = p1
     d = distance
     tc = radial
     lat =asin(sin(lat1)*cos(d)+cos(lat1)*sin(d)*cos(tc))
     
     dlon=atan2(sin(tc)*sin(d)*cos(lat1),cos(d)-sin(lat1)*sin(lat))
     lon=((lon1-dlon +pi)%(2*pi) - pi)
     return lon, lat


     
def spherical_line(p1, p2, n=20):
    """Given two points p1, p2 (in radians), return a series of points 
    equispaced along the great circle connecting them. n specifies
    the number of points to use"""
    pts = []
    
    p1 = (-(p1[1]-pi), p1[0])
    p2 = (-(p2[1]-pi), p2[0])
    d = spherical_distance(p1, p2)
    # print d
    lat1, lon1 = p1
    lat2, lon2 = p2
    if d<=0:
        return []
    for i in range(n):
        f = i/float(n-1)
        A=sin((1-f)*d)/sin(d)
        B=sin(f*d)/sin(d)
        x = A*cos(lat1)*cos(lon1) +  B*cos(lat2)*cos(lon2)
        y = A*cos(lat1)*sin(lon1) +  B*cos(lat2)*sin(lon2)
        z = A*sin(lat1)           +  B*sin(lat2)
        lat=atan2(z,sqrt(x**2+y**2))
        lon=atan2(y,x)
        # print lat, lon
        pts.append((lon, -(lat-pi)))
        
    return pts

# import transformations

# def spherical_flat_circle(pt, rad, n=20):
    # """Given a point p1 (in radians), return a series of points 
    # equispaced along a circle around that point, tangent to a unit
    # sphere surface. The points are returned in Cartesian space,
    # along with a set of normals which point outwards along
    # the sphere centre vector.
    # rad specifies the radius.
    # n specifies the number of points to use. """    
    # centre = spherical_to_cartesian(pt)
    # rotate = transformations.rotation_matrix(2*np.pi/n,centre)[:3,:3]    
    # pt = np.cross(np.array(centre), np.array([0,0,1]))
    # pt = pt/np.linalg.norm(pt)
    # pt = (pt-centre)*rad + centre
    # pts = []
    # norms = []
    # for i in range(n):                
        # pt = np.dot(pt, rotate)
        # pts.append(pt)
        # norms.append(np.array(centre))
    # return pts, norms

def spherical_circle(p1, rad, n=20):
    """Given a point p1 (in radians), return a series of points 
    equispaced along a circle around that point. n specifies the number of 
    points to use. """
    pts = []    
    for i in range(n):
        f = i/float(n)
        lon,lat = p1
        lon, lat = spherical_radial((lon,lat), rad, f*2*pi)
        pts.append((lon,lat))
    return pts

def spherical_arc(p1, radius, arc_1, arc_2, n=20):
    """Given a point p1 (in radians), return a series of points 
    equispaced along an arc around that point. n specifies the number of 
    points to use. """
    pts = []    

    # Determine where n number of points will fall
    start=arc_1
    end = arc_2
    if arc_1 > arc_2:
        start,end = end,start 

    angle = end - start
    increment = angle/float(n)
    while start < end:
        lon,lat = p1
        lon, lat = spherical_radial((lon,lat), radius, start)
        pts.append((lon,lat))
        start += increment
    return pts
    
    
def spherical_midpoint(p1, p2):
    """Return the midpoint of p1, p2, in lot, lat format"""
    p1 = (-(p1[1]-pi), p1[0])
    p2 = (-(p2[1]-pi), p2[0])
    d = spherical_distance(p1, p2)
    lat1, lon1 = p1
    lat2, lon2 = p2
    if d<=0:
        return None
    f = 0.5
    A=sin((1-f)*d)/sin(d)
    B=sin(f*d)/sin(d)
    x = A*cos(lat1)*cos(lon1) +  B*cos(lat2)*cos(lon2)
    y = A*cos(lat1)*sin(lon1) +  B*cos(lat2)*sin(lon2)
    z = A*sin(lat1)           +  B*sin(lat2)
    lat=atan2(z,sqrt(x**2+y**2))
    lon=atan2(y,x)    
    return (lon, -(lat-pi))
        
    


def subdivide_spherical_triangles(vertices, faces, uv=None):
    # should also generate UV co-ordinates...
    newfaces = []
    vertices = list(vertices)
    def midpoint(p1, p2):
        return ((p1[0]+p2[0])/2,(p1[1]+p2[1])/2)
        
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
        vindex2 = len(vertices)+1
        vindex3 = len(vertices)+2
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
        vindex2 = len(vertices)+1
        vindex3 = len(vertices)+2
        vindex4 = len(vertices)+3
        vindex5 = len(vertices)+4
        vertices += [v1,v2,v3,v4,v7]
        
        # new face
        newfaces.append((face[0], vindex1, vindex5, vindex4))        
        newfaces.append((vindex1, face[1], vindex2, vindex5))        
        newfaces.append((vindex5, vindex2, face[2], vindex3))        
        newfaces.append((vindex4, vindex5, vindex3, face[3]))        
    
    return vertices, newfaces, uv
    
def spherical_triangle(pts,uv=None,iter=2):
    """Return a triangle mesh for the triangle given by pts (in (lon,lat) pair form).
    Triangle is subdivied iter times; don't use more than 3 or 4!
    """
    vertices = pts
    faces = [[0,1,2]]
    for i in range(iter):
        vertices, faces,uv = subdivide_spherical_triangles(vertices, faces, uv)
    return vertices, faces, uv
   

def spherical_quad(pts, iter=2, uv=None, **kwargs):
    """Return a quad mesh for the quadrilateral given by pts (in (lon,lat) pair form).
    Triangle is subdivied iter times; don't use more than 3 or 4!
    """    
    vertices = pts
    faces = [[0,1,2,3]]    
    for i in range(iter):
        vertices, faces, uv = subdivide_spherical_quads(vertices, faces, uv)
    return vertices, faces, uv
   
   
import numpy as np

def spherical_to_cartesian(pt):
    """Convert a lon, lat co-ordinate to an a Cartesian x,y,z point on the unit sphere."""
    lon, lat = pt 
    lat += np.pi/2
    st = np.sin(lat)
    x = np.cos(lon) * st
    y = np.sin(lon) * st
    z = np.cos(lat)
    
    return x,y,z

def polar_to_cart(lon, lat):
    lat += np.pi/2
    st = np.sin(lat)
    
    x = np.cos(lon) * st
    y = np.sin(lon) * st
    z = np.cos(lat)
    
    return x,y,z

    
def cartesian_to_spherical(pt):
    """Convert a Cartesian 3D point to lon, lat co-ordinates of the projection
    onto the unit sphere."""
    pt = np.array(pt)
    n = np.sqrt(pt.dot(pt)) 
    pt = pt / n       
    lat = np.arccos(pt[2]) - np.pi/2
    lon = np.arctan2(pt[1], pt[0])
    return lon, lat

def cart_to_polar(x,y,z):
    return cartesian_to_spherical([x,y,z])
    
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
    
   
def spherical_rectangle(centre, width, height, up, x_ratio=1, y_ratio=1, **kwargs):
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
    up, right, forward = tangent_coord_system(orig, upv)
     
    # create rectangle
    p1 = orig - right*width - up*height
    p2 = orig + right*width - up*height
    p3 = orig + right*width + up*height
    p4 = orig - right*width + up*height
    
    # project onto sphere and convert to spherical
    pts = [cartesian_to_spherical(p) for p in [p1,p2,p3,p4]]
    
    
    uv = [[0.0,0.0], [x_ratio,0.0], [x_ratio,y_ratio], [0.0,y_ratio]]
    return spherical_quad(pts, uv=uv, **kwargs)
    
     
