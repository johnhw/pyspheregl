import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *
import pygame,time,sys,random,math
import glskeleton, glutils, random
from collections import defaultdict
import gloffscreen
import sphere_sim
import sphere
import itertools
import time
#import sphere_cy
import argparse

# global state
target = 0
size = 0

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

    
def start_touch():
    touch_lib.init(ip="192.168.1.40", fseq=True)
    touch_lib.add_handler()
    touch_lib.start()
    
    
def spiral_targets(n=140):
    targets = spiral_layout(n)
    return targets
        
def iso_targets(k=2):
    vertices, edges = sphere_sim.gen_geosphere(k)       
    targets = [sphere.cartesian_to_spherical(v) for v in vertices]
    # exclude duplicate targets, and targets in bottom part of the sphere
    targets = list(set(targets))         
    targets = sorted(targets)
    return targets

def draw_polar(pts):
    for x,y in pts:
        x,y =  sphere.polar_to_display(x,y,size)
        glVertex2f(x,y)

def draw_all_targets(targets):
    for target in targets:
        lon, lat = target
        glColor4f(0.2,0.2,0.2,0.2)
        if lat>(np.pi/2-1e-4):
            lat = np.pi/2-1e-4        
        pts = sphere.spherical_circle((lon, lat), 0.01, n=12)                 
        glBegin(GL_LINE_LOOP)
        draw_polar(pts)
        glEnd()
            

        
def draw_targets(targets, target, active=False):
    lon, lat = targets[target]
    if active:
        glColor4f(0.9, 0.3, 0.3, 0.8)
    else:
        glColor4f(0.8, 0.5, 0.0, 0.2)               
    
    if lat>(np.pi/2-1e-4):
        lat = np.pi/2-1e-4
    
    pts = sphere.spherical_circle((lon, lat), 0.01, n=32)                 
    glBegin(GL_LINE_LOOP)
    draw_polar(pts)
    glEnd()


    for angle in [0,np.pi/2, np.pi,-np.pi/2]:
        r1 = sphere.spherical_radial((lon,lat), 1, angle)
        pts = sphere.spherical_line((lon,lat), r1)
        glColor4f(0.0,0.0,0.0,0.3)
        glBegin(GL_LINES)
        draw_polar(pts)
        glEnd()
    
    if active:
        glColor4f(0.2, 0.5, 0.9, 0.8)
        r = 0.0
    else:
        glColor4f(0.5, 0.5, 0.0, 0.1)               
        # add pulsing while there is no touch event
        r = np.sin(time.clock()*2)*0.02
    
    pts = sphere.spherical_circle((lon, lat), 0.2+r, n=32)                 
    glBegin(GL_LINE_LOOP)
    draw_polar(pts)
    glEnd()
    
    
    pts = sphere.spherical_circle((lon, lat), 0.8+r, n=32)                 
    glBegin(GL_LINE_LOOP)
    draw_polar(pts)
    glEnd()
        
def init_gl():
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
    



