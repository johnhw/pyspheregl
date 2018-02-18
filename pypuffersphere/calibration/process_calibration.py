import pandas as pd
import timeit
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab 
import cPickle, base64, bz2
import os, sys, time, random
from collections import defaultdict
import pyproj
import scipy.optimize, scipy.interpolate, scipy.misc
from sklearn import gaussian_process
from pypuffersphere.sphere import sphere
import random

import matplotlib as mpl
mpl.rcParams['lines.linewidth'] = 0.2

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
    
    
def polar_to_az(lon, lat):    
    """Convert polar to azimuthal x,y co-ordinates """
    r = (np.pi/2-lat)/np.pi          
    x,y = r * np.cos(lon), r*np.sin(lon)
    return x,y  

def az_to_polar(x, y):
    """Convert azimuthal x,y to polar co-ordinates"""
    lat = -np.sqrt((x**2)+(y**2)) * np.pi + np.pi/2
    lon = np.arctan2(y,x)
    return lon, lat

def polar_adjust(lon, lat, s=1):    
    """Rescale lon, lat by contracting or expanding from the north pole. s sets
    the scaling factor. """
    x, y = polar_to_az(lon, lat)    
    x = x * s
    y = y * s        
    return az_to_polar(x,y)
    
def quadratic_polar_adjust(lon, lat, coeff):
    """Adjust the given lon, lat co-ordiantes by converting to azimuithal equidistant
    representation and apply the 2D quadratic polynomial given by coeff (12 coefficients)"""
    r = (np.pi/2-lat)/np.pi          
    x,y = r * np.cos(lon), r*np.sin(lon)
    adjust_x = coeff[0]*x + coeff[1]*y + coeff[2]*x*x + coeff[3]*y*y + coeff[4]*x*y + coeff[5]
    adjust_y = coeff[6]*x + coeff[7]*y + coeff[8]*x*x + coeff[9]*y*y + coeff[10]*x*y + coeff[11]
    lat = -np.sqrt((adjust_x**2)+(adjust_y**2)) * np.pi + np.pi/2
    lon = np.arctan2(adjust_y,adjust_x)
    return lon, lat
    
   
def cubic_polar_adjust(lon, lat, coeff):
    """Adjust the given lon, lat co-ordiantes by converting to azimuithal equidistant
    representation and apply the 2D cubic polynomial given by coeff (20 coefficients)"""
    r = (np.pi/2-lat)/np.pi          
    x,y = r * np.cos(lon), r*np.sin(lon)
    adjust_x = coeff[0]*x + coeff[1]*y + coeff[2]*x*x + coeff[3]*y*y + coeff[4]*x*y + coeff[5] + coeff[12] * x * x *y + coeff[13] * x * y *y + coeff[14] * y * y *y + coeff[15]*x*x*x
    
    adjust_y = coeff[6]*x + coeff[7]*y + coeff[8]*x*x + coeff[9]*y*y + coeff[10]*x*y + coeff[11]+ coeff[16] * x * x *y + coeff[17] * x * y *y + coeff[18] * y * y *y + coeff[19]*x*x*x
    lat = -np.sqrt((adjust_x**2)+(adjust_y**2)) * np.pi + np.pi/2
    lon = np.arctan2(adjust_y,adjust_x)
    return lon, lat


def spherical_mse(calibration, fn):  
    """Return the mse error using the given correction"""
    distances = []
    for ix,row in calibration.iterrows():        
        corr_touch_lon, corr_touch_lat = fn(row["touch_lon"], row["touch_lat"])                
        distances.append(sphere.spherical_distance((row["target_lon"],row["target_lat"]), (corr_touch_lon, corr_touch_lat)))
        
    #return np.median(distances)
    return np.sqrt(np.mean(np.array(distances)**2))  


def correction_error(calibration, s):
    """Return the mse error using constant correction"""    
    return spherical_mse(calibration, lambda x,y: polar_adjust(x,y,s))

def quadratic_error(calibration, coeff):
    return spherical_mse(calibration, lambda x,y:quadratic_polar_adjust(x,y, coeff=coeff))
    
def cubic_error(calibration, coeff):    
    return spherical_mse(calibration, lambda x,y:cubic_polar_adjust(x,y, coeff=coeff))

