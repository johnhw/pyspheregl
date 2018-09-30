#version 330

// These are sent to the fragment shader

in vec4 texCoord;                // UV coords of texture
in vec2 flat_position;
layout(location=0) out vec4 color;
uniform vec4 quat;
uniform sampler2D tex;

vec2 azimuthal_to_polar(vec2 az)
{
    vec2 lonlat;
    lonlat.x = -atan(-az.y, az.x);
    lonlat.y = -(sqrt((az.x * az.x) + (az.y * az.y)) * M_PI - M_PI / 2);
    return lonlat;
}


void main()
{
    vec2 screen = (texCoord.xy);

    // convert to azimuthal
    vec2 polar = azimuthal_to_polar(flat_position);
    vec3 cart = polar_to_cartesian(polar);
    vec4 inv_quat = quat;
    inv_quat.x = -quat.x;
    inv_quat.y = -quat.y;
    cart = quat_rotate_vertex(cart, inv_quat);
    vec3 az = cartesian_to_azimuthal(cart);
    color = texture(tex, (az.xy+1) / 2.0);
}