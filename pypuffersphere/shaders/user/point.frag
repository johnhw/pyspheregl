#version 330 core

in vec4 f_color;
layout(location=0) out vec4 frag_color;

void main()
{    
    vec2 pt = gl_PointCoord - vec2(0.5, 0.5);
    float radius = length(pt);
    float w = fwidth(radius);
    float density = smoothstep(0.5-w, 0.5, radius);
    frag_color = f_color;
    frag_color.a = 1-density;
    
}