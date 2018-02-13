#version 330 core

// These are sent to the fragment shader
out vec2 texCoord;      // UV coordinates of texture
out float alpha;        // Mask to remove out of circle texture
out float illumination; // brightness of point
out vec2 sphere;        // polar sphere coords
layout(location=0) in vec2 position;
uniform float rotate, tilt;

#define M_PI 3.1415926535897932384626433832795

vec2 az_to_polar(vec2 az)
{
    vec2 latlon;
    latlon.x = -sqrt((az.x*az.x)+(az.y*az.y)) * M_PI + M_PI/2;
    latlon.y = atan(az.y,az.x);
    return latlon;    
}

vec3 spherical_to_cartesian(vec2 latlon)
{
    // Convert a lat, lon co-ordinate to an a Cartesian x,y,z point on the unit sphere.
    vec3 cart;
    float lon, lat;
    lat = latlon.x;
    lon = latlon.y;
    lat += M_PI/2;
    float st = sin(lat);
    cart.x = cos(lon) * st;
    cart.y = sin(lon) * st;
    cart.z = -cos(lat);    
    return cart;
}   

// From https://gist.github.com/neilmendoza/4512992
mat4 rotationMatrix(vec3 axis, float angle)
{
    axis = normalize(axis);
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    
    return mat4(oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s,  oc * axis.z * axis.x + axis.y * s,  0.0,
                oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,           oc * axis.y * axis.z - axis.x * s,  0.0,
                oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s,  oc * axis.z * axis.z + c,           0.0,
                0.0,                                0.0,                                0.0,                                1.0);

                
}

void main()
{
    // convert screen co-ordinates (in aximuthal) to polar
    vec2 polar = az_to_polar(position);
    sphere = polar;

    // apply longitude rotation 
    polar.y -= rotate;
    
    // compute the cartesian coordinate
    vec4 pos = vec4(spherical_to_cartesian(polar),1);

    // rotate by the tilt
    pos = rotationMatrix(vec3(1,0,0), -tilt) * pos;
    
    // set the position
    gl_Position.xzy = pos.xyz;


    // cut off all portions outside of the circle and at the rear of the sphere
    float radius = sqrt((position.x*position.x)+(position.y*position.y));
    alpha = 1.0-smoothstep(0.8,0.95, radius);    
    alpha *= smoothstep(0.0, 0.1, gl_Position.z);

    // illuminate
    illumination = gl_Position.z;
    
    gl_Position.w = 1;
    // tex-coords are just 0-1, 0-1
    texCoord = position / 2.0 + 0.5;
}