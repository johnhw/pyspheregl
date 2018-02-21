import shlex
import pyglet
import pyglet.gl
from collections import namedtuple
import numpy as np
from PIL import Image
import os
from pyglet.gl import *

# loads a BMFont Text format glyph atlas into a dictionary
# see https://71squared.com/blog/bitmap-font-file-format for more info
# From https://gist.github.com/dghost/20ee2f55deb89861230b
def load_glyph_atlas(filename):
    atlas = {}
    for line in open(filename):
        attributes = shlex.split(line)
        attributes = [x for x in attributes if x != '' and x != '\n']
        dictkey = attributes[0]
        
        if dictkey in atlas:
            attribdict = atlas[dictkey]
        else:
            attribdict = atlas[dictkey] = {}
        if dictkey=='kerning':            
            first = int(attributes[1].split("=")[1])
            second = int(attributes[2].split("=")[1])
            amount = int(attributes[3].split("=")[1])            
            attribdict[(first, second)] = amount
            
        elif dictkey in ['char', 'page']:
            c = int(attributes[1].split("=")[1])
            entry = {}
            for attrib in attributes[2:]:
                key, value = attrib.split("=")
                try:
                    entry[key] = float(value)
                except:
                    entry[key] = value.strip('\"\n')
                attribdict[c] = entry
        else:
            
            for attrib in attributes[1:]:                
                key, value = attrib.split("=")
                try:
                    attribdict[key] = float(value)
                except ValueError:
                    strval = value.strip('\"\n')
                    if ',' in strval:
                        arry = strval.split(',')
                        try:
                            arry = map(float,arry)
                        finally:
                            attribdict[key] = arry
                    else:
                        attribdict[key] = strval
                            
    return atlas

Glyph = namedtuple("Glyph",["x", "y", "width", "height", "xoffset", "yoffset", "xadvance", "page", "chnl"])


class GlyphLabel(object):
    def __init__(self, vertices, textures, indices):
        self.vertices = vertices
        self.textures = textures
        self.indices = indices
        
    def draw(self):
        """To draw, make sure that the OpenGL state is set to:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, page_texture)
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)
            
            In general, if lots of labels need to be drawn, it is much faster
            to concatenate all of the arrays and draw in a single pass.
        """
        pyglet.gl.glVertexPointer(3, GL_FLOAT, 0, self.vertices.ctypes.data)    
        #pyglet.gl.glColorPointer(3, GL_FLOAT, 0, colors.ctypes.data)    
        #pyglet.gl.glNormalPointer(GL_FLOAT, 0, normals.ctypes.data)    
        pyglet.gl.glTexCoordPointer(GL_FLOAT, 0, self.textures.ctypes.data)    
        pyglet.gl.glDrawElements(GL_QUADS, len(self.indices), GL_UNSIGNED_INT, self.indices.ctypes.data)

        
def hex_to_float_color(v):
    if v[0] == '#':
        v = v[1:]
    if len(v)==6:
        return int(v[:2], 16)/255.0, int(v[2:4], 16)/255.0, int(v[4:6], 16)/255.0, 1.0
    else:
        return int(v[:2], 16)/255.0, int(v[2:4], 16)/255.0, int(v[4:6], 16)/255.0, int(v[6:8], 16)/255.0
        
