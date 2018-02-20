#version 330

// These are sent to the fragment shader
in vec2 az_position;
in vec2 flat_position;
in vec3 cart_position; // position in cartesian coordinates
in vec2 polar_position;// position in spherical coordinates
in vec4 texCoord;      // UV coordinates of texture

layout(location=0) out vec4 color;

uniform float spacing=5;
uniform float brightness=0.1;

vec3 grid(vec2 sphere, float spacing)
{
    float ycoord = degrees(sphere.y) / spacing;
    float xcoord = degrees(sphere.x) / spacing;    
    
    float yline = abs(fract(ycoord - 0.5) - 0.5) / min(fwidth(ycoord),0.1);    
    float xline = abs(fract(xcoord - 0.5) - 0.5) / min(fwidth(xcoord),0.1);    
    vec3 grid_line =  (vec3(1.0 - min(xline, 1.0)) + vec3(1.0 - min(yline, 1.0)));
        
    return grid_line;

}


void main()
{   
    color = vec4(grid(polar_position.xy, spacing), brightness);    
}
