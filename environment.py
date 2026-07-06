import gymnasium as gym
import gymnasium as spaces
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