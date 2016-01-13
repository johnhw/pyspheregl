import pygame
import numpy as np

class ColorGradient(object):
    def __init__(self, color_array):
        """Create a color gradient from an array of RGB integer tuples"""
        self.color_array = color_array/255.0        
        self.n = len(self.color_array)
        self.base = np.arange(0,self.n)
        
    def __call__(self, xs):
        """Given a floating point value in [0,1], return the RGB color as an floating point triple."""
        cx = np.clip(xs * self.n, 0, self.n)
        r = np.interp(cx, self.base, self.color_array[:,0])
        g = np.interp(cx, self.base, self.color_array[:,1])
        b = np.interp(cx, self.base, self.color_array[:,2])
        return r,g,b
            
def make_gradient(img):
    """Load a gradient from an image. Should be a horizontal strip. """
    color_array = np.mean(pygame.surfarray.pixels3d(pygame.image.load(img)), axis=1)
    return ColorGradient(color_array)
    
# gradient = make_gradient("some.png")
# gradient(0.3)