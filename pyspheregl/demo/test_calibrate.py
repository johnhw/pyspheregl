import sys
import matplotlib.pyplot as plt
import numpy as np
from ..touch.touch_calibration import Calibration

if __name__=="__main__":

    if len(sys.argv)==2:
        calibration = sys.argv[1]
    else:
        calibration = None # use newest file

    calibration = Calibration(calibration)

    cal = calibration.calibration
    plt.figure()
    plt.plot(np.degrees(cal["target_lon"]), np.degrees(cal["target_lat"]), 'ro')
    plt.plot(np.degrees(cal["touch_lon"]), np.degrees(cal["touch_lat"]), 'go')
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Targets")
    plt.figure()
    for ix, row in cal.iterrows():
        lon, lat = row["target_lon"], row["target_lat"]
        tlon, tlat = row["touch_lon"], row["touch_lat"]
            
        
        lonc, latc = calibration.adjust(tlon, tlat)
        plt.plot(np.degrees(lon), np.degrees(lat), 'ro')     
        plt.plot(np.degrees(lonc), np.degrees(latc), 'gx')
        plt.plot([np.degrees(lonc),np.degrees(tlon)], [np.degrees(latc), np.degrees(tlat)], 'b')
        
    lons = np.random.uniform(-np.pi, np.pi, (30,))
    lats = np.random.uniform(-np.pi/4, np.pi/2, (30,))
    for lon, lat in zip(lons, lats):
        lonc, latc = calibration.adjust(lon, lat)
        plt.plot([np.degrees(lon), np.degrees(lonc)], [np.degrees(lat), np.degrees(latc)], 'b')
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Correction")    
    plt.show()
    