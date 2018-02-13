#version 330 core

// These are sent to the fragment shader
out vec2 texCoord;      // UV coordinates of texture

layout(location=0) in vec2 position;

void main()
{
    gl_Position.xy = position;
    texCoord = position;
}