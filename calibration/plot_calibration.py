
    
def gp_offset_shading(calibration, gp_x, gp_y, best_s):
    """Plot the GP offset model for x and y, after removing the constant correction"""
    proj = proj_wrapper(pyproj.Proj("+proj=robin"))
    plt.figure(figsize=(9,4))
    plot_reference_grid(pyproj.Proj("+proj=robin"), labels=False)    
    xs, ys, zs = [], [], []
    us, vs = [], []
    test_pts = sphere.spiral_layout(2000)
    for lon, lat in test_pts:
        
        # gp corrected lon, lat
        az_x,az_y = sphere.polar_to_az(lon, lat)
        tinput = [az_x, az_y]
        xc = gp_x.predict(tinput)
        yc = gp_y.predict(tinput)
        lonc, latc = sphere.az_to_polar(az_x+xc, az_y+yc)
        # constant corrected lon, lat
        lons, lats = polar_adjust(lon, lat, best_s)
        
        # compute offset from constant corrected
        px,py = proj(lon, lat)
        px_c,py_c = proj(lonc, latc)
        px_s,py_s = proj(lons, lats)
        d = (px_s-px_c)**2 + (py_s-py_c)**2
        xs.append(px)        
        ys.append(py)
        
        if np.sqrt(d)<6e7:            
            us.append(px_s-px_c)
            vs.append(py_s-py_c)
        else:
            us.append(0)
            vs.append(0)
        zs.append(np.sqrt(d))
    
    
    xi = np.linspace(np.min(xs), np.max(xs), 500)
    yi = np.linspace(np.min(ys), np.max(ys), 500)
    #zi = matplotlib.mlab.griddata(xs, ys, zs, xi, yi, interp='linear')
    
    
    #levels = np.linspace(np.min(zi), np.max(zi), 30)
    #plt.contourf(xi, yi, zi, cmap="bone", levels=levels)
    plt.quiver(xs,ys,us,vs,scale=3e7,width=5e-4)
    #plt.colorbar()
    

    

def error_shading(calibration, fn):
    """Plot the GP offset model for x and y, after removing the constant correction"""
    proj = proj_wrapper(pyproj.Proj("+proj=robin"))    
    plot_reference_grid(pyproj.Proj("+proj=robin"))    
    xs, ys, zs = [], [], []
    
    for ix, row in calibration.iterrows():
        tlon, tlat = row["target_lon"], row["target_lat"]
        lon, lat = row["touch_lon"], row["touch_lat"]
        # compute offset from constant corrected
        px,py = proj(lon, lat)
        lonc, latc = fn(lon, lat)        
        d = np.degrees(sphere.spherical_distance((tlon, tlat), (lonc, latc)))
        xs.append(px)        
        ys.append(py)
        zs.append(d)
    xi = np.linspace(np.min(xs), np.max(xs), 500)
    yi = np.linspace(np.min(ys), np.max(ys), 500)
    zi = matplotlib.mlab.griddata(xs, ys, zs, xi, yi, interp='linear')
    #xr, yr = np.meshgrid(xi,yi)
    #iv = scipy.interpolate.interp2d(xs,ys,zs,kind='cubic')
    #zi = iv(xi, yi)
    #zi = scipy.interpolate.griddata((np.array(xs).flatten(),np.array(ys).flatten()),np.array(zs).flatten(),(xr,yr), method='cubic')
    levels = np.linspace(np.min(zi), np.max(zi), 30)
    plt.contourf(xi, yi, zi, cmap="bone", levels=levels, vmin=0, vmax=9)
    plt.colorbar()
            
            
            
   
          
    
def gp_n_test(train_set, test_set, max_n, reps=10):
    ds = []
    ns = []
    for n in range(5,max_n-5):        
        gp_x, gp_y = train_gp(train_set, n)
        d = []
        for j in range(reps):
            d += error_distribution(test_set, lambda x,y: gp_adjust(x,y,gp_x,gp_y))
        ds.append(d)        
        ns.append(n)
    return ds, ns
    
    
    
def gp_offset_plot(gp_x, gp_y):
    plt.figure(figsize=(9,4))
    plt.clf()
    proj = pyproj.Proj("+proj=robin")
    plot_reference_grid(proj, labels=True)
    plot_proj = proj_wrapper(proj)
    for ix,row in calibration.iterrows():
        target = [row["touch_lon"], row["touch_lat"]]
        corr_touch_lon, corr_touch_lat = gp_predict(gp_x, gp_y, row["touch_az_x"], row["touch_az_y"])                        
        xp, yp = plot_proj(row["target_lon"],row["target_lat"])
        xr, yr = plot_proj(row["touch_lon"],row["touch_lat"])
        xq, yq = plot_proj(corr_touch_lon,corr_touch_lat)
    
        plt.plot([xp,xq],[yp,yq],'k-')        
        plt.plot([xp,xr],[yp,yr],'k', alpha=0.1)    


