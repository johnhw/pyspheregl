#version 330 core
// plain square
layout(location=0) out vec4 color;
in float brightness;

void main()
{
    // white blob
    vec2 pt = gl_PointCoord - vec2(0.5, 0.5);
    float radius = length(pt);
    float ring_radius = length(pt)-0.3;
    float bright = exp(-(ring_radius*ring_radius)*500) + exp(-(radius*radius)*200);
    color = vec4(1,1,1,bright * brightness);
}