
from ..sim import sphere_sim
              
if __name__=="__main__":
    sphere = sphere_sim.make_viewer(test_render=True, show_touches=True)
    sphere.start()
    
   