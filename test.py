import numpy as np
from environment import AegisNepEnv
env = AegisNepEnv()
for episode in range(3):
    obs, info = env.reset(seed=episode)
    print(f"Episode {episode}")

    for day in range(400):
        action = env.action_space.sample()
        obs, reward, termianted, truncated, info = env.step(action)

        if np.any(np.isnan(obs)) or np.any(np.isinf(obs)):
            print(f"Broken at day {day}: found nan/inf in the obs")
            break

        if termianted or truncated:
            print(f"Ended at day {day} (terminated = {termianted}, truncated = {truncated})")
            print(f"Final mass : {obs[6]:.1f}kg Final fault_state {obs[19]}")
            break
        else:
            print("Ran the full 400 days without ending - check if that's expected")