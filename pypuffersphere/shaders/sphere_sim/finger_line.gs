
layout(lines) in;
layout(line_strip, max_vertices = 64) out;

in float brightness[];
out float f_brightness;

vec4 az_position_from_xy(vec2 position)
{
    vec2 pos = vec2(position.x, -position.y);
    vec3 az = polar_to_azimuthal(pos);
    return vec4(az.x,az.y,0,1);
}

void main()
{
    vec2 p1 = gl_in[0].gl_Position.xy;
    vec2 p2 = gl_in[1].gl_Position.xy;
        
    f_brightness = brightness[0]; // passthrough the line brightness

    // compute distance, in spherical units
    float d = spherical_distance(p1, p2);
    
    float lon1 = p1.x;
    float lat1 = p1.y;
    float lon2 = p2.x;
    float lat2 = p2.y;

    // split up line into segments
    int n = 32;
    for(int i=0;i<n;i++)
    {
        float f = i/float(n-1);
        float A=sin((1-f)*d)/sin(d);
        float B=sin(f*d)/sin(d);
        float x = A*cos(lat1)*cos(lon1) +  B*cos(lat2)*cos(lon2);
        float y = A*cos(lat1)*sin(lon1) +  B*cos(lat2)*sin(lon2);
        float z = A*sin(lat1)           +  B*sin(lat2);
        float lat=atan(z,sqrt(sqr(x)+sqr(y)));
        float lon=atan(y,x);        
        gl_Position = az_position_from_xy(vec2(lon, lat));
        EmitVertex();            
    }
    
    EndPrimitive();
    
}