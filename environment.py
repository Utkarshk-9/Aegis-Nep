
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class AegisNepEnv(gym.Env):
    def __init__(self):
     super().__init__()
     #Room1: Continuous Action Gimbals [Throttle%, Azimuth, Elevation]
     self.action_space = spaces.Box(
        low = np.array ([0.0,-1.0,-1.0]),
        high = np.array ([1.0,1.0,1.0]),
        dtype = np.float32
     )

     # Room1: 14-D Telemetry Output
     self.observation_space = spaces.Box(
        low =-np.inf,
        high = np.inf,
        shape = (14,),
        dtype = np.float32
     )

    #Time_Step from Geo Orbit to Mars Interception
     self.current_steps = 0
     self.max_steps = 200

   #Room 2
    def reset(self, seed =None , options=None):
      super().reset(seed = seed)

       #Reset internal time tracking clock back to Day 0.
      self.current_steps = 0
      observation = np.zeros(14,dtype = np.float32)

      #J2000 Baseline Coordinates (Earth Orbit Escape Line-up positions)
      observation[0] = 1.496e11 #SpaceCraft Position X
      observation[1] = 0.0 #SpaceCraft Position Y
      observation[2] = 0.0 #SpaceCraft Positon Z

      observation[3] = 0.0 #SpaceCraft Velocity VX
      observation[4] = 29780.0 #SpaceCraft Velocity VY (approx.. earth's orbital speed in m/s)
      observation[5] = 0.0 #SpaceCraft Veloctiy VZ
      observation[6] = 12000.0 #Initial SpaceCraft Launch Wet Mass (Kg)
      observation[7] = 600.0 # Full Starting Ion Grid Operational Potential (Volts)
      
   #Storage PipeLine
      info = {}
      return observation, info


