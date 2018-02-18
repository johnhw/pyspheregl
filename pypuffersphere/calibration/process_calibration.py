import pandas as pd
import timeit
import numpy as np
import pickle
import os, sys, time, random
import pyproj
from sklearn import gaussian_process
from pypuffersphere.sphere import sphere


def spherical_mean_rms(lonlats):
    """Compute spherical mean, rms error and geodesic distances, using Robinson projection method"""
    proj = pyproj.Proj("+proj=robin")
    pts = []
    for lon, lat in lonlats:
        pts.append(proj(lon, lat))
    pts = np.array(pts)
    proj_mean = np.mean(pts, axis=0)    
    lon_mean, lat_mean = proj(proj_mean[0], proj_mean[1], inverse=True)        
    distances = []
    for lon, lat in lonlats:
        distances.append(sphere.spherical_distance((lon_mean, lat_mean), (lon, lat)))
    rms = np.sqrt(np.mean(np.array(distances)**2))    
    return (lon_mean, lat_mean), rms, distances
    
def spherical_mse(calibration, fn):  
    """Return the mse error using the given correction"""
    distances = []
    for ix,row in calibration.iterrows():        
        corr_touch_lon, corr_touch_lat = fn(row["touch_lon"], row["touch_lat"])                
        distances.append(sphere.spherical_distance((row["target_lon"],row["target_lat"]), (corr_touch_lon, corr_touch_lat)))
    return np.sqrt(np.mean(np.array(distances)**2))  


def train_gp_sp(calibration, n=None):
    """Train a squared-exponential Gaussian process to predict offsets
    in azimuthal equidistant space. The GPs are trained on x, y, z inputs in the
    cartesian space, and predict x' and y' outputs.
    
    Returns a GP object that performs the prediction."""
    unique_targets = calibration.groupby(["target_x", "target_y"]).mean()    
    
    if n is not None:
        unique_targets = unique_targets.loc[random.sample(unique_targets.index, n)]
        
    target_x = unique_targets["target_az_x"]
    target_y = unique_targets["target_az_y"]
    corr_x = unique_targets["touch_az_x"]
    corr_y = unique_targets["touch_az_y"]
    resid_x = np.array(target_x - corr_x)
    resid_y = np.array(target_y - corr_y)    
    x,y,z = sphere.spherical_to_cartesian((unique_targets["touch_lon"], unique_targets["touch_lat"]))    
    target = np.vstack((x,y,z)).transpose()     
    residual = np.vstack((resid_x, resid_y)).T
    gp = gaussian_process.GaussianProcessRegressor()
    gp.fit(target, residual)
    return gp

        
def gp_adjust(lon, lat, gp):
    x,y,z = sphere.spherical_to_cartesian((lon, lat))
    az_x, az_y = sphere.polar_to_az(lon, lat)
    res = gp.predict([[x,y,z]])
    xc, yc = res[0]    
    corr_touch_lon, corr_touch_lat = sphere.az_to_polar(az_x+xc, az_y+yc)
    return corr_touch_lon, corr_touch_lat

    
   
def augment_calibration(calibration):
    xs, ys = calibration["tuio_x"], calibration["tuio_y"]
    lonlat = np.array([sphere.tuio_to_polar(x,y) for x,y in zip(xs,ys)])    
    calibration["touch_lon"],calibration["touch_lat"] = lonlat[:,0], lonlat[:,1]

    lons,lats = calibration["target_lon"], calibration["target_lat"]
    xys = np.array([sphere.polar_to_tuio(lon,lat) for lon,lat in zip(lons,lats)])
    calibration["target_x"],calibration["target_y"] = xys[:,0], xys[:,1]

    # remove extreme targets which could not be hit (distance > 1 radian)

    calibration["target_lon"] = calibration["target_lon"] % (2*np.pi) - np.pi
    calibration["touch_lon"] = calibration["touch_lon"] % (2*np.pi) - np.pi
    
    # calculate co-ordinates in azimuthal space

    lons, lats = calibration["touch_lon"], calibration["touch_lat"]
    xy = np.array([sphere.polar_to_az(lon,lat) for lon,lat in zip(lons,lats)])
    calibration["touch_az_x"],calibration["touch_az_y"] = xy[:,0], xy[:,1]

    lons, lats = calibration["target_lon"], calibration["target_lat"]
    xy = np.array([sphere.polar_to_az(lon,lat) for lon,lat in zip(lons,lats)])
    calibration["target_az_x"],calibration["target_az_y"] = xy[:,0], xy[:,1]


