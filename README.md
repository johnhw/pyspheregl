# pyspheregl
Python/Pyglet code for using rendering on spherical displays.

Dependencies:


# Module launching

## Quick demo of simulator
* `python -m pyspheregl.demo.world --test`

* [Left click] rotate sphere
* [SHIFT] lock sphere rotation
* [Right click] simulate OSC message for touch

### **touch broadcast/monitor**

        python -m pyspheregl.touch.touch_zmq monitor --full_trace

Will try to load `calibration.py` from the current directory as the calibration

    Broadcast on the ZMQ PUB stream on the given TCP port.

    Usage:       touch_zmq.py monitor [PORT] [ZMQ_PORT] [IP] [MSG] [TIMEOUT] [FULL_TRACE] [CONSOLE] [NO_CALIBRATION]
                touch_zmq.py monitor [--port PORT] [--zmq-port ZMQ_PORT] [--ip IP] [--msg MSG] [--timeout TIMEOUT] [--full-trace FULL_TRACE] [--console CONSOLE] [--no-calibration NO_CALIBRATION]

* `--calibration <fname>` specify a specific calibration file (otherwise use the latest one in `calibrations/`)
* `--full_trace` Show a full trace of activity, including an ASCII sphere view
* `--no_calibration` Don't use touch calibration
* `--console=False` Don't show the console view

### Calibration
To run the calibration process you must first run `touch_zmq.py` with `--no_calibration` and then run the calibration using `calibrate.py`. Once complete you must then restart `touch_zmq` for the calibration to take effect.

`python -m pyspheregl.touch.calibrate`

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


## Overall structure

* sphere_sim provides spherical drawing context
* make_viewer will construct a drawing context object
* it takes callbacks to render content (`draw_fn`), update (`tick_fn`), receive touches (`touch_fn`)
* the context runs in an pyglet event loop

### Touch

### From TUIO to ZMQ
* Touch is received by the ZMQ rebroadcaster `touch_zmq`. 
* The raw TUIO touch is converted to lon, lat format
* Calibration is applied (if enabled) before the messages are sent over ZMQ on TCP port 4000, as PUB stream called "TOUCH"
* `touch_zmq` shows the live touch status while running
* The output over ZMQ is calibrated touch points, with low latitude touches filtered out
    * Touches below the lowest target calibrated successfully are removed

### Touch manager
* Messages are received by the touch manager `touch_manager`
* This takes the lon,lat positions of fingers and creates touch events: UP, DOWN, DRAG
* These are passed to the sphere simulator to be passed to client code, using `touch_fn`
* Touches are clustered to create cluster events for closely spaced fingers: `CLUSTER_UP`, `CLUSTER_DOWN`, `CLUSTER_DRAG`, `CLUSTER_LEAVE`, `CLUSTER_JOIN`


### Feedback buffer
* When rendering, if a shader writes integers to COLOR_ATTACHMENT1, then these values
are used to provide pixel perfect touch feedback.
* Shaders that want to use touch feedback need to have draw calls surrounded using `with sphere_sim.TouchFeedback()` to enable writing to the second color attachment
* The results of writing to this color attachment are copied into a numpy array each frame
    * This is done internally inside sphere_sim, which prepares an FBO for this process
* The touch manager queries this numpy array and augments each incoming touch with the tag of the pixel underneath

## Raw TUIO format
* Touch is received over OSC in the TUIO format. 
* Messages are received from /tuio/2Dcur, by default on port 3333
* Valid messages are "ALIVE", "FSEQ" and "SET"
* Coordinates are as "TUIO" coordinates above

## Rendering
* All rendering is to textures, which are eventually either mapped to a full screen quad (for real spherical display) or onto a simulated spherical geometry (for the simulator)
* There are two color buffers: 
    * COLOR_ATTACHMENT0 is a standard RGBA color buffer (the "color buffer")
    * COLOR_ATTACHMENT1 is an integer, single channel buffer (GL_RED_INTEGER/GL32UI) which is used to store the ids of objects rendered on the screen. (the "touch buffer")

* Shaders using touch feedback should have:

    layout(location=0) out vec4 frag_color;
    layout(location=1) out uint obj_id;

* Locations 0 and 1 are bound to the respective framebuffers targets in sphere_sim automatically

    
