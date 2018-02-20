#version 330 core
// plain square
layout(location=0) out vec4 fcolor;
in vec4 color;
in vec2 polar;
in float bar_bright;

void main()
{
    // white blob
    vec2 pt = gl_PointCoord - vec2(0.5, 0.5);
    float radius = length(pt);
    float ring_radius = length(pt)-0.3;

    float bright = exp(-(ring_radius*ring_radius)*3000) + exp(-(radius*radius)*200)*bar_bright;
    bright += bar_bright * (exp(-pt.x*pt.x*20000.0) + exp(-pt.y*pt.y*20000.0));
    float glow = bright * 0.5;
    fcolor = vec4(color.r+glow,color.g+glow,color.b+glow, color.a * bright);
    
}
