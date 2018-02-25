import pyglet
from pyglet.gl import *
import numpy as np

class VBuf:
    def __init__(self,  buffer, name="", id=-1, divisor=-1, mode=GL_STATIC_DRAW):
        self.buffer = create_vbo(buffer, mode=mode)
        self.name = name
        self.id = id
        self.shape = buffer.shape
        self.divisor = divisor
        self.mode = mode

    def set(self, array):
        assert(self.shape==array.shape)
        self.buffer.set_data(array)
        #self.buffer.set_data(array.astype(np.float32).ctypes.data)




def create_vao(vbufs):
    """
        Takes a list of VBufs, and generates
        the VAO which attaches all of them and returns it.
    """
    # generate a new vao
    vao = GLuint()
    glGenVertexArrays(1, vao)
    glBindVertexArray(vao)
 
    # attach vbos
    for vbuf in vbufs:
        glEnableVertexAttribArray(vbuf.id)
        attach_vbo(vbuf.buffer, vbuf.id)        
        if vbuf.divisor!=-1:
            glVertexAttribDivisor(vbuf.id, vbuf.divisor)

    # unbind all buffers
    glBindVertexArray(0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)               
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    return vao

def draw_vao(vao, ibo=None, primitives=GL_QUADS,  n_vtxs=0, n_prims=0):
    glBindVertexArray(vao)
    if ibo is None:
        if nprims==0:
            glDrawArrays(primitives, 0, n_vtxs)
        else:
            glDrawArraysInstanced(primitives, 0, n_vtxs, n_prims)
    else:
        ibo.bind()
        if n_prims==0:
            glDrawElements(primitives, n_vtxs, GL_UNSIGNED_INT, 0)            
        else:
            glDrawElementsInstanced(primitives, n_vtxs, GL_UNSIGNED_INT, 0, n_prims)            
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    glBindVertexArray(0)



# simple VBO wrapper since pyglet's built in object
# seems to be buggy (?)
class VBO:
    def __init__(self, data, mode):
        vbo = GLuint()
        glGenBuffers(1, vbo)
        self.target = GL_ARRAY_BUFFER
        self.id = vbo 
        self.bind()
        self.mode = mode    
        # upload the placeholder data
        # must be the same shape on subsequent updates!
        
        data = data.astype(np.float32)
        glBufferData(self.target, data.nbytes, data.ctypes.data, self.mode)        
        
        self.nbytes = data.nbytes                
        self.vbo_id = vbo
        self.shape = data.shape        
        self.unbind()

    def bind(self):
        glBindBuffer(self.target, self.id)

    def unbind(self):
        glBindBuffer(self.target, 0)

    def set_data(self, data):
        data = data.astype(np.float32)
        assert(data.nbytes == self.nbytes and data.shape==self.shape)
        self.bind()
        glBufferSubData(self.target, 0, data.nbytes, data.ctypes.data)
        
        



def create_vbo(arr, mode=GL_STATIC_DRAW):
    """Creates an np.float32/GL_FLOAT buffer from the numpy array arr on the GPU"""
    #bo = pyglet.graphics.vertexbuffer.create_buffer(arr.nbytes, GL_ARRAY_BUFFER, mode, vbo=True)
    bo = VBO(arr, mode)
    return bo

def create_elt_buffer(arr, mode=GL_STATIC_DRAW):
    """Creates an np.uint32/GL_UNSIGNED_INT buffer from the numpy array arr on the GPU"""    
    arr = arr.astype(np.uint32)
    bo = pyglet.graphics.vertexbuffer.create_buffer(arr.nbytes, GL_ELEMENT_ARRAY_BUFFER, mode, vbo=True)
    bo.bind()            
    
    bo.set_data(arr.ctypes.data)  
    bo.shape = arr.shape # store shape for later  
    # unbind
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
    return bo

def IBuf(arr):
    return create_elt_buffer(arr)

def attach_vbo(bo, n):
    """Attach a vertex buffer object to attribute pointer n"""
    glEnableVertexAttribArray(n)
    glBindBuffer(bo.target, bo.id)        
    # use number of elements in last element of the buffer object
    glVertexAttribPointer(n, bo.shape[-1], GL_FLOAT, False, 0, 0)


def draw_elt_buffer(elt_bo, primitives=GL_QUADS):
    """Using the given element buffer, draw the indexed geometry"""    
    glBindBuffer(elt_bo.target, elt_bo.id)    
    glDrawElements(primitives, elt_bo.shape[0], GL_UNSIGNED_INT, 0)        
    # unbind all buffers
    glBindBuffer(GL_ARRAY_BUFFER, 0)               
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