def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
        
        
import matplotlib.lines as mlines
def plot_correction_models(calibration, correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y):
    plt.figure(figsize=(9,4))
    plt.clf()
    proj = pyproj.Proj("+proj=robin")
    plot_reference_grid(proj, labels=False)
    plot_proj = proj_wrapper(proj)
    for ix,row in calibration.iterrows():
        def plot_corrected(corrector_fn, *args, **kwargs):
            lon, lat = corrector_fn(row["touch_lon"], row["touch_lat"])
            tx, ty = plot_proj(row["target_lon"], row["target_lat"])
            x, y = plot_proj(lon, lat)
            thresh = 1e6
            if abs(x-tx)<thresh and abs(y-ty)<thresh:
                plt.plot([tx,x], [ty,y], *args, **kwargs)

        plot_corrected(lambda x,y:polar_adjust(x,y,s=correction_factor), 'k')
        plot_corrected(lambda x,y:polar_adjust(x,y,1), 'k', alpha=0.2)
        plot_corrected(lambda x,y:quadratic_polar_adjust(x,y,quadratic_coeff), 'r')
        plot_corrected(lambda x,y:cubic_polar_adjust(x,y,cubic_coeff), 'm')
        plot_corrected(lambda x,y:gp_adjust(x,y,gp_x,gp_y), 'g')
        
    plt.legend(handles=[mlines.Line2D([], [], color='k', alpha=0.2, linestyle="-",label='Original offset'),
    mlines.Line2D([], [], color='k', linestyle="-",label='Constant corrected'),
    mlines.Line2D([], [], color='r', linestyle="-",label='Quadratic corrected'),
    mlines.Line2D([], [], color='m', linestyle="-",label='Cubic corrected'),
    mlines.Line2D([], [], color='g', linestyle="-",label='GP corrected'),    
    ], frameon=False, prop={'size':5})



def plot_shading(calibration,  correction_factor, cubic_coeff, quadratic_coeff, gp_x, gp_y):
    plt.figure(figsize=(10,4))
    error_shading(calibration, lambda x,y: polar_adjust(x,y,1))        
    plt.savefig("uncorrected_error.pdf",bbox_inches='tight', pad_inches=0)
    plt.figure(figsize=(10,4))
    error_shading(calibration, lambda x,y:polar_adjust(x,y,s=correction_factor))
    plt.savefig("constant_error.pdf",bbox_inches='tight', pad_inches=0)
    plt.figure(figsize=(10,4))
    error_shading(calibration, lambda x,y:quadratic_polar_adjust(x,y,quadratic_coeff))
    plt.savefig("quadratic_error.pdf",bbox_inches='tight', pad_inches=0)
    plt.figure(figsize=(10,4))
    error_shading(calibration, lambda x,y:cubic_polar_adjust(x,y,cubic_coeff))
    plt.savefig("cubic_error.pdf",bbox_inches='tight', pad_inches=0)
    plt.figure(figsize=(10,4))
    error_shading(calibration, lambda x,y:gp_adjust(x,y,gp_x,gp_y))
    plt.savefig("gp_error_shading.pdf",bbox_inches='tight', pad_inches=0)
    
    
def error_labels(calibration, uncorrected_rmse, constant_rmse, quadratic_rmse, cubic_rmse, gp_rmse):
    x = 0.65
    y = 0.04
    plt.figtext(x, y, "RMSE uncorrected: %.2f degrees" % uncorrected_rmse, fontdict={"size":5})
    y += 0.03
    
    plt.figtext(x,y,"RMSE constant: %.2f degrees" % constant_rmse, fontdict={"size":5})
    y += 0.03
    plt.figtext(x,y,"RMSE quadratic: %.2f degrees" % quadratic_rmse, fontdict={"size":5})
    y += 0.03
    plt.figtext(x,y,"RMSE cubic: %.2f degrees" % cubic_rmse, fontdict={"size":5})
    y += 0.03
    plt.figtext(x,y,"RMSE GP: %.2f degrees" % gp_rmse, fontdict={"size":5})    
    
    
    

       
def plot_gp_n_test(train_calibration, test_calibration)
    ds, ns = gp_n_test(train_calibration, test_calibration)
    ds = np.array(ds)
    plt.figure()
    seaborn.tsplot(ds.transpose(), time=ns)
    plt.xlabel("Number of training points")
    plt.ylabel("RMS Error (degrees)")    
    plt.savefig("gp_error_n.pdf",bbox_inches='tight', pad_inches=0)
            