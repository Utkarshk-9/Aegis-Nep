import numpy as np

# NASA  Standard Gravitational Parameter Constants (G * MASS)
GM_SUN = 1.32712440018e20
GM_EARTH = 3.986004418e14
GM_MARS = 4.282837e13

def compute_gravitational_acceleration(r_sc, r_earth, r_mars):
    #Calculates the combined 3d Gravitational acceleration Arrow acting on a SpaceCraft

    #Acceleration from the Sun (Sun is at [0,0,0])
    dist_sun = np.linalg.norm(r_sc)
    a_sun = -(GM_SUN / (dist_sun ** 3)) * r_sc

    #Accleration form Earth
    rel_earth = r_sc - r_earth
    dist_earth = np.linalg.norm(rel_earth)
    a_earth = -(GM_EARTH /(dist_earth ** 3)) * rel_earth

    #Accleration from Mars
    rel_mars = r_sc - r_mars
    dist_mars = np.linalg.norm(rel_mars)
    a_mars = -(GM_MARS / (dist_mars ** 3)) * rel_mars
    #Total vector Sum: (Combining all 3 accleration vectors into one main vector)
    return a_sun + a_earth + a_mars

#RK4 Integration
def get_state_derivatives(state_6d,r_earth,r_mars,thrust_vector,mass):
    #Unpack arrays into independent 3D Vectors,,
    r_sc =state_6d[:3]
    v_sc = state_6d[3:]
    #Calling gravitational vector arrow solver
    a_grav = compute_gravitational_acceleration(r_sc,r_earth,r_mars)
    #Calculating active Hall-Effect thruster acceleration vector
    a_thrust = thrust_vector / mass
    #Combined gravity arrows and thrust force into acceleration
    a_total = a_grav + a_thrust

    #Pack Derivatives: [dr/dt, dv/dt] which translates structurally to [velocity,accleration]
    derivatives = np.zeros(6,dtype =np.float32)
    derivatives[:3] = v_sc      #Time change in postion = Velocity
    derivatives[3:] = a_total   #Time change in velocity = acceleration

    return derivatives

def rk4_step(state_6d, r_earth, r_mars, thrust_vector, mass, dt_seconds):
    #Executes 4th-order Runge-Kutta numerical Integration over dt time interval
    #Checkpoint k1: Derivatives at the absolute current position
    k1 = get_state_derivatives(state_6d,r_earth,r_mars,thrust_vector,mass)
    #Checkpoint k2: Predict state at Midday using k1, then re-sample derivatives
    state_k2 = state_6d +(dt_seconds * k1 / 2.0)
    k2 = get_state_derivatives(state_k2,r_earth,r_mars,thrust_vector,mass)
    #Checkpoint k3: Predict state at Midday using k2,then re-sample derivatives
    state_k3 = state_6d +(dt_seconds * k2 / 2.0)
    k3 = get_state_derivatives(state_k3,r_earth,r_mars,thrust_vector,mass)
    #CheckPoint k4: Predict state derivative Midnight using k3, then sample final derivative
    state_k4 = state_6d +(dt_seconds * k3)
    k4 = get_state_derivatives(state_k4,r_earth,r_mars,thrust_vector,mass) 

    #Run the high-precision weighted average combination sequence to slide the state vector forward
    next_state_6d = state_6d + (dt_seconds/6.0) * (k1 + 2.0*k2 +2.0*k3 +k4)
    return next_state_6d
