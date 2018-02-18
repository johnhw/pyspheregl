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
        parser.add_argument('-n', "--ntargets", help="Total number of targets to run (default=100)", type=int, default=300)
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
        
        self.ready_for_touch = True        
        ######
        self.sim.start()

    def create_geometry(self):            
        target_array = np.array(self.targets, dtype=np.float32)     
        
        point_shader = shader_from_file([sphere_sim.getshader("sphere.vert"), sphere_sim.getshader("calibration_point.vert")],         
                                        [sphere_sim.getshader("calibration_point.frag")])  

        self.target_render = ShaderVBO(point_shader, IBuf(np.arange(len(target_array))), 
                                        buffers={"position":VBuf(target_array)},                                        
                                        vars = {"target":self.target, "selected_color":[0.2, 0.9, 0.9]},
                                        primitives=GL_POINTS)                                        
                    

    def advance_target(self):
        self.target += 1
        # check if we are done        
        if self.target==len(self.targets):
            self.write_output()
            self.sim.exit()        
             

    def draw(self):
        glClearColor(0.1,0.1,0.1,1)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_POINT_SPRITE)
        glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)        
        
        if self.ready_for_touch:
            self.target_render.draw(vars={"target":self.target, "t":wall_clock()})
        else:
            self.target_render.draw(vars={"target":-1, "t":0})

    def register_touch(self, id):
        pts = self.touch_pts[id]
        # must have enough points to register
        if len(pts)>5:
            med_pt = np.median(self.touch_pts[id][2:-2], axis=0)                                     
            lon, lat = self.targets[self.target]
            self.target_data.append((self.target, lon, lat, med_pt[0], med_pt[1]))
            self.advance_target()            
            self.ready_for_touch = False
            

    def touch(self, events):
        for event in events:
            touch = event.touch            
            # check if we are waiting for a touch
            if self.ready_for_touch:
                if event.event=="DRAG" or event.event=="DOWN":                                                                                
                    # store raw events
                    self.touch_pts[touch.id].append(touch.raw)
                    if touch.duration>self.touch_time:                    
                        self.register_touch(touch.id)

            if event.event=="UP":                
                self.ready_for_touch = True
                
                

    def tick(self):
        pass

    def write_output(self):
        timename = time.asctime(time.localtime()).replace(" ","_").replace(":", "_")
        try:
            os.mkdir("calibration")
        except OSError:
            print("Calibration directory already exists")

        fname = "calibration_%s.csv" % timename
        with open(os.path.join("calibration", fname), "w") as f:
            f.write("id, target_lon, target_lat, tuio_x, tuio_y\n")
            for id, lon, lat, x, y in self.target_data:
                f.write("%d, %f, %f, %f, %f\n" % (id, lon, lat, x, y))
        if self.postprocess:
                print("Beginning post-processing...")
                import pypuffersphere.calibration.process_calibration as process_calibration
                process_calibration.process_calibration(fname)    
    

 
        
    



if __name__ == "__main__":    
    s = SphereCalibration()

