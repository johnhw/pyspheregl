#version 330 core
// plain square
layout(location=0) out vec4 fcolor;
in vec4 color;
in vec2 polar;

void main()
{
    // white blob
    vec2 pt = gl_PointCoord - vec2(0.5, 0.5);
    float radius = length(pt);
    float ring_radius = length(pt)-0.3;

    float bright = exp(-(ring_radius*ring_radius)*500) + exp(-(radius*radius)*200);
    bright += exp(-pt.x*pt.x*20000.0) + exp(-pt.y*pt.y*20000.0);
    fcolor = vec4(color.r,color.g,color.b, color.a * bright);
    
}
