#version 330 core

// from the vertex shader
in vec4 color;    // the base color of the point
flat in int obj_id;

layout(location=0) out vec4 frag_color;
layout(location=1) out int obj_index;

void main(void)
{                    
     // write back to the pixel buffer
     // note that we multiple with color to allow the alpha
     // to be faded to transparent at the sphere lower edge
    frag_color = color;
    // output the index to the second colorbuffer (if attached)
    obj_index = obj_id;
}
