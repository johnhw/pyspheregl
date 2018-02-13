#version 330 core
#define M_PI 3.1415926535897932384626433832795


// used to find the click position in spherical coordinates
// by coloring each pixel according to it's original spherical location

in vec2 sphere;
in float alpha;

void main(void)
{              
    
    gl_FragColor.rg = vec2(sphere.x / M_PI +0.5, sphere.y / (2*M_PI)+0.5);    
    gl_FragColor.b = 0.0;
    gl_FragColor.a = alpha;          
}