if __name__ == "__main__":
    s = sphere_sim.make_viewer()
    size = s.size        # resolution of the display
    print
    # parse the command line arguments    
    parser = argparse.ArgumentParser(description='Run a calibration sequence on the sphere.')
    parser.add_argument('--interleave', '-i', help="Run the repeats immediately after each other, rather than multiple complete runs.",  action='store_true', dest="interleave")
    parser.add_argument('--dummy', help="Ignore all input; just run through the targets and generate no output file.",  action='store_true', dest="dummy")
    parser.add_argument('--noprocess', help="Disable post-processing of the calibration file; just record the data. You can run process_calibration.py afterwards to process the calibration data.",  action='store_true', dest="noprocess")
    parser.add_argument('-n', "--ntargets", help="Total number of targets to run (default=100)", type=int, default=100)
    parser.add_argument('-r', "--repetitions", help="Number of repetitions per target (default=3)", type=int, default=3)
    parser.add_argument('-l', "--minlatitude", help="Minimum southern latitude to include, in degrees (default=40). 0=nothing below equator, 90=to pole", type=int, default=40)
    parser.add_argument('-t', "--touchtime", help="Touch time per target, in seconds (default=0.4)", type=float, default=0.4)
    parser.add_argument('--test', help="Run in sphere simulator mode", action='store_true')
    args = parser.parse_args()
    
    postprocess = not args.noprocess
    interleave = args.interleave
    n_targets = args.ntargets
    repetitions = args.repetitions
    min_latitude_degrees = args.minlatitude
    touch_time = args.touchtime
    min_latitude = -np.radians(min_latitude_degrees)
    dummy = args.dummy
    reps = repetitions        
    
    count = 0
    
    if not dummy:
        import touch_sphere as touch_lib
        # Start touch service
        start_touch()
    else:
        print "WARNING: Running in dummy mode. Touch input will be ignored; NO VALID CALBIRATION WILL BE GENERATED!"
        postprocess = False

    timename = time.asctime(time.localtime()).replace(" ","_").replace(":", "_")
    fname = "calibration_%s.csv" % timename
    with open(os.path.join("calibration", fname), 'w') as f:
        # CSV header
        f.write("id, target_lon, target_lat, tuio_x, tuio_y\n")
        
        targets = []
        nt = n_targets
        
        # adjust to the given number of targets given the latitude constraint
        while len(targets)<n_targets:
            targets = spiral_targets(nt)                                   
            targets = [t for t in targets if t[1]>min_latitude]   
            nt += n_targets-len(targets)
        
        print "%d unique targets; %d reps; %d touches total" % (len(targets), reps, len(targets)*reps)
        print "Touch time is %.2f seconds" % touch_time
        print "Not including targets below -%d degrees" % min_latitude_degrees
        unique_targets = targets
        if interleave:
            targets = [t for t in targets for i in range(reps)]
        else:
            targets = targets * reps
        touch_times = {}
        touch_pts = defaultdict(list)
        ignored_touches = set([-1])        
                
        def draw_fn():
            global target            
            init_gl()                     
            active = False
            
            if not dummy:                
                touches = touch_lib.get_touches()                           
            else:   
                # make fake touches to run through the targets
                tf = int(time.clock()*1.0)
                if tf<3:
                    tf = -1
                touches = {tf:(0.5, 0.5)}                
                
            
            for touch in touches:
                if touch not in ignored_touches:
                    if touch_times.has_key(touch):
                        active = True
                        ts = touch_times[touch]  
                        x, y = touches[touch]
                        touch_pts[touch].append((x,y))
                        if time.clock()-ts > touch_time:                                                                                   
                            # compute median touch position of x and y, ignoring first two samples (probably spurious)
                            med_x = np.median([pt[0] for pt in touch_pts[touch][2:]])
                            med_y = np.median([pt[1] for pt in touch_pts[touch][2:]]) 
                            #print "Stopped: ",touch, " at (%f, %f) %d touches" % (med_x, med_y, len(touch_pts[touch]))                            
                            print "Target %d/%d completed; %d trace points" % (target+1, len(targets), len(touch_pts[touch]))
                            f.write("%d, %f, %f, %f, %f\n" % (target, targets[target][0], targets[target][1], med_x, med_y))
                            ignored_touches.add(touch)
                            active = False
                            target = target+1
                    else:
                        touch_times[touch] = time.clock()
                        #print "Started: ",touch
            
            if target==0 and not active:
                draw_all_targets(unique_targets)  

            # print "Target:" , target , "Length:" , len(targets)                 
                             
            if target == len(targets):
                glClearColor(0,0,0,0)
                glClear(GL_COLOR_BUFFER_BIT)
                print "Completed calibration"
                f.close()
                if not dummy:
                    touch_lib.stop()
                if postprocess:
                    print "Beginning post-processing..."
                    import process_calibration
                    process_calibration.process_calibration(fname)                   
                sys.exit()
            draw_targets(targets, target, active)
        s.draw_fn = draw_fn
        s.start()
