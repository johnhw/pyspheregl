#version 330 core

// from the vertex shader
in vec4 color;    // the base color of the point
in vec3 texCoord;
in vec4 obj_id;
uniform sampler2D tex;

layout(location=0) out vec4 frag_color;
layout(location=1) out vec4 obj_index;

void main(void)
{          
     
     vec4 tex_color = texture(tex, texCoord.xy).rgba;
     // write back to the pixel buffer
     // note that we multiple with color to allow the alpha
     // to be faded to transparent at the sphere lower edge
    frag_color = tex_color * color;
    // output the index to the second colorbuffer (if attached)
    obj_index = obj_id;
    obj_index.a = step(0.5, tex_color.a * color.a);
     
}
