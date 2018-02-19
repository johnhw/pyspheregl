from pypuffersphere.sphere import sphere
import numpy as np

refs = {'npole':[0, -np.pi/2], 'spole':[0,np.pi/2], 'gmq':[0,0], 'wmq':[np.pi/2,0], 'emq':[-np.pi/2,0], 'rmq':[np.pi,0]}
for ref,(lon,lat) in refs.items():
    print ref
    print "\t", "lon %4.1f\tlat %4.1f" % (np.degrees(lon),  np.degrees(lat))
    x,y,z = sphere.polar_to_cart(lon, lat)
    print "\t", "x %4.1f\ty %4.1f\tz %4.1f" % (x,y,z)
    
    # verify reverse is OK
    assert(np.allclose([lon, lat], sphere.cart_to_polar(x,y,z)))

    az_x, az_y = sphere.polar_to_az(lon, lat)
    print "\t", "az_x %4.1f\taz_y %4.1f" % (az_x,az_y)

    assert(np.allclose([lon, lat], sphere.az_to_polar(az_x,az_y)))

    raw_az_theta, raw_az_r = sphere.polar_to_rawaz(lon, lat)
    
    print "\t", "rawaz_th %4.1f\trawaz_r %4.1f" % (np.degrees(raw_az_theta),raw_az_r)
    assert(np.allclose([lon, lat], sphere.rawaz_to_polar(raw_az_theta,raw_az_r)))
    