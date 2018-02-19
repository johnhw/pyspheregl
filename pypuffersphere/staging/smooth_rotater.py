import pypuffersphere.sphere.touch_sphere as touch_lib
import time
import pypuffersphere.sphere.sphere as sphere
import numpy as np
import calibration
calib_mode = 'cubic'

class SmoothedTracker(object):
    """
    Class for managing a smoothed value
    """
    def __init__(self, alpha=0.1, max_jump=1e6):
        self.ddelta = 0
        self.last_delta = 0
        self.rotation_angle = 0
        self.last_touched_delta = 0
        self.alpha = alpha
        self.last = None
        self.max_jump = max_jump
        self.actual_delta = 0

    def reset(self):
        self.last = None
        self.ddelta = 0
        self.last_delta = 0
        self.rotation_angle = 0
        self.last_touched_delta = 0
        self.actual_delta = 0

    def update(self, next, touched=True):
        if self.last is None or next is None:
            delta = 0
        else:
            if abs(self.last - next) < self.max_jump:
                delta = -(next - self.last)
            else:
                delta = -(next - self.last)
                delta = self.max_jump * (delta / abs(delta))
        self.last = next

        self.ddelta = self.alpha * (delta - self.last_delta) + (1 - self.alpha) * self.ddelta
        self.last_delta = delta
        ret_val = 0
        if not touched:
            self.rotation_angle -= self.ddelta
            self.rotation_angle *= 0.7
            if (abs(self.rotation_angle) < 0.1):
                self.rotation_angle = 0
            self.last_touched_delta *= 0.91
            ret_val = self.last_touched_delta
        else:
            self.last_touched_delta = delta
            self.rotation_angle = 0

            if abs(delta) < 0.5:
                ret_val = 0
            else:
                ret_val = (delta * .8) + (self.last_delta * .2)

        if abs(self.actual_delta) < abs(ret_val) or touched:
            self.actual_delta = 0.8 * self.actual_delta + 0.4 * ret_val
        else:
            self.actual_delta = 0.995 * self.actual_delta + 0.005 * ret_val

        self.actual_delta = np.where(self.actual_delta == np.max(self.actual_delta), self.actual_delta, 0)            

        return self.actual_delta


class Hover(object):
    """
    Class representing a potential hover touch
    """

    def __init__(self, timeout, move_thresh):
        self.x = 0
        self.y = 0
        self.time_since_last_move = 0.0
        self.timeout = timeout
        self.move_thresh = move_thresh
        self.hovered = False
        self.disabled = False

    def update(self, dt, x, y):
        d = np.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        if d > self.move_thresh:
            self.time_since_last_move = 0.0
        else:
            self.time_since_last_move += dt

        if not self.hovered:
            self.x, self.y = x, y
            if self.time_since_last_move > self.timeout and not self.disabled:
                self.hovered = True
        else:
            if d > self.move_thresh:
                self.hovered = False
                self.time_since_last_move = 0.0
                self.disabled = True


class HoverHandler(object):
    """
    Class to manage potential hover touches
    """

    def __init__(self, timeout, move_thresh):
        self.fseqs = {}
        self.timeout = timeout
        self.move_thresh = move_thresh

    def hovered(self):
        return [i for i in self.fseqs.itervalues() if i.hovered]

    def update(self, dt, pts):
        for fseq, pt in pts.iteritems():

            if fseq in self.fseqs:
                lat, lon = calibration.get_calibrated_touch(pt[0], pt[1], calib_mode)
                self.fseqs[fseq].update(dt, lat, lon)
            else:
                self.fseqs[fseq] = Hover(timeout=self.timeout, move_thresh=self.move_thresh)
        kills = []
        for fseq in self.fseqs:
            if fseq not in pts:
                kills.append(fseq)
        for kill in kills:
            del self.fseqs[kill]




class PalmTouch(object):
    """
    Class representing potential palm touches
    """

    def __init__(self, id, x, y, time_thresh, move_thresh):
        self.id = id
        self.x = x
        self.y = y
        self.lifetime = 0
        self.valid = False
        self.time_thresh = time_thresh
        self.move_thresh = move_thresh

    def update(self, dt, x, y):
        if not self.valid:
            self.valid = True
            self.lifetime = 0

        # TODO track movement?

        self.x, self.y = x, y
        self.lifetime += dt
        if self.lifetime >= self.time_thresh:
            self.valid = True
            return