def cubic_fit(calibration):                
    #return [1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0]
    best_cubic_coeff = scipy.optimize.minimize(lambda x:cubic_error(calibration,x), [1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0])        
    return best_cubic_coeff.x

def quadratic_fit(calibration):            
    #return [1,0,0,0,0,0,0,1,0,0,0,0]
    best_quadratic_coeff = scipy.optimize.minimize(lambda x:quadratic_error(calibration,x), [1,0,0,0,0,0,0,1,0,0,0,0])    
    return best_quadratic_coeff.x
    
    

def train_gp(calibration, n=None):
    """Train a pair of squared-exponential Gaussian processes to predict offsets
    in azimuthal equidistant space. The GPs are trained on x, y inputs in the
    azimuthal space, and there is one GP for the x' and y' outputs.
    
    Returns a pair of GP objects (gp_x, gp_y) that perform the prediction."""
    unique_targets = calibration.groupby(["target_x", "target_y"]).mean()    
    
    if n is not None:
        unique_targets = unique_targets.loc[random.sample(unique_targets.index, n)]
        
    target_x = unique_targets["target_az_x"]
    target_y = unique_targets["target_az_y"]
    corr_x = unique_targets["touch_az_x"]
    corr_y = unique_targets["touch_az_y"]
    resid_x = np.array(target_x - corr_x)
    resid_y = np.array(target_y - corr_y)
    in_x = unique_targets["touch_az_x"]
    in_y = unique_targets["touch_az_y"]    
    target = np.vstack((in_x, in_y)).transpose()
    gp_x = gaussian_process.GaussianProcess(theta0=1e-2, thetaL=1e-5, thetaU=1e-1, nugget=4e-5, random_start=20)
    gp_y = gaussian_process.GaussianProcess(theta0=1e-2, thetaL=1e-5, thetaU=1e-1, nugget=4e-5, random_start=20)
    gp_x.fit(target, resid_x)
    gp_y.fit(target, resid_y)    
    
    return gp_x, gp_y

    

def train_gp_sp(calibration, n=None):
    """Train a pair of squared-exponential Gaussian processes to predict offsets
    in azimuthal equidistant space. The GPs are trained on x, y inputs in the
    azimuthal space, and there is one GP for the x' and y' outputs.
    
    Returns a pair of GP objects (gp_x, gp_y) that perform the prediction."""
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
    gp_x = gaussian_process.GaussianProcess(theta0=1e-2, thetaL=1e-7, thetaU=3e1, nugget=1e-3, random_start=10)
    gp_y = gaussian_process.GaussianProcess(theta0=1e-2, thetaL=1e-7, thetaU=3e1, nugget=1e-3, random_start=10)
    gp_x.fit(target, resid_x)
    gp_y.fit(target, resid_y)    
    
    return gp_x, gp_y

        
def gp_adjust(lon, lat, gp_x, gp_y):
    x,y,z = sphere.spherical_to_cartesian((lon, lat))
    az_x, az_y = sphere.polar_to_az(lon, lat)
    xc = gp_x.predict([x,y,z])
    yc = gp_y.predict([x,y,z])
    corr_touch_lon, corr_touch_lat = sphere.az_to_polar(az_x+xc, az_y+yc)
    return corr_touch_lon, corr_touch_lat
       
    
def gp_predict(gp_x, gp_y, az_x, az_y):
    """Predict the corrected lon, lat of the position given
    by az_x, az_y (touch point in azimuthal co-ordinates) using
    the Gaussian Process correction method."""
    tinput = [az_x, az_y]
    xc = gp_x.predict(tinput)
    yc = gp_y.predict(tinput)        
    corr_touch_lon, corr_touch_lat = sphere.az_to_polar(az_x+xc, az_y+yc)
    return corr_touch_lon, corr_touch_lat


def gp_adjust_old(lon, lat, gp_x, gp_y):
    """Given a lon,lat input position, convert to azimuthal, predict offset
    using the given GP, and convert to lon, lat as the return value"""
    x,y = sphere.polar_to_az(lon, lat)
    return gp_predict(gp_x, gp_y, x, y)
    


    
