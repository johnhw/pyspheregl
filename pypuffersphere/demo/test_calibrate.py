import sys
from pypuffersphere.touch.touch_calibration import Calibration

if len(sys.argv)==2:
    calibration = sys.argv[1]
else:
    calibration = None # use newest file

calibration = Calibration(calibration)