class PalmManager(object):
    """
    Class to manage palm touch events
    """
    def __init__(self, threshold=0.20, min_points=4, time_thresh=0.5, move_thresh=0.5):
        self.min_points = min_points
        self.threshold = threshold
        self.palmed = (False, -1, 0, 0)
        self.lifetime = 0
        self.points = {}
        self.time_thresh = time_thresh
        self.move_thresh = move_thresh
        self.curid = 0
        self.lastpos = (1e6, 1e6)

    def reset(self):
        self.lifetime = 0
        self.palmed = (False, -1, 0, 0)
        self.points = {}
        self.lastpos = (1e6, 1e6)

    def update(self, dt, touches):
        if len(touches) < self.min_points:
            self.reset()
            return 

        #  update state of current touches
        for id, touch in touches.iteritems():
            lat, lon = calibration.get_calibrated_touch(touch[0], touch[1], calib_mode)
            if id in self.points:
                self.points[id].update(dt, lat, lon)
            else:
                self.points[id] = PalmTouch(id, lat, lon, self.time_thresh, self.move_thresh)

        # remove any dead touches
        removed = []
        for id, touch in self.points.iteritems():
            if id not in touches:
                removed.append(id)

        for r in removed:
            try:
                del self.points[id]
            except KeyError:
                # TODO ??
                pass
                # print('warning: point %d missing' % id)

        sx, sy = 0, 0
        coords = []
        ids = []
        mage = 0

        # only want to consider points that have been active for long enough
        valid_points = [t for t in self.points.itervalues() if t.valid]
        if len(valid_points) < self.min_points:
            return

        for t in valid_points:
            x, y = t.x, t.y 
            sx += x
            sy += y
            mage += t.lifetime
            coords.append((x, y))
            ids.append(t.id)

        # calculate centroid plus average age
        centroid = (sx / len(valid_points), sy / len(valid_points))
        mage /= len(valid_points)
        palm_touches = 0

        # check if each point is within the threshold distance of the centroid
        for dt in coords:
            # TODO still not very good in some areas due to wraparound effects
            xdiff = abs(centroid[0] - dt[0])
            if xdiff > np.pi:
                xdiff = (np.pi * 2) - xdiff
            dist = np.sqrt(((centroid[0] - dt[0]) ** 2) + ((centroid[1] - dt[1]) ** 2))
            # print(centroid, dt, ids[coords.index(dt)], dist)
            if dist < self.threshold:
                palm_touches += 1

        #print('palm points: %d/%d' % (palm_touches, self.min_points))
        is_palmed = palm_touches >= self.min_points
        if is_palmed:
            if sphere.spherical_distance(self.lastpos, centroid) >= self.move_thresh:
                self.curid += 1
                self.palmed = (is_palmed, self.curid, centroid[0], centroid[1])
                self.lastpos = centroid
            else:
                self.palmed = (is_palmed, self.curid, self.lastpos[0], self.lastpos[1])

class Tap(object):
    """
    Class representing potential tap touches
    """

    def __init__(self, id, x, y, time_thresh, move_thresh):
        self.id = id
        self.x = x
        self.y = y
        self.lifetime = 0
        self.valid = True
        self.time_thresh = time_thresh
        self.move_thresh = move_thresh

    def update(self, dt, x, y):
        if not self.valid:
            return

        d = np.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        if d >= self.move_thresh:
            self.valid = False
            # print('TAP invalid, moved too far')
            return

        self.lifetime += dt
        if self.lifetime >= self.time_thresh:
            self.valid = False
            # print('TAP invalid, time exceeded')
            return

        self.x, self.y = x, y

class TapHandler(object):
    """
    Class to manage tap events
    """

    def __init__(self, zone, time_thresh, move_thresh):
        self.time_thresh = time_thresh
        self.move_thresh = move_thresh
        self.zone = zone
        self.taps = {}
        self.events = {}

    def update(self, dt, touches):
        self.events = {}
        for id, touch in touches.iteritems():
            lat, lon = calibration.get_calibrated_touch(touch[0], touch[1], calib_mode)
            if id in self.taps:
                self.taps[id].update(dt, lat, lon)
            else:
                self.taps[id] = Tap(id, lat, lon, self.time_thresh, self.move_thresh)

        removed = []
        for id, tap in self.taps.iteritems():
            if id not in touches:
                removed.append(id)

        for r in removed:
            if self.taps[r].valid:
                self.events[r] = self.taps[r]
            del self.taps[r]


