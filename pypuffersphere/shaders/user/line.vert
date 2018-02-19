// simple pass through for geometry shader
// which will subdivide this line
layout(location=0) in vec2 position;
layout(location=1) in vec4 color;

uniform vec4 constant_color;

out vec4 g_color;
void main()
{    
    gl_Position = vec4(position, 0, 0);
    g_color = constant_color + color;
}