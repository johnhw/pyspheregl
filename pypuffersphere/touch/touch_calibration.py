import pandas as pd
import timeit
import numpy as np
import pickle
import os, sys, time, random
from sklearn import gaussian_process
from pypuffersphere.sphere import sphere


def train_gp(calibration, subsample=None):
    """Train a squared-exponential Gaussian process to predict offsets
    in azimuthal equidistant space. The GPs are trained on x, y, z inputs in the
    cartesian space, and predict x' and y' outputs.
    
    Returns a GP object that performs the prediction."""
    unique_targets = calibration.groupby(["target_x", "target_y"]).mean()    
    
    # subsample if required
    if subsample is not None:
        unique_targets = unique_targets.loc[random.sample(unique_targets.index, subsample)]

    tx, ty, tz = sphere.spherical_to_cartesian((unique_targets["target_lon"], unique_targets["target_lat"]))

    x,y,z = sphere.spherical_to_cartesian((unique_targets["touch_lon"], 
                                            unique_targets["touch_lat"]))    

    
    target = np.vstack((x,y,z)).transpose()       
    residual = np.vstack((tx, ty, tz)).T
    gp = gaussian_process.GaussianProcessRegressor(alpha=1e-3)
    gp.fit(target, residual)
    return gp

        
def gp_adjust(lon, lat, gp):
    x,y,z = sphere.spherical_to_cartesian((lon, lat))
    res = gp.predict([[x,y,z]])
    xc, yc, zc = res[0] + np.array([x,y,z])
    corr_touch_lon, corr_touch_lat = sphere.cart_to_polar(xc, yc, zc)
    return corr_touch_lon, corr_touch_lat

def fix_angle(x):
    return np.arctan2(np.sin(x), np.cos(x))


def augment_calibration(calibration):
    xs, ys = calibration["tuio_x"], calibration["tuio_y"]
    lonlat = np.array([sphere.tuio_to_polar(x,y) for x,y in zip(xs,ys)])    
    calibration["touch_lon"],calibration["touch_lat"] = lonlat[:,0], lonlat[:,1]

    lons,lats = calibration["target_lon"], calibration["target_lat"]
    xys = np.array([sphere.polar_to_tuio(lon,lat) for lon,lat in zip(lons,lats)])
    calibration["target_x"],calibration["target_y"] = xys[:,0], xys[:,1]

    # fix angles

    calibration["target_lon"] = fix_angle(calibration["target_lon"])
    calibration["touch_lon"] = fix_angle(calibration["touch_lon"])
    

def latest_file(path, ext):
    dated_files = [(os.path.getmtime(os.path.join(path, fn)), os.path.basename(os.path.join(path, fn))) 
                   for fn in os.listdir(path) if fn.lower().endswith(ext)]
    dated_files.sort()
    dated_files.reverse()
    newest = dated_files[0][1]
    return newest

def get_calibrated_touch(tuio_x, tuio_y, gp):
    """Returns the lon, lat co-ordinates (radians) of a touch point after applying calibration
    from the preset constants. Input is in tuio format (range [0,1] for x and y). 
    mode selects the correction mode, which can be one 'gp', 'cubic', 'quadratic', 'constant', 'none'            
    """
    
    lon, lat = sphere.tuio_to_polar(tuio_x, tuio_y)    
    lon,lat = gp_adjust(lon, lat, gp)
    return lon, lat
    


def error_distribution(calibration, fn):
    """Return the error distribution after applying fn"""
    ds = []
    for ix, row in calibration.iterrows():
        lon, lat = row["target_lon"], row["target_lat"]
        tlon, tlat = row["touch_lon"], row["touch_lat"]
        
        # compute offset from constant corrected
        lonc, latc = fn(tlon, tlat)
        # plt.plot(lon, lat, 'ro')     
        # plt.plot(lonc, latc, 'gx')
        # plt.plot([lonc,tlon], [latc, tlat], 'b')
        d = sphere.spherical_distance((lon, lat), (lonc, latc))
        ds.append(np.degrees(d))      

    # lons = np.random.uniform(-np.pi, np.pi, (30,))
    # lats = np.random.uniform(-np.pi/4, np.pi/2, (30,))
    # for lon, lat in zip(lons, lats):
    #     lonc, latc = fn(lon, lat)
    #     plt.plot([lon, lonc], [lat, latc], 'b')
        
        
    # plt.show()
    return ds          

def rms(x):
    return np.sqrt(np.mean(np.array(x)**2))

class CalibrationException(Exception):
    pass

# import matplotlib.pyplot as plt

class Calibration(object):
    def get_calibrated_touch(self, x, y):
        return get_calibrated_touch(x,y,self.gp)
        
    def __init__(self, calibration_name=None, exclude_distance=25):
        if calibration_name is None:
            print "No calibration file specified."
            latest_csv = latest_file("calibration", ".csv")
            print "Using latest calibration file found: %s" % latest_csv
            calibration_name = latest_csv    
        print "Processing %s" % calibration_name
        print

        self.fname = calibration_name
        # read the calibration data
        calibration = pd.io.parsers.read_table(os.path.join("calibration", calibration_name), delimiter=",", skipinitialspace=True)
        augment_calibration(calibration)

       

        # compute distances from estimated touches (w/o calibration) and target touches        
        calibration["distance"] = [sphere.spherical_distance((r["target_lon"], r["target_lat"]),
                                                        (r["touch_lon"], r["touch_lat"])) for ix, r in calibration.iterrows()]

        
       
        self.total_targets = len(calibration)
        
        print "Read %d calibration targets" % self.total_targets

        # exclude targets >  exclude distance away (typically <30 degrees)
        calibration = calibration[calibration["distance"]<np.radians(exclude_distance)]
        self.used_targets = len(calibration)
        print "%d targets excluded as being outliers with >25 degree offset\n%d calibration targets remain" % (self.total_targets-self.used_targets, self.used_targets)
        

        if len(calibration)<5:
            raise CalibrationException("Less than 5 calibration targets; aborting...")
            
        grouped = calibration.groupby(["target_x", "target_y"])
        self.unique = int(0.5+self.total_targets/float(len(grouped)))
        self.reps = len(grouped)
        print "%d unique targets identified; %d repeats per target" % (self.reps, self.unique)
        print
        
        print("Minimum latitude is %1.f" % np.degrees(np.min(calibration["target_lat"])))

        # allow up to 5 degrees below min latitude
        self.min_latitude = np.min(calibration["target_lat"]) - np.radians(5)


        # plt.plot(calibration["target_lon"], calibration["target_lat"], 'ro')
        # plt.plot(calibration["touch_lon"], calibration["touch_lat"], 'go')
        # plt.show()

        self.gp = train_gp(calibration)       
        error = error_distribution(calibration, lambda x,y:gp_adjust(x,y,self.gp))

        # plt.show()
        self.rms_error = rms(error)
        self.median_error =  np.median(error)
        
        print("RMS error: %.2f deg\nMedian error: %.2f deg" % (self.rms_error, self.median_error))

if __name__=="__main__":
    c = Calibration()

        