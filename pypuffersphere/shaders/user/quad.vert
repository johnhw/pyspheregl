#version 330

// These are sent to the fragment shader
out vec4 color;         // color of the point
out vec3 texCoord;      // UV coordinates of texture
out vec4 obj_id;        // id of the object

layout(location=0) in vec2 quad_vtx; // vertex position, one instance
layout(location=1) in vec4 position; // instanced position
layout(location=2) in vec2 tex_coord; // texture coords, one instance
layout(location=3) in int frame;  // animation frame 
layout(location=4) in vec4 fcolor;

uniform float scale=0.1;
uniform int obj_type;

void main()
{   
    
    vec4 pos_3d;
    float lat, lon, x, y, w, r, z;
    
    vec4 pos = vec4(quad_vtx,0,1);   

    
    
    // fwd vector is just forward
    vec3 pseudo_up= vec3(0,0,1);
    vec3 fwd = polar_to_cartesian(position.xy);
    vec3 right = cross(fwd, pseudo_up);
    vec3 up = cross(fwd, right);
    
    mat4 rotation = rotationMatrix(up, pos.x*scale);
    mat4 rotation2 = rotationMatrix(right, pos.y*scale);    
    // axis rotation disabled for now
    mat4 rotation3 = rotationMatrix(fwd, position.w * 0);    
    

    pos_3d =  rotation3 * rotation2 * rotation *  vec4(fwd, 1.0);  
        
    // convert to sphere space 
    vec2 polar = cartesian_to_polar(pos_3d.xyz);
    vec3 az = polar_to_azimuthal(polar);

    // copy texture coordinates
    texCoord.xy = tex_coord;
    texCoord.y =  texCoord.y;
    texCoord.z = frame;
    
    // positions are now in [-1, 1] normalised coordinates

    gl_Position =  vec4(az.x, az.y, 0.0, 1.0);    
    
    // fade out low vertices to avoid overdraw of the whole
    // sphere!
    if(az.z>0.95)
    {
        color = vec4(0.0,0.0,0.0,0.0);
        obj_id = vec4(0, 0, 0, 0);
    }
    else
    {
        color = fcolor;
        obj_id = vec4(obj_type/255.0, (gl_InstanceID)/255.0, (gl_InstanceID & 255)/255.0, 1);
    }
}
