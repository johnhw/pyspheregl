
#version 330 core
#define version_set 330
#define M_PI 3.1415926535897932384626433832795
vec3 quat_rotate_vertex(vec3 v, vec4 q)
{ 
  return v + 2.0 * cross(q.xyz, cross(q.xyz, v) + q.w * v);
}

vec2 az_to_polar(vec2 az)
{
    vec2 lonlat;
    lonlat.x = atan(az.y,az.x);
    lonlat.y = -(sqrt((az.x*az.x)+(az.y*az.y)) * M_PI - M_PI/2);
    
    return lonlat;    
}

float sqr(float f)
{
    return f*f;
}

float spherical_distance(vec2 p1, vec2 p2)
{
    /* Given two points p1, p2 (in radians), return
    the great circle distance between the two points. */
    float lon1 = p1.x;
    float lat1 = p1.y;
    float lon2 = p2.x;
    float lat2 = p2.y;

    float dlat = lat2-lat1;
    float dlon = lon2-lon1;
    float a = sqr(sin(dlat/2)) + cos(lat1)*cos(lat2)*sqr(sin(dlon/2));
    float c = 2*atan(sqrt(a), sqrt(1-a));
    return c;
}

vec3 cartesian_to_azimuthal(vec3 cartesian)
{
    vec3 az;
    vec3 norm_pos = normalize(cartesian);
    vec2 xy = normalize(cartesian.xy);
    float r = acos(norm_pos.z) / M_PI;        
    az.x = r*xy.x;
    az.y = -r*xy.y;
    az.z = r;
    return az;    
}

vec2 cartesian_to_polar(vec3 cartesian)
{
    vec3 norm_pos = normalize(cartesian);
    float lat = acos(-norm_pos.z) - M_PI/2;
    float lon = atan(norm_pos.y, norm_pos.x);
    return vec2(lon, lat);
}



vec3 polar_to_azimuthal(vec2 lonlat)
{
    vec3 az;
    float lon = lonlat.x;
    float lat = lonlat.y;
    float r = (M_PI/2-lat)/M_PI;
    az.x = r * cos(lon);
    az.y = -r * sin(lon);
    az.z = r;
    return az;
}



vec3 spherical_to_cartesian(vec2 lonlat)
{
    // Convert a lon, lat co-ordinate to an a Cartesian x,y,z point on the unit sphere.
    vec3 cart;
    float lon, lat;
    lon = lonlat.x;
    lat = lonlat.y;
    lat += M_PI/2;
    float st = sin(lat);
    cart.x = cos(lon) * st;
    cart.y = sin(lon) * st;
    cart.z = -cos(lat);    
    return cart;
}   

vec3 polar_to_cartesian(vec2 lonlat)
{
    return spherical_to_cartesian(lonlat);
}


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