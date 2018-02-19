// simple pass through for geometry shader
// which will subdivide this line
layout(location=0) in vec3 position;

out vec4 g_color;

void main()
{    
    gl_Position = vec4(position.xy, 0, 0);
    g_color = vec4(1,1,1,position.z);
}