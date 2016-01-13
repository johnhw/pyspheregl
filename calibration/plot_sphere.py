# Functions for spherical plotting
import numpy as np
import matplotlib.pyplot as plt
import os, sys, time, random
import pyproj

import sphere

def proj_wrapper(proj):
    def wrapped_proj(lon, lat):
        x,y = proj(np.clip(np.degrees(lon), -180, 180), np.clip(np.degrees(lat), -90, 90))        
        if abs(x)>1e8 or abs(y)>1e8:            
            return np.nan, np.nan
        return x,y
    return wrapped_proj

def tproj_wrapper(proj):
    def wrapped_proj(lon, lat):
        x,y = proj(lon, lat)
        
        if abs(x)>1e8 or abs(y)>1e8:            
            return np.nan, np.nan
        return x,y
    return wrapped_proj

    
def plot_reference_grid(proj, labels=True):
    # plot a reference grid for polar plotting
    proj = tproj_wrapper(proj)
    ax = plt.gca()
    ax.axis('off')
    rect = plt.gcf().patch
    rect.set_facecolor('white')
    label_font = {'family' : 'serif',        
        'weight' : 'normal',
        'size'   : 8,
        }
    top_font = {'family' : 'serif',        
        'weight' : 'normal',
        'size'   : 10,
        }
    
    # 10 degree grid, lat lines
    for lat in xrange(-90,90+30,30):
        pts = []
        for lon in xrange(-180,180+10,10):
            pts.append(proj(lon, lat))
        ax.plot([p[0] for p in pts], [p[1] for p in pts], 'k:', alpha=0.2)        
        x, y = proj(0, lat)
        if labels:
            ax.text(x,y,u"%d"%lat, fontdict=label_font, alpha=0.5)
    
    # equator
    pts = []
    lat = 0
    for lon in xrange(-180,180+30,30):
        pts.append(proj(lon, lat))
    ax.plot([p[0] for p in pts], [p[1] for p in pts], 'k', alpha=0.3)        
    
    
    # 10 degree grid, lon lines
    for lon in xrange(-180,180+30,30):    
        pts = []
        for lat in xrange(-90,90+10,10):    
            pts.append(proj(lon, lat))
        ax.plot([p[0] for p in pts], [p[1] for p in pts], 'k:', alpha=0.2)
        x, y = proj(lon, 0)
        if labels:
            ax.text(x,y,u"%d"%lon, fontdict=label_font, alpha=0.5)
    if labels:
        # top/bottom labels    
        x,y = proj(0,90)    
        ax.text(x,y+1e6,'Top', fontdict=top_font, alpha=0.5)
        x,y = proj(0,-90)    
        ax.text(x,y-1e6,'Base', fontdict=top_font, alpha=0.5)

        

if __name__=="__main__":
    from sphere_calibration import spiral_layout, iso_targets
    import sphere
    
    for prj, size in [("robin", (10,4)), ("ortho +lat_0=0 +lon_0=0", (10,10)), ("aeqd +lat_0=90 +lon_0=0", (10,10))]:
        plt.figure(figsize=size)        
        proj = pyproj.Proj("+proj=%s" % prj)
        
        wrapped_proj = proj_wrapper(proj)
        plot_reference_grid(proj, labels=False)    
        targets = spiral_layout(64)
        for lon, lat in targets:
            lon = lon % (2*np.pi) - np.pi
            lon_c, lat_c = sphere.polar_adjust_scale(lon, lat, 0.9)            
            x, y = wrapped_proj(lon, lat)
            xc, yc = wrapped_proj(lon_c, lat_c)
            
            plt.plot(x,y, 'rx', markersize=4)
            plt.plot(xc,yc, 'ro', markersize=4)
            plt.plot([x,xc],[y,yc], 'r:', alpha=0.5)
        plt.savefig("offset_%s.pdf" % prj[0:4], bbox_inches='tight', pad_inches=0)
            
    plt.figure(figsize=(10,10))        
    proj = pyproj.Proj("+proj=ortho")    
    wrapped_proj = proj_wrapper(proj)
    plot_reference_grid(proj, labels=False)    
    targets = spiral_layout(100)
    for lon, lat in targets:
        lon = lon % (2*np.pi) - np.pi        
        x, y = wrapped_proj(lon, lat)        
        plt.plot(x,y, 'ko', markersize=6)
        
    plt.savefig("spiral_100.pdf",bbox_inches='tight', pad_inches=0)
        
    plt.figure(figsize=(10,10))            
    plot_reference_grid(proj, labels=False)    
    targets = spiral_layout(30)
    for lon, lat in targets:
        lon = lon % (2*np.pi) - np.pi        
        x, y = wrapped_proj(lon, lat)        
        plt.plot(x,y, 'ko', markersize=6)
        
    plt.savefig("spiral_30.pdf",bbox_inches='tight', pad_inches=0)
            
    plt.figure(figsize=(10,10))        
    plot_reference_grid(proj, labels=False)    
    targets = iso_targets(2)
    for lon, lat in targets:
        lon = lon % (2*np.pi) - np.pi        
        x, y = wrapped_proj(lon, lat)        
        plt.plot(x,y, 'ko', markersize=6)        
    plt.savefig("iso_2.pdf",bbox_inches='tight', pad_inches=0)       

    plt.figure(figsize=(10,10))        
    plot_reference_grid(proj, labels=False)    
    targets = iso_targets(3)
    for lon, lat in targets:
        lon = lon % (2*np.pi) - np.pi        
        x, y = wrapped_proj(lon, lat)        
        plt.plot(x,y, 'ko', markersize=6)        
    plt.savefig("iso_3.pdf",bbox_inches='tight', pad_inches=0)       

