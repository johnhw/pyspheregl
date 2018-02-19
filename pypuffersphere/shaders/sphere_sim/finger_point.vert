// simplest possible touch shader
layout(location=0) in vec3 position;
void main()
{
    vec2 pos = vec2(position.x, -position.y);
    vec3 az = polar_to_azimuthal(pos);
    gl_Position = vec4(az.x,az.y,0,1);
    gl_PointSize = 10.0;
}