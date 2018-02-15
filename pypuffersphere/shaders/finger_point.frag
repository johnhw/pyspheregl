#version 330 core

layout(location=0) out vec4 color;
void main()
{
    // just magenta
    float b = length(gl_PointCoord);
    color = vec4(1,0,1,1);
    
}