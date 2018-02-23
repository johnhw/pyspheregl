from PIL import Image
from pyglet.gl import *
import numpy as np
import StringIO
import timeit
# high precision timing
wall_clock = timeit.default_timer

class SpriteSheet3D(object):
    def __init__(self, w=1024, h=1024,  max_frames=16):
        self.atlas = pyglet.image.atlas.Allocator(w, h)        
        self.anim_texture = TextureStore3D(w,h,max_frames)
        self.max_frames = max_frames
        self.frame_map = {}
        self.n_frames = {}

    @property
    def n_sprites(self):
        return len(self.frame_map)

    def add_frame(self, img, id, frame):
        if frame>self.max_frames:
            # discard excessive frames
            print("Too many frames!") 
            return
        
        self.n_frames[id] = max(frame,self.n_frames.get(id, 0))
        w, h = img.shape[1], img.shape[0]
        if id not in self.frame_map:
            # make sure we have texel border so that
            # slicing up the atlas we don;t have bleed over
            # hence the +2
            x, y = self.atlas.alloc(w+2,h+2)        
            self.frame_map[id] = (x,y,w,h)
        
        x,y,w,h = self.frame_map[id]    
        self.anim_texture.load_sub(img,x,y,w,h,frame)
        
    def get_texture(self):
        return self.anim_texture
        
    def sprite_tex_coord(self, id):
        # return the floating point texture coordinates
        # for the top left and bottom right corners of the sprite
        x,y,w,h = self.frame_map[id]
        u1,v1 = x/float(self.atlas.width), y/float(self.atlas.height)
        u2,v2 = (x+w)/float(self.atlas.width), (y+h)/float(self.atlas.height)
        return u1,v1,u2,v2


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


def make_circle_fan(n_divs, radius=1.0):
    # make a TRIANGLE_FAN style circle
    vertices = [[0,0]]
    indices = [0]
    for i in range(n_divs):
        angle = (i/float(n_divs)) * 2 * np.pi
        x, y = np.cos(angle), -np.sin(angle)
        vertices.append((x,y))
        indices.append(i+1)
    # end point
    x, y = np.cos(0), -np.sin(0)        
    vertices.append((x,y))
    indices.append(n_divs+1)
    return np.array(indices, dtype=np.uint32), np.array(vertices, dtype=np.float32)

    
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
            

    def load_sub(self, img, x, y, w, h, slot):
        if slot>=0 and slot<self.pages:
            glBindTexture(GL_TEXTURE_2D_ARRAY, self.id) 
            glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, x, y, slot, w, h, 1, GL_RGBA, GL_UNSIGNED_BYTE, img.ctypes.data)

    def load_slot(self, img, slot):
        if slot>=0 and slot<self.pages:
            glBindTexture(GL_TEXTURE_2D_ARRAY, self.id) 
            glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, slot, self.width, self.height, 1, GL_RGBA, GL_UNSIGNED_BYTE, img.ctypes.data)
