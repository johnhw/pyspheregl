#version 330

// These are sent to the fragment shader
out vec4 color;         // color of the point
out vec3 texCoord;      // UV coordinates of texture
out vec4 obj_id;        // id of the object

in vec2 quad_vtx; // vertex position, one instance
in vec3 position; // instanced position
in vec3 up_vector; // instanced up vector
in vec2 tex_coord; // texture coords, one instance
in int frame;  // animation frame 
in vec4 fcolor;

uniform float scale=0.1;
uniform int obj_type;
uniform vec4 quat;

vec3 quat_rotate_vertex(vec3 v, vec4 q)
{ 
  return v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v);
}

void main()
{   
    
    vec4 pos_3d;
    float lat, lon, x, y, w, r, z;
    vec4 pos = vec4(quad_vtx,0,1);   
    
    vec3 pseudo_up = normalize(up_vector);
    vec3 fwd = polar_to_cartesian(position.xy);
    
    fwd = quat_rotate_vertex(fwd, quat);
    vec3 right = cross(fwd, pseudo_up);
    //right = (rotationMatrix(fwd, position.w * 0) * vec4(right,1)).xyz;
    vec3 up = cross(fwd, right);
    
    pos_3d.xyz = pos.x * right * scale + pos.y * up * scale + fwd;

    // convert to sphere space 
    vec2 polar = cartesian_to_polar(pos_3d.xyz);
    vec3 az = polar_to_azimuthal(polar);

    // copy texture coordinates
    texCoord.xy = tex_coord;    
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
