// These are sent to the fragment shader
varying vec4 color;         // color of the point
varying vec2 orig_pos;      // original position of the point in lon, lat
varying vec4 texCoord;      // UV coordinates of texture
uniform float alpha;
void main()
{   
	color = gl_Color;
    
   ///// COORDINATES IN [0,1] TORUS SPACE
    // apply the modelview transform
    // both the x and y coordinate should be in range [0,1]
    
    vec4 pos = gl_ModelViewMatrix * gl_Vertex;
        
    // pass the original x,y to the fragment shader
    orig_pos = t_transform(pos);
    
    vec2 torus = to_torus(orig_pos);
    vec2 sphere = to_sphere(torus, orig_pos);
    vec2 azimuthal = to_azimuthal(sphere);
    vec2 torus_centre = to_torus(vec2(tx, ty));
    float fade = torus_fade(torus_centre, 0.22, 0.22);
   
    color.a = front_visible(fade) * alpha;
    
    texCoord = gl_MultiTexCoord0;
    // write out the position. note that we store the actual depth in the z coordinate in
    // case we need it later
    gl_Position = gl_ProjectionMatrix * vec4(azimuthal.x,azimuthal.y,torus.y,1.);
   
}
