// This is old code and may not be useful in its current form!

#define M_PI 3.1415926535897932384626433832795
// resolution of the screen
uniform float resolution;

// rotation and tilt of the torus in radians
uniform float rotate, tilt;
// portion of the sphere used, in [0,1] range
uniform float lat_range, lat_offset;
// position of the object
uniform float tx, ty, scale;

uniform float torus_scale;

vec2 to_torus(vec2 pos)
{
    // flat torus coordinates to true torus coordinates
    // compute the torus location of these points
    float sinx, cosx;
    float px;
    px = pos.x;        
    float angle;
    float torus_mod;
    torus_mod = M_PI*2.0*torus_scale;
    angle = mod((px * M_PI*2.0 - tilt)*torus_scale, torus_mod) - torus_mod/2.0;
    //angle = px * M_PI*2. - tilt;
    
    // latitude is computed from the x position
    sinx = sin(angle)/2.0;
    cosx = cos(angle)/2.0;        
    
    return vec2(sinx, cosx);
}

vec2 to_sphere(vec2 torus, vec2 pos)
{
   // Torus coordinates  to sphere coordinates
   float lat, lon;
   float sinx = torus.x;
   float cosx = torus.y;
   
    lat = (sinx) * M_PI * (lat_range)+lat_offset*M_PI;
    // longitude from the y position
    // +0.005*cosx adds just a little curve at the top and bottom of the torus
    // which looks nice
    lon = (pos.y + 0.005*cosx) * M_PI * 2. -rotate;
    return vec2(lat, lon);
}

vec2 to_azimuthal(vec2 sphere)
{
    ///// COORDINATES IN [lat,lon] SPHERE SPACE

    // standard projection from lat, lon to azimuthal co-ordinates
    // (the native co-ordinates of the PufferSphere)
    // effectively we draw a point on a circle with a radius given by lat
    // and an angle given by lon, centered on the centre of the screen
    float r,w,x,y;
    r = (M_PI/2.0-sphere.x)/M_PI;      
    w = resolution/2.0;
    x = w + r * w * cos(sphere.y);
    y = w - r * w * sin(sphere.y);
    return vec2(x,y);
}

float torus_fade(vec2 torus, float k, float offset)
{
    float c_int = smoothstep(-k+offset, k+offset, torus.y);
    float c = mix(0.0,1.0, c_int);
    return c;
}


float torus_fade(vec2 torus, float k)
{
    float c_int = smoothstep(-k, k, torus.y);
    float c = mix(0.0,1.0, c_int);
    return c;
}

vec2 t_transform_xy(vec4 pos, float xsc, float ysc)
{
    vec2 torus_centre = to_torus(vec2(tx,ty));
    // adjust aspect scaling for distortion across the torus surface
    float xscale = sqrt(2.0)/(max(torus_centre.y*2.0, 0.3)) / torus_scale;
    return vec2(pos.x*scale*xscale*xsc+tx, pos.y*scale*ysc+ty);
}

vec2 t_transform(vec4 pos, float sc)
{
    vec2 torus_centre = to_torus(vec2(tx,ty));
    // adjust aspect scaling for distortion across the torus surface
    float xscale = sqrt(2.0)/(max(torus_centre.y*2.0, 0.3)) / torus_scale;
    return vec2(pos.x*scale*xscale*sc+tx, pos.y*scale*sc+ty);
}

vec2 t_transform(vec4 pos)
{
    return t_transform(pos, 1.0);
}


float front_visible(float fade)
{
    return smoothstep(0.55, 0.65, fade);
}
