#version 330 core
#define M_PI 3.1415926535897932384626433832795

// from the vertex shader
in vec2 texCoord;
in vec2 sphere;
in float alpha, illumination;
uniform sampler2D quadTexture;

layout(location=0) out vec4 frag_color;

// allow a grid to be shown
uniform float grid_space=10;
uniform float grid_bright=0.1;

vec3 grid(vec2 sphere, float spacing)
{
    float ycoord = sphere.y * grid_space;
    float xcoord = sphere.x * grid_space;    
    float yline = abs(fract(ycoord - 0.5) - 0.5) / fwidth(ycoord);    
    float xline = abs(fract(xcoord - 0.5) - 0.5) / fwidth(xcoord);    
    vec3 grid_line =  (vec3(1.0 - min(xline, 1.0)) + vec3(1.0 - min(yline, 1.0)));
    return grid_line;

}

void main(void)
{          
     // look up the texture at the UV coordinates
    vec4 tex_color = texture2D(quadTexture, texCoord);
    tex_color.rgb *= illumination;
    frag_color = tex_color;
    frag_color.rgb += grid_bright * grid(sphere, grid_space);    
    frag_color.a *= alpha;
     
     
}