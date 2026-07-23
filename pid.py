import numpy as np
from environment import AegisNepEnv

env = AegisNepEnv()
obs, info = env.reset(seed=0)

# ---------------- PID Gains ----------------
# Starting values for NORMALIZED error (0 → 1)
Kp = 0.8
Ki = 0.01
Kd = 0.2

integral_error = 0.0
previous_distance = None
initial_distance = None

for day in range(1, 400):

    # ---------------------------------------
    # Current spacecraft & Mars positions
    # ---------------------------------------
    sc_pos = obs[0:3]
    mars_pos = obs[11:14]

    # Current straight-line distance
    distance = np.linalg.norm(mars_pos - sc_pos)

    # Save the initial distance once
    if initial_distance is None:
        initial_distance = distance

    # Save previous distance on first iteration
    if previous_distance is None:
        previous_distance = distance

    # ---------------------------------------
    # PID Controller
    # ---------------------------------------

    # Normalized error (1.0 at launch, 0.0 at Mars)
    error = distance / initial_distance

    # Integral term
    integral_error += error

    # Derivative term
    previous_error = previous_distance / initial_distance
    derivative_error = error - previous_error

    # Store for next timestep
    previous_distance = distance

    # Raw PID output
    raw_throttle = (
        Kp * error +
        Ki * integral_error +
        Kd * derivative_error
    )

    # Clamp throttle
    throttle = np.clip(raw_throttle, 0.0, 1.0)

    # ---------------------------------------
    # Phase 3 Safety Logic
    # ---------------------------------------

    ppu_temp = obs[16]
    fault_state = obs[19]

    if ppu_temp > 413.15:
        throttle = min(throttle, 0.3)

    if fault_state >= 2:
        throttle = min(throttle, 0.2)

    if fault_state >= 3:
        throttle = 0.0

    # ---------------------------------------
    # Steering toward Mars
    # ---------------------------------------

    direction = mars_pos - sc_pos

    azimuth = np.arctan2(direction[1], direction[0])
    azimuth = np.clip(azimuth, -1.0, 1.0)

    elevation = 0.0

    action = np.array(
        [throttle, azimuth, elevation],
        dtype=np.float32
    )

    obs, reward, terminated, truncated, info = env.step(action)

    # ---------------------------------------
    # Logging
    # ---------------------------------------

    if day % 20 == 0 or terminated or truncated:
        print(
            f"Day {day:3d} | "
            f"Throttle={throttle:.3f} | "
            f"Error={error:.3f} | "
            f"Distance={distance/1e9:.1f} M km | "
            f"Temp={ppu_temp:.1f} K | "
            f"Fault={fault_state}"
        )

    if terminated or truncated:
        print("\nSimulation Finished")
        print(f"Day: {day}")
        print(f"Final Mass: {obs[6]:.2f} kg")
        print(f"Final Distance: {distance/1e9:.2f} M km")
        break