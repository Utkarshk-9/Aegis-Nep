import numpy as np

# NASA  Standard Gravitational Parameter Constants (G * MASS)
GM_SUN = 1.32712440018e20
GM_EARTH = 3.986004418e14
GM_MARS = 4.282837e13

def compute_gravitational_acceleration(r_sc, r_earth, r_mars):
    #Calculates the combined 3d Gravitational acceleration Arrow acting on a SpaceCraft

    #Acceleration from the Sun (Sun is at [0,0,0])
    dist_sun = np.linalg.norm(r_sc)
    a_sun = (GM_SUN / (dist_sun ** 3)) * r_sc

    #Accleration form Earth
    rel_earth = r_sc - r_earth
    dist_earth = np.linalg.norm(r_earth)
    a_earth = (GM_EARTH /(dist_earth ** 3)) * rel_earth

    #Accleration from Mars
    rel_mars = r_sc - r_mars
    dist_mars = np.linalg.norm(r_mars)
    a_mars = (GM_MARS / (dist_mars ** 3)) * rel_mars

    #Total vector Sum: Combining all 3 accleration vectors into one main vector
    return a_sun + a_earth + a_mars

