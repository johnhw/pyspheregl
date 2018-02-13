from PIL import Image
from pyglet.gl import *
import numpy as np
import StringIO


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
    
    color_array = np.mean(np.array(Image.open(img)), axis=1)
    return ColorGradient(color_array)
    
def fit_image(img, sz):
    # fit image into sz x sz square scaling and cropping as needed
    w,h = img.width, img.height
    
    scale_factor = sz / float(min(w,h))
    
    new_w = int(w * scale_factor)
    new_h = int(h * scale_factor)
    
    dw = new_w - sz
    dh = new_h - sz
    
    img = img.resize((new_w, new_h), Image.ANTIALIAS) 
    
    
    img = img.crop((dw//2, dh//2, new_w-dw//2, new_h-dh//2))
    img = img.crop((0,0,sz,sz))
    return img
    
def load_image_and_fit(img_string, sz):
    # load an image and fit it to a square of size sz x sz (usually a power of 2)
    image = Image.open(StringIO(img_string))
    image = fit_image(image, sz)        
    return pyglet.image.ImageData(image.width, image.height, 'RGB', image.tobytes(), pitch=-image.width * 3).get_mipmapped_texture()
    
    
def make_unit_quad_tile(n_divs, x1=0.0, x2=1.0, y1=0.0, y2=1.0, tx1=0.0, tx2=1.0, ty1=0.0, ty2=1.0, n_quads=1):
    # subdivide a rectangle into n_divs x n_divs smaller sub-rectangles, with corresponding texture coordinates
    vertices = []
    indices = []
    texs = []
    ix = 0
    for k in range(n_quads):
        x, y = x1, y1 
        xdiv = (x2-x1)/n_divs
        ydiv = (y2-y1)/n_divs
        
        txdiv = (tx2-tx1)/n_divs
        tydiv = (ty2-ty1)/n_divs
        tx, ty = tx1, ty1
        
       
        
        for i in range(n_divs):
            x = x1
            tx = tx1
            for j in range(n_divs):
                vertices += [[x,y], [x+xdiv, y], [x+xdiv, y+ydiv], [x, y+ydiv]]
                texs +=     [[tx,ty], [tx+txdiv, ty], [tx+txdiv, ty+tydiv], [tx, ty+tydiv]]
                indices +=  [ix, ix+1, ix+2, ix+3]
                ix += 4
                x += xdiv
                tx += txdiv
            y += ydiv
            ty += tydiv
       
    return np.array(indices, dtype=np.uint32), np.array(vertices, dtype=np.float32)*2-1, np.array(texs, dtype=np.float32)
 
 


    
class TextureStore3D(object):
    def __init__(self, width=128, height=128, pages=32, data=None):
        self.width = width
        self.height = height
        self.pages = pages
        self.id = GLuint()
        glGenTextures(1, self.id)        
        self.target = GL_TEXTURE_2D_ARRAY
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.id)        
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR)        
        # todo: mipmap each level
        if data is not None:
            glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, self.width, self.height, pages, 0, GL_RGBA, GL_UNSIGNED_BYTE, data.ctypes.data)
        else:
            glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, self.width, self.height, pages, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            
    def load_slot(self, img, slot):
        if slot>=0 and slot<self.pages:
            glBindTexture(GL_TEXTURE_2D_ARRAY, self.id) 
            glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, slot, self.width, self.height, 1, GL_RGBA, GL_UNSIGNED_BYTE, img.ctypes.data)