def estimate_touch_error(calibration, grouped):    
    distances = []
    for name, group in grouped:
        mean, rms, dists = spherical_mean_rms(zip(group["touch_lon"], group["touch_lat"]))
        distances += dists
    true_rms =  np.sqrt(np.mean(np.array(distances)**2))           
    slat = grouped['touch_lat'].var()
    slon = grouped['touch_lon'].var()
    print "Intra-target angular std. dev. estimated at %.2f degrees" % np.degrees(np.sqrt(np.mean(slat)+np.mean(slon)))
    print "Intra-target angular RMS estimated at %.2f degrees" % np.degrees(true_rms)
    return true_rms
    
def fit_models(calibration): 
    print "Computing GP correction..."
    gp = train_gp_sp(calibration)
    return gp
    

def latest_file(path, ext):
    dated_files = [(os.path.getmtime(os.path.join(path, fn)), os.path.basename(os.path.join(path, fn))) 
                   for fn in os.listdir(path) if fn.lower().endswith(ext)]
    dated_files.sort()
    dated_files.reverse()
    newest = dated_files[0][1]
    return newest


  
def write_module(fname, calibration_name, calibration, errors, fit):
    gp = fit

    with open(fname, "w") as f:
        f.write("""# AUTOGENERATED by process_calibration.py on {date}
# DO NOT EDIT
# This file contains calibration constants to align touches on the PufferSphere
# It was generated from the calibration file {file}
# 
# Usage:
# lon, lat = get_calibrated_touch(tuio_x, tuio_y)

# The expected performance for this calibration set is (all figures in degrees):
#
""".format(date=time.asctime(time.localtime()), file=calibration_name))
        
        f.write("# Expected RMS error for mode 'gp':        %.2f \n" % rms(errors["gp"]))
        
        f.write("""    
import  pickle
from pypuffersphere.sphere import sphere
from pypuffersphere.calibration import process_calibration
from numpy import pi
import os
        """)
        
        def precise_list(x):
            return "["+",".join(["%.18f"%f for f in x])+"]"
            
        f.write("""\ncalibration_file = "%s"\n""" % calibration_name)
        f.write("""rmse={}\n""")        
        f.write("rmse['gp']=%.8f\n"  % rms(errors["gp"]))
 
        with open("gp_calibration.dat", "wb") as gp_f:
            pickle.dump(gp, gp_f, protocol=-1)
        
        f.write("""

# find gp_calibration.dat in the same directory as *this file*
dirname = os.path.abspath(os.path.dirname(__file__))

# GP data in pickled format
with open(os.path.join(dirname,"gp_calibration.dat"), "rb") as gp_f:
    gp= pickle.load(gp_f)\n\n""")
        
        
        f.write("""


def get_calibrated_touch(tuio_x, tuio_y, mode='gp'):
    \"""Returns the lon, lat co-ordinates (radians) of a touch point after applying calibration
    from the preset constants. Input is in tuio format (range [0,1] for x and y). 
    mode selects the correction mode, which can be one 'gp', 'cubic', 'quadratic', 'constant', 'none'            
    \"""
    
    lon, lat = sphere.tuio_to_polar(tuio_x, tuio_y)
    lon = lon % (2*pi) - pi
    if mode=='gp':        
        lon,lat = process_calibration.gp_adjust(lon, lat, gp)
    if mode=='none':
        lon,lat = lon, lat    
    return (lon+pi)%(2*pi), lat


def test_calibrated_touch(tuio_x, tuio_y, mode='gp'):
    \"""Runs get_calibrated_touch() in the form that the test code expects (i.e. with a
        +pi offset in longitude)
    \"""
    lon, lat = get_calibrated_touch(tuio_x, tuio_y, mode)
    return (lon+pi)%(2*pi), lat

\n""")
        
        f.write(" # END OF calibration.py")
        
