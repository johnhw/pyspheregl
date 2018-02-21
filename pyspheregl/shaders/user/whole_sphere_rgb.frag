#version 330

// These are sent to the fragment shader
in vec2 az_position;
in vec2 flat_position;
in vec3 cart_position; // position in cartesian coordinates
in vec2 polar_position;// position in spherical coordinates
in vec4 texCoord;      // UV coordinates of texture

layout(location=0) out vec4 color;

uniform sampler2D tex;

void main()
{   
    color = texture(tex, texCoord.xy);
    color.r = (cart_position.x+1)/2;    
    color.g = (cart_position.y+1)/2;    
    color.b = (cart_position.z+1)/2;    
    
}
