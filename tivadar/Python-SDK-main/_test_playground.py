import gymnasium as gym
from stable_baselines3 import SAC
from stable_baselines3 import PPO
from tornaterem_playground import *

from stable_baselines3.common.callbacks import BaseCallback
import cv2

def main():
    env = MistyEnv()


    model = SAC.load("misty_sim")

    obs, info = env.reset()

    while not env.playground_operator.command["started"]:
        time.sleep(0.1)
    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            obs, info = env.reset()

        if keyboard.is_pressed('q'):
            break
    env.playground_operator.command["stop"] = True
    env.close()

if __name__ == "__main__":
    main()
#
# env.tivadar.stop_events()
# env.tivadar.misty.stop()
# cv2.destroyAllWindows()