class TouchManager(object):
    """
    Main class for processing TUIO touch points
    """

    def __init__(self):
        # touch zones for the sphere:
        #   main: the torus area 
        #   tokens: a band above the top of the torus
        #   top: the circular area around the very top of the sphere
        self.zones = {'main': (-1.0, 0.6), 'nowplaying': (0.6, 0.75), 'tokens': (0.75, 1.05), 'top': (1.05, 2.0)}

        if not touch_lib.is_up():
            touch_lib.init(ip="127.0.0.1", fseq=False, zones=self.zones)
            touch_lib.add_handler()
            touch_lib.start()
            print "TouchLib Up"

        self.drag_touch = None
        self.last_touch = time.clock()

        self.rotation = SmoothedTracker(alpha=0.2, max_jump=20)
        self.tilt = SmoothedTracker(alpha=0.2, max_jump=20)
        self.rotation_delta = 0
        self.tilt_delta = 0
        self.moved = False

        self.palmer = PalmManager()
        self.hover = HoverHandler(timeout=0.6, move_thresh=0.02)
        self.taps = {}
        for z in self.zones.keys():
            self.taps[z] = TapHandler(z, time_thresh=0.4, move_thresh=0.02)
        self.tap_events = {}
        self.rotation_distance, self.tilt_distance = 0, 0

    def stop(self):
        self.drag_touch = None
        self.rotation.update(None, touched=False)
        self.tilt.update(None, touched=False)       
        self.rotation.reset()
        self.tilt.reset()   
        self.rotation_delta, self.tilt_delta = 0, 0

    def update_main_other(self, dt, touches):
        rotation_delta, tilt_delta = 0, 0
        self.moved = False
        #  If our dominant touch is no longer visible
        if self.drag_touch not in touches:
            if len(touches.keys()) > 0:
                self.drag_touch = touches.keys()[0]
                self.rotation.update(None, touched=False)
                self.tilt.update(None, touched=False)
            else:
                self.drag_touch = None
                self.rotation.update(None, touched=False)
                self.tilt.update(None, touched=False)

        #  Process current dominant touch
        if self.drag_touch in touches:
            
            x, y = touches[self.drag_touch][0], touches[self.drag_touch][1]
            
            lat, lon = calibration.get_calibrated_touch(x, y, calib_mode)
           
            rotation_delta = self.rotation.update(np.degrees(lat))
            tilt_delta = self.tilt.update(np.degrees(lon))
        else:
            if len(touches) == 0:
                rotation_delta = self.rotation.update(None, touched=False)
                tilt_delta = self.tilt.update(None, touched=False)
            else:
                rotation_delta = self.rotation.update(None)
                tilt_delta = self.tilt.update(None)

        # TODO why??
        # if isinstance(rotation_delta, np.ndarray):
            # if len(rotation_delta.shape) == 0:
                # rotation_delta = 0.0
            # else:
                # rotation_delta = rotation_delta[0]

        # if isinstance(tilt_delta, np.ndarray):
            # if len(tilt_delta.shape) == 0:
                # tilt_delta = 0.0
            # else:
                # tilt_delta = tilt_delta[0]

        self.rotation_delta, self.tilt_delta = np.radians([rotation_delta, tilt_delta])
        #print(self.rotation_delta, self.tilt_delta)
        self.moved = (self.drag_touch is not None) and (abs(self.rotation_delta) > 0.001 or abs(self.tilt_delta) > 0.001)
        if self.moved: 
            self.rotation_distance += abs(self.rotation_delta)
            self.tilt_distance += abs(self.tilt_delta)
        else:
            self.rotation_distance, self.tilt_distance = 0, 0

    def update(self, dt):
        self.tap_events = {}
        if touch_lib.is_up():
            # all touches is a dict of all current touches, zonetouches
            # contains the same info but splits them up between the defined
            # zones of latitude, so you get a dict of dicts with the top level
            # having a key for each zone (e.g. 'main', 'top')
            alltouches, zonetouches = touch_lib.get_touches()
        
            #  Update Last Touch
            if len(alltouches) > 0:
                self.last_touch = time.clock()

            # handle points according to zones:
            #   top zone: only interested in taps (to trigger reset state events)
            #   token zone: only interested in taps??? to delete tokens
            #   main zone: want to process:
            #               - taps (for buttons on selected track)
            #               - palming (to clear playlist)
            #               - other touches (to rotate/tilt the display)
            for z in self.zones:
                self.taps[z].update(dt, zonetouches.get(z, {}))
                if len(self.taps[z].events) > 0:
                    self.tap_events[z] = self.taps[z].events
                    print('Found %d taps in %s' % (len(self.taps[z].events), z))

            if len(self.tap_events) > 0:
                # if there are any tap events, don't try to process any other
                # types of touch event
                return

            # any non-tap events must come from the main (torus) zone
            maintouches = zonetouches.get('main', {})

            # check for (in order of priority)
            #   - palms
            #   - hovers
            #   - other touches
            
            self.palmer.update(dt, maintouches)
            if self.palmer.palmed[0]:
                self.stop()
                return

            # only process hovers if we have a single point, otherwise
            # it's likely to mistake other types of touch for hover events
            if len(maintouches) < 2:
                self.hover.update(dt, maintouches)
                if len(self.hover.hovered()) > 0:
                    self.stop()
                    return

            self.update_main_other(dt, maintouches)

