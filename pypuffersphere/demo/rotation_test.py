import numpy as np
import pyglet
from pyglet.gl import *

# sphere stuff
from pypuffersphere.sim.sphere_sim import getshader, resource_file
import pypuffersphere.sim.sphere_sim as sphere_sim
import pypuffersphere.sphere.sphere as sphere
from pypuffersphere.utils.shader import ShaderVBO, shader_from_file

import time
from pypuffersphere.utils.np_vbo import VBuf, IBuf
from pypuffersphere.utils.graphics_utils import make_unit_quad_tile
import pypuffersphere.utils.transformations as tn
from pypuffersphere.utils.graphics_utils import wall_clock

EQUATORIAL = 1  # rotate around z axis only
FREEBALL = 2    # rotate around any axis at all

class Finger:    
    def __init__(self, last_xyz, last_t):
        self.last_xyz = np.array(last_xyz)
        self.last_t = last_t
        self.last_velocities = []

    def update_velocity(self, xyz, t):
        dt = t - self.last_t
        xyz = np.array(xyz)
        dxyz = xyz - self.last_xyz
        velocity = dxyz / dt
        self.last_xyz = xyz
        self.last_t = t
        self.last_velocities.append(velocity)
        if len(self.last_velocities)>5:
            self.last_velocities.pop(0)
        return dt, np.median(self.last_velocities, axis=0)

class RotationHandler(object):
    def __init__(self, mode=FREEBALL, gain=1.0, base_damping=0.999, finger_damping=0.95):
        self.mode = mode
        self.orientation = np.array([0,0,0,1], dtype=np.float64)
        self.angular_velocity = np.array([0,0,0,0.0], dtype=np.float64)
        self.base_damping = base_damping
        self.finger_damping = finger_damping
        self.gain = gain
        self.fingers = {}
        self.unnormalised_orientation = np.array(self.orientation)

    def update(self):
        self.orientation = tn.unit_vector(self.orientation)

        # force rotations to around equator only
        if self.mode==EQUATORIAL:
            self.angular_velocity[2:] = 0

        spin = tn.quaternion_multiply(self.angular_velocity, self.orientation)
        self.orientation += (1/24.0) * spin * self.gain       

        # unnormalised accumulation of the rotations
        # normalised form is still used for intermediate computations
        self.unnormalised_orientation +=  0.25 * spin * self.gain       
        # apply damping
        damping = self.base_damping * self.finger_damping ** len(self.fingers)
        self.angular_velocity = damping * self.angular_velocity 

    def set_velocity(self, v):
        self.angular_velocity[1:4] = v

    def down(self, id, xyz):        
        self.fingers[id] = Finger(xyz, wall_clock())
        
    def up(self, id, xyz):
        del self.fingers[id]        

    def drag(self, id, xyz):
        # update angular velocities based on drag
        t = wall_clock()
        finger = self.fingers[id]
        dt, velocity = finger.update_velocity(xyz, t)
        rot = tn.quaternion_matrix(self.orientation)
        # get finger velocity vector
        # compute torque = point x velocity
        torque = np.cross(xyz, velocity)
        # axis switchery
        torque = torque[[2,1,0]]
        #torque[1] = -torque[1]
        torque = np.dot(rot[:3,:3], torque)
        # we can just accumulate the angular velocity
        # synchronously
        self.angular_velocity[1:4] += torque * dt
        finger.last_xyz = xyz
        finger.last_t = t


class RotationTest(object):
    def __init__(self):
        self.viewer = sphere_sim.make_viewer(show_touches=True, draw_fn=self.draw, 
        tick_fn=self.tick,
        touch_fn=self.touch)
        self.rotater = RotationHandler()                

        pts = np.array(sphere.spiral_layout(256))
        
        # point shader; simple coloured circles, with no spherical correction
        point_shader = shader_from_file([getshader("sphere.vert"), getshader("user/point.vert")], [getshader("user/point.frag")])
        self.point_vbo = ShaderVBO(point_shader, IBuf(np.arange(len(pts))), 
                                    buffers={"position":VBuf(pts), },
                                    vars={"constant_size":10.0,                                    
                                    }, 
                                    attribs={"color":(1,1,1,1)},
                                    primitives=GL_POINTS)
        
        self.viewer.start()

    def touch(self, events):        
        for event in events:
            xyz = sphere.polar_to_cart(*event.touch.lonlat)
            if event.event=="DRAG":
                self.rotater.drag(event.touch.id, xyz)
            if event.event=="UP":
                self.rotater.up(event.touch.id, xyz)
            if event.event=="DOWN":
                self.rotater.down(event.touch.id, xyz)


    def draw(self):
        glClearColor(0.0,0.0,0.0,1)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_VERTEX_PROGRAM_POINT_SIZE)
        glEnable(GL_POINT_SPRITE)
        
        self.point_vbo.draw(vars={"quat":self.rotater.orientation})

    def tick(self):        
        self.rotater.update()
        pass
        
                        

              
if __name__=="__main__":
    p = RotationTest()
    
    
   