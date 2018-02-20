# pypuffersphere
Python/Pyglet code for using rendering on the PufferSphere

Dependencies:


# Module launching

## Quick demo of simulator
* `python -m pypuffersphere.demo.world --test`

* [Left click] rotate sphere
* [SHIFT] lock sphere rotation
* [Right click] simulate OSC message for touch

### **touch broadcast/monitor**
`python -m pypuffersphere.sphere.touch_zmq monitor` 
Will try to load `calibration.py` from the current directory as the calibration

    Broadcast on the ZMQ PUB stream on the given TCP port.

    Usage:       touch_zmq.py monitor [PORT] [ZMQ_PORT] [IP] [MSG] [TIMEOUT] [FULL_TRACE] [CONSOLE] [NO_CALIBRATION]
                touch_zmq.py monitor [--port PORT] [--zmq-port ZMQ_PORT] [--ip IP] [--msg MSG] [--timeout TIMEOUT] [--full-trace FULL_TRACE] [--console CONSOLE] [--no-calibration NO_CALIBRATION]

* `--calibration <fname>` specify a specific calibration file (otherwise use the latest one in `calibrations/`)
* `--full_trace` Show a full trace of activity, including an ASCII sphere view
* `--no_calibration` Don't use touch calibration
* `--console=False` Don't show the console view

### Calibration
`python -m pypuffersphere.touch.calibrate`

        usage: calibrate.py [-h] [--interleave] [--dummy] [--noprocess]
                                    [-n NTARGETS] [-r REPETITIONS] [-l MINLATITUDE]
                                    [-t TOUCHTIME] [--test]

        Run a calibration sequence on the sphere.

        optional arguments:
        -h, --help            show this help message and exit
        --interleave, -i      Run the repeats immediately after each other, rather
                                than multiple complete runs.
        --dummy               Ignore all input; just run through the targets and
                                generate no output file.
        --noprocess           Disable post-processing of the calibration file; just
                                record the data. You can run process_calibration.py
                                afterwards to process the calibration data.
        -n NTARGETS, --ntargets NTARGETS
                                Total number of targets to run (default=100)
        -r REPETITIONS, --repetitions REPETITIONS
                                Number of repetitions per target (default=3)
        -l MINLATITUDE, --minlatitude MINLATITUDE
                                Minimum southern latitude to include, in degrees
                                (default=40). 0=nothing below equator, 90=to pole
        -t TOUCHTIME, --touchtime TOUCHTIME
                                Touch time per target, in seconds (default=0.4)
        --test                Run in sphere simulator mode

# Coordinate systems

## Reference points
* North pole `npole` 
* South pole `spole` 
* Greenwich Meridian at equator `gmq` 
* 90W of Greenwich Meridian at equator `wmq` 
* 90E of Greenwich Meridian at equator `emq` 
* 180E of Greenwich Meridian at equator `rmq` 

## Default drawing
* Centre at vector extending from sphere centre
* Up vector towards `npole`
* Pixel/vertex space equiangular (one pixel texture subtends equal angle at any location)

## Spherical `polar`
* **Always** in the form `(lon,lat)`
    * **NEVER** in the form `(lat, lon)`!!!
    * longitude (around equator), 
    * latitude (towards away/from equator)
* Computed and stored in radians, except for human display (debug print out)
* latitude -90  is top of sphere `npole`
* latitude 90  is base of sphere `spole`
* longitude 0 is facing side with projector control panel, will be meridian if globe shown
    * +ve longitude goes West (left if facing longitude 0)
    * -ve longitude goes East (right if facing longitude 0)

* `[x, pi/2]` = `npole`
* `[x, -pi/2]` = `spole`
* `[0,0]` = `gmq`
* `[pi/2, 0]` = `wmq`
* `[-pi/2, 0]` = `emq`
* `[pi,0]` = `rmq`

## Cartesian `cart`
* Unit length vector XYZ representing point on sphere
* `[0,0,-1]` = `npole`
* `[0,0,1]` = `spole`
* `[1,0,0]` = `gmq`
* `[0,1,0]` = `wmq`
* `[0,-1,0]` = `emq`
* `[-1,0,0]` = `rmq`

## Extended Cartesian `xcart`
* As Cartesian, but vec4
    * length of vector represents scale of objects
    * w component represents rotation about z axis, in radians

## TUIO `tuio`
* x,y coordinates in [0,1]    
* `x = 2*pi*lon`
* `y = pi*lat - 0.5*pi`

## Azimuthal (polar equidistant) `raw_az`
* radius, theta coordinates
* radius = (pi/2 - latitude) / pi, in range [0,1]
* theta = longitude
* discontinuity at base of sphere


## Device native azimuthal `az`
* x,y in [-1, 1] 
* 0,0 = centre = top of sphere
* circle at radius = 1 = bottom of sphere
* `x = cos(radius) * theta `
* `y = sin(radius) * theta`
* `[0,0]` = `npole`
* `[1,0]` = `spole`
* `[0.5,0]` = `gmq`
* `[0,0.5]` = `wmq`
* `[0,-0.5]` = `emq`
* `[-0.5,0]` = `rmq`

## Corrected device native pixel format `pixel`
* Device native azimuthal scaled by resolution, but tweaked for partial sphere coverage
* For example, 1600x1600 sphere has native resolution 2560x1600
* Sphere is rendered as 1920x1920 image centered in that box to compensate for lens distortion

## Quaternion `quat`
* Represents rotation from `gmq` as a single quaternion

## Toroidal `torus`
* major [0,1], minor [0,1]
* minor axis runs north/south 
* major axis runs east/west 
* configurable portion of minor axis represented on spherical segment