class TextRender(object):

    def load_pages(self):
        """Load each texture page from the font page specifications"""
        self.pages = {}
        for id, pagespec in self.font_spec["page"].iteritems(): 
            #img = Image.open(pagespec["file"])            
            #self.pages[id] = pyglet.image.ImageData(img.width, img.height, 'RGBA', img.tostring(), pitch=-img.width*4).get_texture()
            img = pyglet.image.load(os.path.join(self.path, pagespec["file"]))            
            self.pages[id] = img.get_mipmapped_texture()
            glBindTexture(self.pages[id].target, self.pages[id].id)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)        
       
        
        
    def texture(self, page=0):
        """Return the Pyglet texture object for the given page (0 if only one page)"""
        return self.pages[page]
            
            
    def load_glyphs(self):
        """Transfer each glyph spec into a namedtuple representing that glyph, and place into
            a dictionary which maps each available character to the glyph spec"""            
        self.glyphs = {}
        for id, glyph in self.font_spec["char"].iteritems():            
            g = Glyph(**glyph)
            if id<256:
                self.glyphs[chr(id)] = g
            
            
    def generate_geometry(self, text, strips=False, fake_normals=False, color=None, kerning=0, leading=0, vcenter=False, hcenter=False):
        """Generate geometry to render glyphs to a quad. 
        If strips is True, returns a triangle strip and indices will be None        
        
        Parameters:
            text            String to generate glyphs for
            strips          If True, returns triangle strip format instead of indexed triangle format                       
            normals         Generate normals
            color           Color to be used for the color array, or None if no color array to be generated
            kerning         Adjustment to the kerning of the text (0=normal, -ve=reduced kerning, +ve=increased kerning)
            leading        Adjustment to the leading of the text (0=normal, -ve=reduced, +ve=increased)
            
        Returns:
            size            Dimensions of the text, as a (width, height) pair
            indices         Indices for indexed drawing (i.e. using glDrawElements(GL_TRIANGLES,...). GL_UNSIGNED_INT format 
                            Will be None if strips is True, which will return a format suitable for glDrawArrays(GL_TRIANGLE_STRIP,...) instead.                                        
            vertices        Flat GL_FLOAT array of vertices, with 2 elements-per-vertex.
            texcoords       Flat GL_FLOAT array of 2D texture coordinates into the texture page for this text.                        
            fake_normals    Normal vectors for the text. Always points outwards from the quad centre (only if normals is True), otherwise None
            colors          Color vectors for the text.  (only if color is set). Consists of n copies of the color, one per vertex generated., otherwise None
            
            
        """
        x,y = 0,0
        colors = []
        vertices = []
        texcoords = []
        max_height = 0
        max_width = 0
        lh = self.common["base"]
        scale = 1.0
        last_char = None
        in_command = False
        # dimensions of the page
        sw, sh = float(self.common["scaleW"]), float(self.common["scaleH"])
        if color==None:
            color=[1,1,1,1]
            
        for c in text:        
        
            if c=='{':
                in_command = True
                command = ""
                
            # parse formatting commands
            if c=='}':
                in_command = False
                ##remove leading {
                command = command[1:]                
                commands = command.split(" ")
                
                for elt in commands:                    
                    ##split by colons and strip whitespace
                    if ":" in elt:
                        lhs, rhs = elt.split(":")
                        lhs, rhs = lhs.strip(), rhs.strip()                        
                        if lhs and rhs: 
                            if lhs=="c":
                                color = hex_to_float_color(rhs)
                            if lhs=="k":
                                kerning = float(rhs)
                            if lhs=="x":
                                x += float(rhs)
                            if lhs=="y":
                                y += float(rhs)
                            if lhs=="l":
                                leading = float(rhs)
                            if lhs=="s":
                                scale = float(rhs)
                            
                continue 
                
            ##if we are parsing a command, don't emit anything
            if in_command:
                command += c
                continue
                
     
            if c in self.glyphs:
                char = self.glyphs[c]
            else:
                # otherwise use space character
                char = self.glyphs[" "]
                
        
            if c in self.glyphs:
                char = self.glyphs[c]
            else:
                # otherwise use space character
                char = self.glyphs[" "]
                
                
            # update kerning
            kerning_offset = self.kerning.get((last_char, c), 0)            
            last_char = c
            
            w, h = char.width, char.height
            
            # texture co-ordinates in the page
            tx1,ty2 = char.x/sw, 1.0-(char.y/sh)
            tx2,ty1 = (char.x+char.width)/sw, 1.0-((char.y+char.height)/sh)
            
            # handle newlines
            if c=="\n":
                n_char = self.glyphs["X"]
                y -= (n_char.height + leading) * scale
                x = 0
            else:                
                
                # true position of character
                vx, vy = x+char.xoffset*scale, y-((h+char.yoffset)*scale+lh)
                
                # generate strip geometry
                if strips:
                    if len(vertices)==0:
                        vertices += [(vx,vy), (vx+w*scale, vy), (vx+w*scale, vy+h*scale), (vx, vy+h*scale)]
                        colors += [color, color, color, color]
                        texcoords += [(tx1,ty1), (tx2,ty1), (tx2, ty2), (tx1,ty2)]
                    else:
                        vertices += [(x+w*scale, y), (x+w*scale, y+h*scale)]                    
                        colors += [color, color]
                        texcoords += [(tx2,ty2), (tx2, ty1)]
                else:
                    # or indexed geometry
                    colors += [color, color, color, color, color, color]                    
                    texcoords += [(tx1,ty1), (tx2,ty1), (tx1, ty2), (tx1,ty2), (tx2, ty1),   (tx2, ty2)]
                    vertices += [(vx,vy),   (vx+w*scale, vy), (vx, vy+h*scale), (vx,vy+h*scale), (vx+w*scale, vy),  (vx+w*scale, vy+h*scale)]
                    
                    
                    
                x += (char.xadvance + kerning + self.padding[0] - self.padding[1] - self.spacing[0] + kerning_offset) * scale
                
            # track size of the text box
            if x>max_width:
                max_width = x
            if (y+h)<max_height:
                max_height = y+h
                    
        vertices = np.array(vertices, dtype=np.float32)
        
        # adjust for centering
        if vcenter:
            vertices -= np.array([0,max_height / 2])
        if hcenter:
            vertices -= np.array([max_width/2, 0])
            
        normals, indices = None, None
        if not strips:
            indices = np.arange(len(vertices)).astype(np.uint32)
        if color:
            colors = np.array(colors, dtype=np.float32)            
        if fake_normals:
            normals = np.tile((max_width/2,max_height/2,0), (len(vertices),1)).astype(np.float32)        
        
        return ((max_width, max_height), indices, vertices, np.array(texcoords, dtype=np.float32), np.array(normals, dtype=np.float32), np.array(colors, dtype=np.float32))
        
        
        
    def label(self, text, **kwargs):
        """Create a GlyphLabel object, which can be called to draw text"""
        kwargs["strips"] = False
        v,t,i = generate_geometry(text, **kwargs)
        label = GlyphLabel(v,t,i)
        return label
        
        
    def load_kerning(self):
        self.kerning = {}
        if "kerning" in self.font_spec:            
            for ((first, second), offset) in self.font_spec["kerning"].iteritems():                                
                fc, sc = chr(first), chr(second)
                self.kerning[(fc,sc)] = offset
                
    
    def __init__(self, font_name):
        self.path, self.file = os.path.split(font_name)
        
        self.font_spec = load_glyph_atlas(font_name)        
        self.info = self.font_spec["info"]
        self.padding = self.info["padding"]
        self.spacing = self.info["spacing"]
        self.size = self.info["size"]
        self.common = self.font_spec["common"]
        
        self.load_kerning()
        self.load_pages()
        self.load_glyphs()
    
    
if __name__=="__main__":    
    t = TextRender("century_schoolbook_32.fnt")
    print t.generate_geometry("hello", color=[1,0,1.], fake_normals=True)
    
    