DEFAULT_PRODUCT = "pf1600"

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
        # how tuio maps onto the surface
        # format: xy offset, degrees range, degrees offset
        "tuio_map": [[-0.5, 360, -180], 
                     [0.0, 180, -90]]
    }
}

import sys, os, argparse


# use: passed arguments, if provided
# command line arguments, if provided
# environment variable, if provided
# global default, if none provided
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