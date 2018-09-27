from pyglet.gl import *
from ctypes import *
from shader import GLSLError
import contextlib
import numpy as np
import np_vbo
import pyglet.gl as gl

class ShaderVBO:
    def __init__(self, shader, ibo, buffers=None, textures=None, attribs=None, vars=None, primitives=GL_QUADS):
        self.shader = shader        
        self.ibo = ibo
        
        self.buffers =  {}
        self.textures = {}
        self.tex_names = {}
        self.uniforms = {}
        self.primitives = primitives
        buffers = buffers or {}
        textures = textures or {}
        attribs = attribs or {}
        vars = vars or {}
        self.buffers_used = {}
        with self.shader as s:
            vbos = []
            
            # set the locations from the shader given the buffer names
            for name,vbuf in buffers.items():
                id = self.shader.attribute_location(name)                
                if id<0:
                    raise GLSLError("Could not find attribute %s in shader" % name)
                vbuf.id = id
                vbuf.name = name
                print("attr: %s -> %d" % (name, id))
                self.buffers[name] = vbuf
                vbos.append(vbuf)
                
            # bundle into a single vao
            self.vao = np_vbo.create_vao(vbos, ibo=ibo)
            self.n_vtxs = ibo.shape[0]

            # set constant attribs
            for name,attrib in attribs.items():
                id = self.shader.attribute_location(name)                
                if id<0:
                    raise GLSLError("Could not find attribute %s in shader" % name)
                        
                print("constant attr: %s" % name)
                glDisableVertexAttribArray(id)
                self.shader.attribf(id, attrib)                   
                
            for ix,(tex_name,tex) in enumerate(textures.items()):
                # set the sampler to the respective texture unit
                s.uniformi(tex_name, ix)       
                print("texture: %s -> active_texture_%d" % (tex_name, ix))
                self.tex_names[tex_name] = ix         
                self.textures[ix] = tex

            for var, value in vars.items():
                self.__setitem__(var, value)
        self.shader.unbind()

    def set_attrib(self, name, attrib):
        id = self.shader.attribute_location(name)  
        if id<0:
                raise GLSLError("Could not find attribute %s in shader" % name)                        
        
        glDisableVertexAttribArray(id)
        self.shader.attribf(id, attrib) 

    def __setitem__(self, var, value):
        """Override setting uniforms so that they actually write to the shader,
        as if they were just ordinary variables"""
        if var in self.shader.active_uniforms:
            self.shader.__setitem__(var, value)

    def set_texture(self, name, texture):
        """Change the named texture to the given texture ID"""
        self.textures[self.tex_names[name]] = texture

    def draw(self, vars=None, n_prims=0, textures=None, primitives=None, attribs=None):
        vars = vars or {}
        attribs = attribs or {}

        primitives = primitives or self.primitives
        # either use the default textures

        if textures is None:
            textures = self.textures
            
        else:
            # or remap them here
            ntextures = {}
            with self.shader as s:
                for ix,(tex_name,tex) in enumerate(textures.items()):                
                    s.uniformi(tex_name, ix) 
                    ntextures[ix] = tex
            textures = ntextures

        self.shader.draw(vao=self.vao, textures=textures, 
                        vars=vars, n_prims=n_prims, primitives=self.primitives, attribs=attribs,
                        n_vtxs=self.n_vtxs)
        
  
    

