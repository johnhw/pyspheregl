#version 330 core

in vec4 f_color;
in float radius_cutoff;
layout(location=0) out vec4 frag_color;

void main()
{    
    vec2 pt = gl_PointCoord - vec2(0.5, 0.5);
    float radius = length(pt);
    float w = fwidth(radius);
    float density = 1-smoothstep(0.5-w, 0.5, radius);
    
    float inner_density = 1-smoothstep(0.5*radius_cutoff-w, 0.5*radius_cutoff, radius);
    
    
    frag_color = f_color;
    frag_color.a = density-inner_density;
    
}