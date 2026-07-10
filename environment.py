import utilis
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
        shape = (20,),
        dtype = np.float32
     )
    #Time_Step from Geo Orbit to Mars Interception
     self.current_steps = 0
     self.max_steps = 3650

   #Room 2
    def reset(self, seed=None, options=None):
      super().reset(seed = seed)

       #Reset internal time tracking clock back to Day 0.
      self.current_steps = 0
      observation = np.zeros(20,dtype = np.float32)

      #J2000 Baseline Coordinates (Earth Orbit Escape Line-up positions)
      observation[0] = 1.496e11 #SpaceCraft Position X
      observation[1] = 0.0 #SpaceCraft Position Y
      observation[2] = 0.0 #SpaceCraft Positon Z

      observation[3] = 0.0 #SpaceCraft Velocity VX
      observation[4] = 29780.0 #SpaceCraft Velocity VY (approx.. earth's orbital speed in m/s)
      observation[5] = 0.0 #SpaceCraft Veloctiy VZ
      observation[6] = 12000.0 #Initial SpaceCraft Launch Wet Mass (Kg)
      observation[7] = 600.0 # NASA Hall-Effect spec
      self.state = np.copy(observation)
   #Storage PipeLine
      info = {}
      return observation, info
   
   #Room 3: Engine Loop- Executes in every single simulation day,,

    def step(self, action):
      #Advance the clock by day 1 steps
      self.current_steps += 1

      #Continuous 3D Actions Output
      throttle = action[0] #Range [0.0 , 1.0]
      azimuth = action[1] #Range [-1.0 , 1.0]
      elevation = action[2] # Range [-1.0, 1.0]

      #Pull Current 6d State [Position, Velocities] out of internal state array
      #For now slicing the first 6 elements of observation tracking matrix
      current_state_6d = self.state[:6]
      current_mass = self.state[6] #Live Tracking Mass Coordinates (Initially 12000kg)
      current_voltage = self.state[7] #Live Tracking Discharge Potential (initially 600V)

      #PHASE 2B: Propulsion and Mass Depletion 
      F_max_newtons = 0.60  #Maximum continuous engine force (Newtons)
      mdot_max_kg_per_sec = 5.02e-5 #Maximum Xenon propellnat consumption(kg/s)
      dt_seconds = 8640.0  #High Precision Time Interval (Exactly 0.1 Earth Days)

      #Calculating active thrust force magnitude and linear burn depletion
      active_thrust_magnitude = throttle * F_max_newtons
      fuel_burned_this_step = throttle *mdot_max_kg_per_sec * dt_seconds

      #Mass Conservation Law: Updating vehicle tracking weight sadely down
      #Clamping the spacecraft mass to ensure it can never drop below its dry structural weight

      next_mass = max(7000.0, current_mass - fuel_burned_this_step)
   
      #Resolving 3D thrust vector using apatial steering tracking angles
      thrust_vector = np.array([
        active_thrust_magnitude * np.cos(azimuth) * np.cos(elevation),
        active_thrust_magnitude * np.sin(azimuth) *  np.cos(elevation),
        active_thrust_magnitude * np.sin(elevation)], dtype=np.float32)
      
      #Moving 3D coordinates vector positions for Earth and Mars
      #Passing Current simulation step day into analytical keplerian solver
      r_earth = utilis.get_planetary_ephemeris(self.current_steps,planet_flag="Earth")
      r_mars = utilis.get_planetary_ephemeris(self.current_steps,planet_flag="Mars")
      
      #Calling Rk 4 solver from utilis to slide space cooridnates forward 1 Day
      #dt_seconds = 86400.00 (total sec in exactly 1.0 Earth Day Steps)
      next_6d_state = utilis.rk4_step(
        state_6d=current_state_6d,
        r_earth=r_earth,  # Earth Moving Baseline
        r_mars=r_mars,  # Mars Moving Target
        thrust_vector=thrust_vector,
        mass= next_mass,
        dt_seconds=dt_seconds)
       

      #Updating Physics coordinates straight back into observation array
      observation = np.zeros(20,dtype = np.float32)
      observation[:6] = next_6d_state
      observation[6] = next_mass # Mass
      observation[7] = current_voltage  #NASA Hall _Effect discharge voltage ceiling spec
      
      #Injecting moving planet position coordinates into relacie observation tracking slots
      #Live Radar to track Earth and Mars position
      observation[8:11] = r_earth
      observation[11:14] = r_mars

      #Stochastic Hardware Observation Parameters
      observation[14] = 1.0  # Grid Heatlh Coefficient (Pristine 1.0 down to Dead 0.0)
      observation[15] = 0.0 #Cumulative failure Probability Risk (Weibull Scale)
      observation[16] = 298.15 #PPU Internal Circuit Temperature: T_PPU (Kelvin)
      observation[17] = 0.0 #Valve Flutter Amplitude
      observation[18] = 0.0 #Cathode Poisioning Contaminatio Score
      observation[19] = 0.0 #Core System Operational Fault State (0.0 Nominal)

      #Updates Observation values back into persistent class memory for next step
      self.state = np.copy(observation)

      #Core Lifecycle Compliance Handshake Tensors
      reward = 0.0
      #Terminal flag catches complete propellant starvationn structural faliures
      terminated = next_mass <= 7000.0
      truncated = self.current_steps >= self.max_steps
      info = {}
      

      return observation,reward,terminated,truncated,info


