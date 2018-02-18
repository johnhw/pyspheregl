// simplest possible touch shader
layout(location=0) in vec2 position;



out vec4 color;
out vec2 polar;
uniform int target;
uniform vec3 selected_color;
uniform float t;

void main()
{
    vec2 pos = vec2(position.x, position.y);
    polar = position.xy;
    vec3 az = polar_to_azimuthal(pos);
    gl_Position = vec4(az.x,az.y,0,1);
    
    if(target==gl_VertexID)
    {
        color = vec4(selected_color,1.0);        

        gl_PointSize = 100.0 + cos(t*2)*20.0;
    }
    else
    {
        color = vec4(0.8, 0.8, 0.8, 1.0);
        gl_PointSize = 30.0;
    }
    
    
}