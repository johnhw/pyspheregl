import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pygame.locals import *
import pygame,time,sys,random,math
import glskeleton, glutils, random
import gloffscreen
import sphere_sim
import sphere
import itertools

if __name__ == "__main__":
	s = sphere_sim.make_viewer()
	size = s.size
	def draw_fn():
		global first
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glDisable(GL_LIGHTING)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(0, size, 0, size, -1, 500)
		glMatrixMode(GL_MODELVIEW)    
		glLoadIdentity()
		glEnable(GL_POINT_SMOOTH)
		glPointSize(2.0)
		glColor4f(1,0,1,1)
		glDisable(GL_TEXTURE_2D)
		glLineWidth(2.0)
		glEnable(GL_LINE_SMOOTH)
		glEnable(GL_BLEND)
		glDisable(GL_DEPTH_TEST)
		glClearColor(1,1,1,1)
		glClear(GL_COLOR_BUFFER_BIT)
		sphere_sim.make_grid(size)

		def draw_polar(pts):
			for x,y in pts:
				x,y =  sphere.polar_to_display(x,y,size)
				glVertex2f(x,y)


		n = 8
		rad = 0.03 * np.pi

		for i in range(n*2):
			for j in range(n):
				lon = i * ((np.pi)/n) - np.pi
				lat = j * ((np.pi)/n) - np.pi/2
				if lat>-1.4:
					pts = sphere.spherical_circle((lon, lat), rad)
					glColor4f(0.5, 0.5, 0.0, 0.5)
					glBegin(GL_LINE_LOOP)
					draw_polar(pts)
					glEnd()


	s.draw_fn = draw_fn
	s.start()
