import sys, time, os
import pyglet

# Skeleton class                                          
class GLSkeleton:
      
    def init_pyglet(self, size):
        width, height= size
        config = None
        # windows only
        if os.name == 'nt':
            config = pyglet.gl.Config(sample_buffers=1, samples=8)
        screens= pyglet.window.get_platform().get_default_display().get_screens()
        self.window = None
        # try to find a matching screen
        for screen in screens:
            if screen.width==width and screen.height==height:
                self.window = pyglet.window.Window(config=config, fullscreen=True, screen=screen)
        if not self.window:
            self.window = pyglet.window.Window(config=config, fullscreen=False, width=width, height=height)        

        # attach the handlers for events
        self.window.set_handler("on_draw", self.on_draw)    
        
        self.window.set_handler("on_key_press", self.on_key_press)
        self.window.set_handler("on_key_release", self.on_key_release)
        self.window.set_handler("on_mouse_motion", self.on_mouse_motion)
        self.window.set_handler("on_mouse_press", self.on_mouse_press)
        self.window.set_handler("on_mouse_release", self.on_mouse_release)
        self.window.set_handler("on_mouse_drag", self.on_mouse_drag)  
        self.window.set_handler("on_resize", self.on_resize)      
        self.w, self.h = self.window.width, self.window.height

        print("OpenGL version", pyglet.gl.gl_info.get_version(), pyglet.gl.gl_info.get_vendor())
        
        
        

    def on_resize(self, w, h):            
            if self.resize_fn:
                    self.resize_fn(w,h)
            return pyglet.event.EVENT_HANDLED

    def on_draw(self):
        if self.draw_fn:
            self.draw_fn()
            
    def on_key_press(self, symbol, modifiers):
        if self.key_fn:
            self.key_fn("press", symbol, modifiers)
    
    def on_key_release(self, symbol, modifiers):
        if self.key_fn:
            self.key_fn("release", symbol, modifiers)
            
    def on_mouse_motion(self, x, y, dx, dy):
        if self.mouse_fn:
            self.mouse_fn("move", x=x,y=y,dx=dx,dy=dy)
            
    def on_mouse_drag(self, x,y, dx, dy, buttons, modifiers):
        if self.mouse_fn:
            self.mouse_fn("drag", x=x,y=y,dx=dx,dy=dy,buttons=buttons,modifiers=modifiers)
                        
    def on_mouse_press(self, x,y, buttons, modifiers):
        if self.mouse_fn:
            self.mouse_fn("press", x=x,y=y,buttons=buttons,modifiers=modifiers)
            
    def on_mouse_release(self, x,y, buttons, modifiers):
        if self.mouse_fn:
            self.mouse_fn("release", x=x,y=y,buttons=buttons, modifiers=modifiers)
            
    def on_mouse_scroll(self, x,y, scroll_x, scroll_y):
        if self.mouse_fn:
            self.mouse_fn("scroll", x=x,y=y,scroll_x=scroll_x, scroll_y=scroll_y)
    
        
    # init routine, sets up the engine, then enters the main loop
    def __init__(self, draw_fn = None, tick_fn = None, event_fn = None, key_fn=None, resize_fn = None, mouse_fn = None, window_size=(800,600), fullscreen=False):    
        #self.init_pygame(window_size[0], window_size[1], fullscreen)
        self.init_pyglet(window_size)
        self.fps = 60
        
        self.resize_fn = resize_fn
        self.draw_fn = draw_fn
        self.tick_fn = tick_fn        
        self.key_fn = key_fn
        self.mouse_fn = mouse_fn        
        self.running = True
        
    # handles shutdown
    def quit(self):
        self.running = False
        pyglet.app.exit()
        
    # this is the redraw code. Add drawing code between the "LOCK" and "END LOCK" sections
    def flip(self):       
          if self.draw_fn:
            self.draw_fn()
          
    #frame loop. Called on every frame. all calculation shpuld be carried out here     
    def tick(self, delta_t):  
        time.sleep(0.002) # yield!               
        if self.tick_fn:
            self.tick_fn()
      
                                
    #main loop. Just runs tick until the program exits     
    def main_loop(self):
        pyglet.clock.schedule_interval(self.tick, 1.0/self.fps)
        pyglet.app.run()
         
     
