
// These are sent to the fragment shader
out vec2 texCoord;      // UV coordinates of texture

layout(location=0) in vec2 position;
layout(location=1) in vec2 tex_coord;

void main()
{
    gl_Position.xy = position;
    texCoord = tex_coord;
}