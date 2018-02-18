// simple pass through for geometry shader
// which will subdivide this line
layout(location=0) in vec3 position;

out float brightness;

void main()
{
    brightness = position.z;    
    gl_Position = vec4(position, 0);
}