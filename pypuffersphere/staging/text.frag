#version 140

// from the vertex shader
varying vec4 color;    // the base color of the point
varying vec4 texCoord;
uniform float mask_start, mask_end;
uniform float outline_start, outline_end;
uniform sampler2D glyphTexture;

void main(void)
{          
    
     // look up the texture element (we only care about the alpha value)     
     vec4 text_color = texture2D(glyphTexture, texCoord.xy);
     float a,b;

     float aa = 0.4;
     // text_color.a has a value between 0 (edge of character blur) and 1 (centre of character)
     // We first compute the alpha level to apply (the wider this band is, the smoother the character is) [alpha mask]
     a = smoothstep(0.0, 0.5, text_color.a); 
     // then compute the width of the black outline [outline mask]
     b = smoothstep(0.3, 0.6, text_color.a);      
     // set the scale factors
     text_color.rgb = mix(vec3(0,0,0), vec3(1,1,1), b);
     text_color.a = a;
     
     // write back to the pixel buffer, combining the alpha mask, outline mask and original color
     gl_FragColor = text_color * color;     
}
