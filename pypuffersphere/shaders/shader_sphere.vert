varying vec4 color;
uniform float resolution;
#define M_PI 3.1415926535897932384626433832795

void main()
{   
	vec4 pos_3d, norm_pos;
	float lat, lon, x, y, w, r, z;
    color = gl_Color;

    pos_3d =  gl_ModelViewMatrix * gl_Vertex;        
    pos_3d.w = 0;

    // convert to sphere space
    norm_pos = normalize(pos_3d);

    lat = acos(norm_pos.z) - M_PI/2;
    lon = atan2(norm_pos.y, norm_pos.x);
    
    r = (M_PI/2-lat)/M_PI;      
    w = resolution/2.0;
    x = w + r * w * cos(lon);
    y = w - r*w*sin(lon);
    
 	//z = (r<0.9) & (r>0.05);
 	//z = (1-z) * 1000;

    gl_Position = gl_ProjectionMatrix * vec4(x,y,0,1);
}