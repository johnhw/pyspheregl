import numpy as np

# sphere stuff
import pypuffersphere.sphere.sphere as sphere
import pypuffersphere.utils.transformations as tn
from pypuffersphere.utils.graphics_utils import wall_clock


EQUATORIAL = 1  # rotate around z axis only
FREEBALL = 2    # rotate around any axis at all

class Finger:    
    # tracks the dynamics of a single finger point
    def __init__(self, last_xyz, last_t):
        self.last_xyz = np.array(last_xyz)
        self.last_t = last_t
        self.last_velocities = []

    # update the estimated velocity of this touch point
    def update_velocity(self, xyz, t):
        dt = t - self.last_t
        xyz = np.array(xyz)
        dxyz = xyz - self.last_xyz
        velocity = dxyz / dt
        self.last_xyz = xyz
        self.last_t = t

        # take median of last 5 velocities
        self.last_velocities.append(velocity)
        if len(self.last_velocities)>5:
            self.last_velocities.pop(0)
        return dt, np.median(self.last_velocities, axis=0)

class RotationHandler(object):
    # tracks the orientation of the sphere
    # using a simple model of the sphere
    # as ball with inertia and damping

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
        self.orientation += (1/40.0) * spin * self.gain       

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