fitted_params = {}


def test_calibration(calibration_name, test_name):
    
    print
    print "*** Training..."    
    fit, train_calibration = process_calibration(calibration_name)
    print    
    print "*** Testing..."
    process_calibration(test_name, fit=fit)
    
def error_distribution(calibration, fn):
    """Return the error distribution after applying fn"""
    ds = []
    for ix, row in calibration.iterrows():
        lon, lat = row["target_lon"], row["target_lat"]
        tlon, tlat = row["touch_lon"], row["touch_lat"]
        # compute offset from constant corrected
        lonc, latc = fn(tlon, tlat)
        d = sphere.spherical_distance((lon, lat), (lonc, latc))
        ds.append(np.degrees(d))        
    return ds          

def rms(x):
    return np.sqrt(np.mean(np.array(x)**2))

        
def generate_module(calibration_name, calibration, errors, gp):
  
    print
    print "Generating calibration.py"    
    write_module("calibration.py", calibration_name, calibration, errors, gp)
    print
    print "Testing calibration.py..."
    
    import calibration as cal
    def test_calibration(test_x, test_y):
        def valid(a, b, name):
            d = sphere.spherical_distance(a,b)
            if d<1e-6:
                print "Testing %s: OK, error is within %.4e" % (name, d)
                return True
            else:
                print "Testing %s: FAIL! error exceeds 1e-6 at %.4e" % (name, d)
                return False
            
        lat, lon = sphere.tuio_to_polar(test_x, test_y)  
        lon += np.pi
        assert(valid(cal.test_calibrated_touch(test_x, test_y, 'gp'),gp_adjust(lon, lat, gp), 'GP'))                
    test_calibration(0.5, 0.5)
    print "calibration.py seems to be working"

        

        
def report_errors(errors):
    for error in errors:
        print "Error for %s: RMS=%.2f, median=%.2f" % (error, rms(errors[error]), np.median(errors[error]))
        

def process_calibration(calibration_name=None, fit=None):            
    
    if calibration_name is None:
        print "WARNING: No calibration file specified."
        latest_csv = latest_file("calibration", ".csv")
        print "Using latest calibration file found: %s" % latest_csv
        calibration_name = latest_csv
    
    print "Processing calibration %s" % calibration_name
    print
    # load the calibration data
    calibration = pd.io.parsers.read_table(os.path.join("calibration", calibration_name), delimiter=",", skipinitialspace=True)
    augment_calibration(calibration)
    
    calibration["distance"] = [sphere.spherical_distance((r["target_lon"], r["target_lat"]),
                                                     (r["touch_lon"], r["touch_lat"])) for ix, r in calibration.iterrows()]
    total_targets = len(calibration)
    print "Read %d calibration targets" % total_targets
    calibration = calibration[calibration["distance"]<np.radians(22)]
    print "%d targets excluded as being outliers with >25 degree offset\n%d calibration targets remain" % (total_targets-len(calibration), len(calibration))

    if len(calibration)<5:
        print("Less than 5 calibration targets; aborting...")
        return
    grouped = calibration.groupby(["target_x", "target_y"])
    print "%d unique targets identified; %d repeats per target" % (len(grouped), int(0.5+total_targets/float(len(grouped))))
    print
    true_rms = estimate_touch_error(calibration, grouped)
    
    if fit is None:
        gp = fit_models(calibration)       
    else:
        gp = fit        
            
    errors = {}    
    errors["gp"] = error_distribution(calibration, lambda x,y:gp_adjust(x,y,gp))
    
    report_errors(errors)        
    if fit is None: 
        generate_module(calibration_name, calibration, errors, gp)
   
    
        
    return gp, calibration
        
if __name__=="__main__":            
    if len(sys.argv)==3:
        test_calibration(sys.argv[1], sys.argv[2])    
    elif len(sys.argv)==2:
        process_calibration(sys.argv[1])
    else:
        process_calibration()


