import sys, os, argparse


DEFAULT_PRODUCT = "pf1600"

# definitions of standard
# spherical/nonplanar displays, 
products = {
    "pf1600": 
    {
        "width":2560,               # dimensions of the projector display
        "height":1600,
        "virtual_resolution":1920,             # viewport size rendered at, to compensate for partial coverage        
        "lat_range":[-90, 90],      # min and max latitude displayed, in degrees
        "lon_range":[-180, 180],    # min and max longitude displayed
        "prod_id":"",
        "tuio_port":3333,
        "tuio_addr":"/tuio/2Dcur",
        "at_ip":"127.0.0.1",
        # how tuio maps onto the surface
        # format: xy offset, degrees range, degrees offset
        "tuio_map": [[-0.5, 360, 180], 
                     [0.0, 180, -90]]
    },

    "dome1600": 
    {
        "width":2560,               # dimensions of the projector display
        "height":1600,
        "virtual_resolution":1920*2,# viewport size rendered at, to compensate for partial coverage        
        "lat_range":[0, 90],      # min and max latitude displayed, in degrees
        "lon_range":[-180, 180],    # min and max longitude displayed
        "prod_id":"",
        "at_ip":"127.0.0.1",
        "tuio_port":3333,
        "tuio_addr":"/tuio/2Dcur",
        # how tuio maps onto the surface
        # format: xy offset, degrees range, degrees offset
        "tuio_map": [[-0.5, 360, 180], 
                     [0.0, 90, 0]]
    }
}


def get_tuio_to_polar(product):
    off_x, scale_x, offset_lon = product["tuio_map"][0]
    off_y, scale_y, offset_lat = product["tuio_map"][1]
    scale_x, scale_y = np.radians(scale_x), np.radians(scale_y)
    offset_lon, offset_lat = np.radians(offset_lon), np.radians(offset_lat)
    def tuio_to_polar(x,y):
        lon = ((tuio_x+off_x)*scale_x + offset_lon) % (2*np.pi)
        lat = scale_y * (1-tuio_y) + offset_lat
        if lon>np.pi:
            lon -= 2*np.pi
        return lon, lat



# use: passed arguments, if provided
# or command line arguments, if provided
# or environment variable, if provided
# or global default, if none of the above provided
def get_product(product=None, test_mode=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', help="Run in simulator mode.",  action='store_true', dest="test")
    parser.add_argument('--product', help="Set the product ID.",  action='store', dest="product_id")
    results, _ = parser.parse_known_args()    

    if product is None:
        # check enivronment variables
        product = os.environ.get("pf_product", None)    
                
        test_mode = results.test
        if results.product_id is not None:
            product = results.product_id

        # no config, so use the global default
        if product is None:
            product =  DEFAULT_PRODUCT

    if test_mode is None:
        test_mode = results.test

    product_dict = dict(products[product])
    product_dict["product"] = product
    product_dict["test_mode"] = test_mode
    return product_dict


if __name__=="__main__":
    print("Using %s device" % get_product()["product"])