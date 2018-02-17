
#version 330
// These are sent to the fragment shader
out vec2 texCoord;      // UV coordinates of texture

layout(location=0) in vec2 position;
layout(location=1) in vec2 tex_coord;

void main()
{
    gl_Position = vec4(position,0,1);        
    //texCoord = vec2(1-tex_coord.y, 1-tex_coord.x);
    texCoord = vec2(tex_coord.x, 1-tex_coord.y);
}