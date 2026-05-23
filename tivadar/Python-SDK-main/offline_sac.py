import gymnasium as gym
from stable_baselines3 import SAC
from stable_baselines3 import PPO
from tornaterem_yolo import *
from stable_baselines3.common.logger import configure

from stable_baselines3.common.callbacks import BaseCallback
import cv2


env = MistyEnv()

model = SAC.load("misty_yolo", env=env)
model.load_replay_buffer("misty_yolo_replay")

new_logger = configure("tmp_log", ["stdout", "csv"])
model.set_logger(new_logger)
updates = 5000
batch_size = 64
for i in range(updates):
    model.train(gradient_steps=1, batch_size=batch_size)
    if i % 500 == 0:
        print(f"{i}/{updates}")

model.save("misty_yolo")
model.save_replay_buffer("misty_yolo_replay")

# del model
#
# model = SAC.load("misty2")
#
# obs, info = env.reset()
#
# while True:
#     action, _states = model.predict(obs, deterministic=True)
#     obs, reward, terminated, truncated, info = env.step(action)
#     if terminated or truncated:
#         obs, info = env.reset()