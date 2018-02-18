
// These are sent to the fragment shader
out vec2 flat_position; // position in flat coordinates
out vec2 az_position;   // position in azimuthal coordinates
out vec3 cart_position; // position in cartesian coordinates
out vec2 polar_position;// position in spherical coordinates
out vec4 texCoord;      // UV coordinates of texture

layout(location=0) in vec2 quad_vtx;

//uniform mat4 correction;

vec2 az_to_polar(vec2 az);
vec3 polar_to_cartesian(vec2 latlon);

void main()
{   
    
    // copy texture coordinates
    texCoord.xy = (quad_vtx+1)/2;
    texCoord.y = 1 - texCoord.y;

    flat_position = quad_vtx.xy;
    az_position = vec2(atan(flat_position.y, flat_position.x), length(flat_position));
    polar_position = az_to_polar(flat_position);
    cart_position = polar_to_cartesian(polar_position);
    
    // positions are now in [-1, 1] normalised coordinates
    // apply any correction afterwards 
    // (to compensate for sphere not being perfectly aligned with coords)
    gl_Position = vec4(flat_position.x, flat_position.y, 0.0, 1.0);    
    
    
}
