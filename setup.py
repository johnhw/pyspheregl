from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Build import cythonize
from numpy import get_include

sphere_ext = Extension('pyspheregl.sphere.sphere_cy', sources=['pyspheregl/sphere/sphere_cy.pyx'])
# doesn't work on OSX unless you do this explicitly for some reason...
sphere_ext.include_dirs = [get_include()]

setup(
    # basic info
    name = 'pyspheregl',
    version = '0.0.2',
    packages = find_packages(),
    
    install_requires = ['numpy', 'pyopengl', 'pyglet', 'Cython', 'pyosc', 
                        'attrs', 'scikit-learn', 'asciimatics', 'pyzmq'],

    # files 
    ext_modules = cythonize([sphere_ext]),
    include_package_data = True,

    # metadata
    description = 'Python/Pyglet code for rendering on the PufferSphere',
    author = 'John Williamson',
    author_email = 'johnhw@gmail.com',
    url = 'https://github.com/johnhw/pyspheregl', 
    keywords = ['pyspheregl', 'sphere', 'touch', 'spherical'], 
    classifiers = [],
)
