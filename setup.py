from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Build import cythonize
from numpy import get_include

sphere_ext = Extension('pypuffersphere.sphere.sphere_cy', sources=['pypuffersphere/sphere/sphere_cy.pyx'])
# doesn't work on OSX unless you do this explicitly for some reason...
sphere_ext.include_dirs = [get_include()]

setup(
    # basic info
    name = 'pypuffersphere',
    version = '0.0.1',
    packages = find_packages(),
    # also pygame, but can't easily install that like this 
    install_requires = ['numpy', 'pyopengl', 'pyglet', 'Cython', 'pyosc' ],

    # files 
    ext_modules = cythonize([sphere_ext]),
    include_package_data = True,

    # metadata
    description = 'Python/Pyglet code for rendering on the PufferSphere',
    author = 'John Williamson',
    author_email = 'johnhw@gmail.com',
    url = 'https://github.com/johnhw/pypypuffersphere', 
    keywords = ['pypuffersphere', 'sphere', 'touch', 'spherical'], 
    classifiers = [],
)
