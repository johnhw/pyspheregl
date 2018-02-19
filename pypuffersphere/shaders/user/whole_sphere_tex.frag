#version 330

// These are sent to the fragment shader

in vec4 texCoord;      // UV coordinates of texture

layout(location=0) out vec4 color;

uniform sampler2D tex;

void main()
{   
    color = texture(tex, texCoord.xy);

    
}
