import numpy as np
import time,sys
from pyglet.gl import *
import pyglet
from collections import defaultdict
from pypuffersphere.sphere import sphere_sim, sphere
import random
import itertools
import time
import os
from pypuffersphere.utils.np_vbo import IBuf, VBuf
from pypuffersphere.utils.shader import shader_from_file, ShaderVBO
import timeit
# high precision timing
wall_clock = timeit.default_timer

import argparse




class SphereCalibration:
    def __init__(self):            
        
        parser = argparse.ArgumentParser(description='Run a calibration sequence on the sphere.')
        #parser.add_argument('--interleave', '-i', help="Run the repeats immediately after each other, rather than multiple complete runs.",  action='store_true', dest="interleave")
        parser.add_argument('--dummy', help="Ignore all input; just run through the targets and generate no output file.",  action='store_true', dest="dummy")
        parser.add_argument('--noprocess', help="Disable post-processing of the calibration file; just record the data. You can run process_calibration.py afterwards to process the calibration data.",  action='store_true', dest="noprocess")
        parser.add_argument('-n', "--ntargets", help="Total number of targets to run (default=100)", type=int, default=100)
        parser.add_argument('-r', "--repetitions", help="Number of repetitions per target (default=3)", type=int, default=3)
        parser.add_argument('-l', "--minlatitude", help="Minimum southern latitude to include, in degrees (default=40). 0=nothing below equator, 90=to pole", type=int, default=40)
        parser.add_argument('-t', "--touchtime", help="Touch time per target, in seconds (default=0.4)", type=float, default=0.4)
        parser.add_argument('--test', help="Run in sphere simulator mode", action='store_true')
        args = parser.parse_args()
        
        self.postprocess = not args.noprocess
        self.interleave = True # args.interleave
        self.n_targets = args.ntargets
        self.repetitions = args.repetitions
        self.min_latitude_degrees = args.minlatitude
        self.touch_time = args.touchtime
        self.min_latitude = -np.radians(self.min_latitude_degrees)
        self.dummy = args.dummy
        reps = self.repetitions        

        if self.dummy:        
            print("WARNING: Running in dummy mode. Touch input will be ignored; NO VALID CALBIRATION WILL BE GENERATED!")
            self.postprocess = False
        self.target = 0

        self.targets = []
        nt = self.n_targets
        
        # adjust to the given number of targets given the latitude constraint
        while len(self.targets)<self.n_targets:
            self.targets = sphere.spiral_layout(nt)                                   
            self.targets = [t for t in self.targets if t[1]>self.min_latitude]   
            nt += self.n_targets-len(self.targets)

        self.n_targets = len(self.targets)
        
        
        print("%d unique targets; %d reps; %d touches total" % (len(self.targets), reps, len(self.targets)*reps))
        print("Touch time is %.2f seconds" % self.touch_time)
        print("Not including targets below -%d degrees" % self.min_latitude_degrees)

        self.unique_targets = self.targets
        if self.interleave:
            self.targets = [t for t in self.targets for i in range(reps)]
        else:
            self.targets = self.targets * reps


        self.touch_times = {}
        self.touch_pts = defaultdict(list)
        self.ignored_touches = set([-1])        

        self.sim = sphere_sim.make_viewer(draw_fn=self.draw, tick_fn=self.tick, touch_fn=self.touch)     
        self.size = self.sim.size
        self.target_data = [] 
        self.create_geometry()
        self.rep = 0
        ######
        self.sim.start()

    def create_geometry(self):
        
        target_array = np.array(([[0,0]]*4)+self.targets, dtype=np.float32)     
        
        point_shader = shader_from_file([sphere_sim.getshader("sphere.vert"), sphere_sim.getshader("calibration_point.vert")],         
                                        [sphere_sim.getshader("calibration_point.frag")])  
        self.target_render = ShaderVBO(point_shader, IBuf(np.arange(len(target_array))), 
                                        buffers={"position":VBuf(target_array)},                                        
                                        vars = {"target":self.target, "selected_color":[0.9, 0.9, 0.2]},
                                        primitives=GL_POINTS)                                        
                    

    def advance_target(self):
        self.target += 1
        self.rep += 1
        self.rep = self.rep % self.repetitions
        # check if we are done
        if self.target==self.n_targets:
            self.write_output()
            self.sim.exit()        

    def add_touch(self, t_id, lon, lat, x, y):
        self.target_data.append((t_id, lon, lat, x, y))

    def draw(self):
        glClearColor(0.1,0.1,0.1,1)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_POINT_SPRITE)
        glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)        
        self.target_render.draw(vars={"target":self.target+4, "t":wall_clock(), "rep":self.rep})

    def register_touch(self, id):
        pts = self.touch_pts[id]
        # must have enough points to register
        if len(pts)>5:
            med_pt = np.median(self.touch_pts[id][2:-2], axis=0)                                     
            lon, lat = self.targets[self.target]
            self.add_touch(self.target, lon, lat, med_pt[0], med_pt[1])
            self.advance_target()


    def touch(self, events):
        for event in events:
            touch = event.touch            
            # store raw events
            if event.event=="DRAG" or event.event=="DOWN":                                                                
                self.touch_pts[touch.id].append(touch.raw)
            if event.event=="UP":
                # touch went up; accept if at least 
                # touch_time long
                if touch.duration>self.touch_time:
                    self.register_touch(touch.id)

    def tick(self):
        if self.target == self.n_targets:
            # complete; write the output and exit
            self.write_output()
            self.sim.exit()

    def write_output(self):
        timename = time.asctime(time.localtime()).replace(" ","_").replace(":", "_")
        try:
            os.mkdir("calibration")
        except OSError:
            print("Calibration directory already exists")

        fname = "calibration_%s.csv" % timename
        with open(fname) as f:
            f.write("id, target_lon, target_lat, tuio_x, tuio_y\n")
            for id, lon, lat, x, y in self.target_data:
                f.write("%d, %f, %f, %f, %f" % (id, lon, lat, x, y))
        if self.postprocess:
                print("Beginning post-processing...")
                import pypuffersphere.calibration.process_calibration as process_calibration
                process_calibration.process_calibration(fname)    
    

 
        
    



if __name__ == "__main__":
    
    s = SphereCalibration()
    

    print
    # parse the command line arguments    
    
    
    count = 0
    
   


    
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
                
            touches = touches[0]
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
                
                if postprocess:
                    print "Beginning post-processing..."
                    import process_calibration
                    process_calibration.process_calibration(fname)                   
                sys.exit()
            draw_targets(targets, target, active)
        
        s.start()
