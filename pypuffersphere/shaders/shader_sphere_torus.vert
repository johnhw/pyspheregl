varying vec4 color;
uniform float resolution;
#define M_PI 3.1415926535897932384626433832795
uniform float torus_rotate=0;

// From https://gist.github.com/neilmendoza/4512992
mat4 rotationMatrix(vec3 axis, float angle)
{
    axis = normalize(axis);
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    
    return mat4(oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s,  oc * axis.z * axis.x + axis.y * s,  0.0,
                oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,           oc * axis.y * axis.z - axis.x * s,  0.0,
                oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s,  oc * axis.z * axis.z + c,           0.0,
                0.0,                                0.0,                                0.0,                                1.0);
}



void main()
{   
	vec4 pos_3d, norm_pos;
	float lat, lon, x, y, w, r, z;
    vec4 normal;
    mat4 rot_matrix;
    color = gl_Color;

    normal.xyz = gl_Normal;
    normal.w = 0;
    pos_3d =   gl_Vertex;        
    pos_3d.w = 0;

    // convert to sphere space
    norm_pos = normalize(pos_3d);

    vec3 lon_equator = gl_Normal.xyz;
    lon_equator.z = 0;
    lon_equator = normalize(lon_equator);
    vec3 rotate_vector = vec3(-lon_equator.y, lon_equator.x, 0);
    
    // now rotate by the torus rotation vector for this point
    rot_matrix = rotationMatrix(rotate_vector, torus_rotate);
    norm_pos =  rot_matrix * norm_pos;    
    norm_pos = normalize(norm_pos);

    // drop normal to horizon
    normal.z = 0;
    normal = normalize(normal);



    float inside;
    inside = dot(normal.xyz, norm_pos.xyz)<0;
    color.a *= inside;    

    norm_pos = gl_ModelViewMatrix * norm_pos;

    // project to azimuthal as usual
    lat = acos(norm_pos.z) - M_PI/2;
    lon = atan2(norm_pos.y, norm_pos.x);
    
    r = (M_PI/2-lat)/M_PI;      
    w = resolution/2.0;
    x = w + r * w * cos(lon);
    y = w - r*w*sin(lon);
    
 	z = ((r<0.85) & (r>0.01));

 	z = (1-z) * 1000;

    gl_Position = gl_ProjectionMatrix * vec4(x,y,z,1);
}