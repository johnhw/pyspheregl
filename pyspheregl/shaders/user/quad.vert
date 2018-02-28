#version 330

// These are sent to the fragment shader
out vec4 color;         // color of the point
out vec3 texCoord;      // UV coordinates of texture
flat out int obj_id;        // id of the object

in vec2 quad_vtx; // vertex position, one instance
in vec3 position; // instanced position
in vec3 up_vector; // instanced up vector
in vec2 tex_coord; // texture coords, one instance
in int frame;  // animation frame 
layout (location=2) in vec4 fcolor;

uniform float scale=0.1;

uniform vec4 quat;

vec3 planar_sphere_transform(vec3 position, vec3 up_vector, vec2 vertex, vec4 quat);

void main()
{   
    
    vec4 pos_3d;
    float lat, lon, x, y, w, r, z;
    
    vec3 az = planar_sphere_transform(polar_to_cartesian(position.xy), up_vector, quad_vtx*scale, quat);

    // copy texture coordinates
    texCoord.xy = tex_coord + fcolor.x;    
    texCoord.z = frame;
    
    // positions are now in [-1, 1] normalised coordinates
    gl_Position =  vec4(az.x, az.y, 0.0, 1.0);    
    
    // fade out low vertices to avoid overdraw of the whole
    // sphere!
    if(az.z>0.95)
    {
        color = vec4(0.0,0.0,0.0,0.0);
        obj_id = 0;
    }
    else
    {
        color = fcolor;
        obj_id = TOUCH_ID;
    }
   
}
