#version 330 core
#define M_PI 3.1415926535897932384626433832795

layout (location=0) out vec4 color;

// used to find the click position in spherical coordinates
// by coloring each pixel according to it's original spherical location

in vec2 sphere;
in float alpha;

void main(void)
{              
    
    color.rg = vec2(sphere.x / (2*M_PI)+0.5, -sphere.y / M_PI +0.5);    
    color.b = 0.0;
    color.a = alpha;          
}