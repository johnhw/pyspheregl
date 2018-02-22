layout(location=0) in vec2 position;
layout(location=1) in vec4 color;
layout(location=2) in float size;

uniform vec4 constant_color;
uniform float constant_size;

out vec4 f_color;

uniform vec4 quat;


void main()
{    
    vec3 cart = polar_to_cartesian(position.xy);
    cart = quat_rotate_vertex(cart, quat);
    gl_Position = vec4(cartesian_to_azimuthal(cart).xy, 0, 1);
    f_color = constant_color +color ;    
    gl_PointSize = constant_size + constant_size;
}