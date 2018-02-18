#version 330 core

in float f_brightness;
layout(location=0) out vec4 color;

void main()
{
    // white blob
    color = vec4(1,1,1,f_brightness);
}