def gp_error(gp_x, gp_y):
    """Return the error function using the passed GP objects"""
    return spherical_mse(lambda x,y:gp_adjust(x,y,gp_x,gp_y))

   
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
    print
    
    print "Computing constant correction..."
    correction_factor = scipy.optimize.minimize_scalar(lambda x:correction_error(calibration,x), bounds=(0,2)).x
    print "Computing cubic correction..."
    cubic_coeff = cubic_fit(calibration)
    print "Computing quadratic correction..."
    quadratic_coeff = quadratic_fit(calibration)     
    print "Computing GP correction..."
    #gp_x, gp_y = train_gp(calibration)
    gp_x, gp_y = train_gp_sp(calibration)
    return correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y

    


def latest_file(path, ext):
    dated_files = [(os.path.getmtime(os.path.join(path, fn)), os.path.basename(os.path.join(path, fn))) 
                   for fn in os.listdir(path) if fn.lower().endswith(ext)]
    dated_files.sort()
    dated_files.reverse()
    newest = dated_files[0][1]
    return newest


  
def write_module(fname, calibration_name, calibration, errors, fit):
    correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y = fit

    with open(fname, "w") as f:
        f.write("""# AUTOGENERATED by process_calibration.py on {date}
# DO NOT EDIT
# This file contains calibration constants to align touches on the PufferSphere
# It was generated from the calibration file {file}
# 
# Usage:
# lon, lat = get_calibrated_touch(tuio_x, tuio_y)
# optionally, can specify correction mode: can be one of
#
#   'gp' GP correction (default) -- most accurate, but may be slow
#   'cubic' cubic curve correction
#   'quadratic' quadratic curve correction
#   'constant' simple constant correction
#   'none' perform no correction (equivalent to calling sphere.tuio_to_polar)
#
# Example:
# lon, lat = get_calibrated_touch(tuio_x, tuio_y, mode='cubic')
#       
# Normally, GP correction should be used. If this is too slow, use 'cubic' instead.
# 
# The expected performance for this calibration set is (all figures in degrees):
#
""".format(date=time.asctime(time.localtime()), file=calibration_name))
        
        f.write("# Expected RMS error for mode 'none':      %.2f \n" % rms(errors["none"]))
        f.write("# Expected RMS error for mode 'constant':  %.2f \n" % rms(errors["constant"]))
        f.write("# Expected RMS error for mode 'quadratic': %.2f \n" % rms(errors["quadratic"]))
        f.write("# Expected RMS error for mode 'cubic':     %.2f \n" % rms(errors["cubic"]))
        f.write("# Expected RMS error for mode 'gp':        %.2f \n" % rms(errors["gp"]))
        
        f.write("""    
import  cPickle, base64
from pypuffersphere.sphere import sphere
from pypuffersphere.calibration import process_calibration
from numpy import pi
import os
        """)
        
        def precise_list(x):
            return "["+",".join(["%.18f"%f for f in x])+"]"
            
        f.write("""\ncalibration_file = "%s"\n""" % calibration_name)
        f.write("""rmse={}\n""")
        f.write("rmse['none']=%.8f\n" %rms(errors["none"]))
        f.write("rmse['constant']=%.8f\n" % rms(errors["constant"]))
        f.write("rmse['quadratic']=%.8f\n" % rms(errors["quadratic"]))
        f.write("rmse['cubic']=%.8f\n" % rms(errors["cubic"]))
        f.write("rmse['gp']=%.8f\n"  % rms(errors["gp"]))
        f.write("""
def expected_rmse(mode):
    \"""Return the expected RMS error for the given correction mode, in degrees\"""
    return rmse.get(mode, rmse['none'])
""")
        

        f.write("""
# calibration constants
correction_factor = {correction_factor}
cubic_coeff = {cubic_coeff}
quadratic_coeff = {quadratic_coeff}
        """.format(correction_factor="%.18f"%correction_factor, cubic_coeff=precise_list(cubic_coeff), quadratic_coeff=precise_list(quadratic_coeff)))

        with open("gp_calibration.dat", "wb") as gp_f:
            cPickle.dump((gp_x, gp_y), gp_f, protocol=-1)
        
        f.write("""

# find gp_calibration.dat in the same directory as *this file*
dirname = os.path.abspath(os.path.dirname(__file__))

# GP data in pickled format
with open(os.path.join(dirname,"gp_calibration.dat"), "rb") as gp_f:
    gp_x, gp_y = cPickle.load(gp_f)\n\n""")
        
        
        f.write("""


def get_calibrated_touch(tuio_x, tuio_y, mode='gp'):
    \"""Returns the lon, lat co-ordinates (radians) of a touch point after applying calibration
    from the preset constants. Input is in tuio format (range [0,1] for x and y). 
    mode selects the correction mode, which can be one 'gp', 'cubic', 'quadratic', 'constant', 'none'            
    \"""
    
    lon, lat = sphere.tuio_to_polar(tuio_x, tuio_y)
    lon = lon % (2*pi) - pi
    if mode=='gp':        
        lon,lat = process_calibration.gp_adjust(lon, lat, gp_x, gp_y)
    if mode=='cubic':        
        lon,lat =process_calibration.cubic_polar_adjust(lon, lat, cubic_coeff)
    if mode=='quadratic':        
        lon,lat =process_calibration.quadratic_polar_adjust(lon, lat, quadratic_coeff)
    if mode=='constant':        
        lon,lat =process_calibration.polar_adjust(lon, lat, correction_factor)
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


def plot_calibration_state(calibration, fit):
    correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y = fit
    print
    plot_correction_models(calibration, correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y)
    fname = "calibration_plot.pdf"
    print
    print "Writing calibration plot to %s" % fname
    try:
        plt.savefig(fname,bbox_inches='tight', pad_inches=0)
    except IOError:
        print "WARNING: Could not write to %s" % fname
    
    plt.figtext(0.04, 0.16, "Calibration data from %s" % calibration_name, fontdict={"size":5})
    plt.figtext(0.04, 0.13, "%d calibration targets; %d unique" % (len(calibration), len(grouped)), fontdict={"size":5})
    plt.figtext(0.04, 0.1, "%.2f degrees intra-target error" % np.degrees(true_rms), fontdict={"size":5})
    error_labels(calibration, uncorrected_rmse, constant_rmse, quadratic_rmse, cubic_rmse, gp_rmse)    
    fname = "calibration_state.pdf"
    print
    print "Writing calibration plot to %s" % fname
    try:
        plt.savefig(fname)
    except IOError:
        print "WARNING: Could not write to %s" % fname
        
        
def plot_error_distribution(calibration, labels, errors):
    
    plt.figure(figsize=(6,9))
    
    plt.xlabel("Correction method")
    plt.ylabel("Error (degrees)")
    plt.gca().set_frame_on(False)
    simpleaxis(plt.gca())    
    seaborn.boxplot(errors)
    plt.xticks([0,1,2,3,4], [""]+labels)
    
    
    fname = "calibration_dist.pdf"    
    print "Writing calibration boxplot to %s" % fname
    try:
        plt.savefig(fname,bbox_inches='tight', pad_inches=0)
    except IOError:
        print "WARNING: Could not write to %s" % fname
        
        
def plot_offset_shading(calibration, gp_x, gp_y, correction_factor):
    gp_offset_shading(calibration, gp_x, gp_y, correction_factor)
    fname = "gp_offset.pdf"
    plt.savefig("gp_offset.svg",bbox_inches='tight', pad_inches=0)
    print "Writing GP offset plot to %s" % fname
    try:
        plt.savefig(fname,bbox_inches='tight', pad_inches=0)
    except IOError:
        print "WARNING: Could not write to %s" % fname

        
        
def generate_module(calibration_name, calibration, errors, fit):
  
    print
    print "Generating calibration.py"    
    write_module("calibration.py", calibration_name, calibration, errors, fit)
    print
    print "Testing calibration.py..."
    correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y = fit
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
        assert(valid(cal.test_calibrated_touch(test_x, test_y, 'gp'),gp_adjust(lon, lat, gp_x, gp_y), 'GP'))        
        assert(valid(cal.test_calibrated_touch(test_x, test_y, 'cubic'),cubic_polar_adjust(lon, lat, cubic_coeff), 'cubic'))        
        assert(valid(cal.test_calibrated_touch(test_x, test_y, 'quadratic'),quadratic_polar_adjust(lon, lat, quadratic_coeff),'quadratic'))        
        assert(valid(cal.test_calibrated_touch(test_x, test_y, 'constant'),polar_adjust(lon, lat, correction_factor), 'constant'))        
        assert(valid(cal.test_calibrated_touch(test_x, test_y, 'none'),polar_adjust(lon, lat, 1), 'none'))
    test_calibration(0.5, 0.5)
    print "calibration.py seems to be working"
        

def time_module(calibration):
    import calibration as cal
    tuio_time = timeit.timeit("lon, lat = sphere.polar_to_tuio(0.5, 0.5)", setup="from pypuffersphere.sphere import sphere", number=1000)
    times = {}
    times["tuio"] = tuio_time
    for mode in ["none", "constant", "quadratic", "cubic", "gp"]:
        ds = []
        
        tx,ty=0.5,0.5
        mode_time = timeit.timeit("lon, lat = calibration.test_calibrated_touch(0.5, 0.5, mode='%s')"%mode, setup="import calibration", number=1000)
        times[mode] = mode_time        
    return times
        
def report_errors(errors):
    for error in errors:
        print "Error for %s: RMS=%.2f, median=%.2f" % (error, rms(errors[error]), np.median(errors[error]))
        

def generate_offset_map(mode, fn, res=1600):
    print "Generating offset map for calibration type %s at %dx%d" % (mode, res, res)
    print "Offsets are 8-bit values in pixels; X in red, Y in green." 
    img = np.zeros((res,res,3),dtype=np.uint8)
    for x in range(res):
        print x
        for y in range(res):
            rx, ry = x/float(res), y/float(res)
            # if in unit circle (i.e. on sphere)
            if np.sqrt(rx**2+ry**2)<1:
                lon, lat = az_to_polar(rx, ry)
                dlon, dlat = fn(lon, lat)
                cx, cy = polar_to_az(dlon, dlat)
                dx = (rx-cx) * res
                dy = (ry-cy) * res
                img[x,y,0] = dx + 128
                img[x,y,1] = dy + 128
    scipy.misc.imsave("sphere_offset_%s.png" % mode, img)


def generate_offset_map_gp(gp_x, gp_y, res=400):
    print "Generating offset map for GP at %dx%d" % (res, res)
    print "Offsets are 8-bit values in pixels; X in red, Y in green" 
    img = np.zeros((res,res,3),dtype=np.uint8)
    
    for x in range(res):
        print x
        for y in range(res):
            rx, ry = x/float(res/2)-1, y/float(res/2)-1
            
            # if in unit circle (i.e. on sphere)
            if np.sqrt(rx**2+ry**2)<1:
                tinput = [rx,ry]
                dx = (gp_x.predict(tinput)) * (res) + 128
                dy = (gp_y.predict(tinput)) * (res) + 128                
                
                if dx<0 or dx>255 or dy<0 or dy>255:
                    print "Clip warning!"
                img[x,y,0] = np.clip(dx, 0, 255)
                img[x,y,1] = np.clip(dy, 0, 255)
                
    scipy.misc.imsave("sphere_offset_gp.png", img)    
        
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
        correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y = fit_models(calibration)       
    else:
        correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y = fit
        
            
    errors = {}    
    errors["none"] =  error_distribution(calibration, lambda x,y:polar_adjust(x,y,s=1))
    errors["constant"] = error_distribution(calibration, lambda x,y:polar_adjust(x,y,s=correction_factor))
    errors["quadratic"] = error_distribution(calibration, lambda x,y:quadratic_polar_adjust(x,y,quadratic_coeff))
    errors["cubic"] = error_distribution(calibration, lambda x,y:cubic_polar_adjust(x,y,cubic_coeff))
    errors["gp"] = error_distribution(calibration, lambda x,y:gp_adjust(x,y,gp_x,gp_y))
    
    
    report_errors(errors)
        
    #plot_calibration_state(calibration, (correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y))                
    #plot_error_distribution(calibration, ["Constant", "Quadratic", "Cubic", "GP"], [constant, quadratic, cubic, gp])        
    #plot_offset_shading(calibration, gp_x, gp_y, correction_factor)
    
    # only write the calibration if we fitted new models
    if fit is None: 
        generate_module(calibration_name, calibration, errors, (correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y))
   
    #generate_offset_map("gp", lambda x,y:gp_adjust(x,y,gp_x,gp_y))
    #generate_offset_map_gp(gp_x, gp_y)
    mode_times = time_module(calibration)
    for mode in mode_times:
        print "%s took %d ms" %(mode, 1000*mode_times[mode])
    
        
    return (correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y), calibration
        
if __name__=="__main__":            
    if len(sys.argv)==3:
        test_calibration(sys.argv[1], sys.argv[2])    
    elif len(sys.argv)==2:
        process_calibration(sys.argv[1])
    else:
        process_calibration()


