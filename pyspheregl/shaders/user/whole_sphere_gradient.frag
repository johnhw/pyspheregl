#version 330

// These are sent to the fragment shader
in vec2 az_position;
in vec2 flat_position;
in vec3 cart_position; // position in cartesian coordinates
in vec2 polar_position;// position in spherical coordinates
in vec4 texCoord;      // UV coordinates of texture

layout(location=0) out vec4 color;
layout(location=1) out uint obj_id;

uniform sampler2D tex;
uniform vec3 gradient_axis;

void main()
{   
    float grad_pos = dot(gradient_axis, cart_position);
    color = texture(tex, vec2((grad_pos+1)/2, 0.5));        
    obj_id = 0;
}
