layout(location=0) in vec2 position;
void main()
{
    vec3 az = polar_to_azimuthal(position);
    gl_Position = vec4(az.x,az.y,0,1);
    gl_PointSize = 10.0;
}