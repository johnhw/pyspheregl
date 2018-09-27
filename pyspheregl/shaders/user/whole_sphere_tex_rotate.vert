uniform vec4 quat;

// These are sent to the fragment shader
out vec2 flat_position;
out vec2 az_position;
out vec3 cart_position;
out vec2 polar_position;
out vec4 texCoord;

layout(location=0) in vec2 quad_vtx;

//uniform mat4 correction;

vec2 az_to_polar(vec2 az);
vec3 polar_to_cartesian(vec2 latlon);

vec2 azimuthal_to_polar(vec2 az)
{
    vec2 lonlat;
    lonlat.x = -atan(-az.y, az.x);
    lonlat.y = -(sqrt((az.x * az.x) + (az.y * az.y)) * M_PI - M_PI / 2);
    return lonlat;
}

void main()
{
    // Copy the texture coordinates
    texCoord.xy = (quad_vtx+1.0)/2;
    texCoord.y =  texCoord.y;
    flat_position = quad_vtx.xy;

    // Convert to azimuthal
    vec2 polar = azimuthal_to_polar(flat_position);

    vec3 cart = polar_to_cartesian(polar);
    
    vec4 inv_quat = quat;
    
    inv_quat.x = -quat.x;
    inv_quat.y = -quat.y;
    
    cart = quat_rotate_vertex(cart, inv_quat);
    
    vec3 az = cartesian_to_azimuthal(cart);
    
    texCoord.xy = (az.xy + 1.0) / 2.0;

    gl_Position = vec4(flat_position.x, flat_position.y, 0.0, 1.0); 
    // gl_Position = vec4(az.xy, 0.0, 1.0);
}
