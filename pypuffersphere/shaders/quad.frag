#version 330 core

// from the vertex shader
in vec2 texCoord;
uniform sampler2D quadTexture;

void main(void)
{          
     // look up the texture at the UV coordinates, with the given animation frame     
     vec4 tex_color = texture2D(quadTexture, texCoord);
     gl_FragColor = tex_color;
     
}
