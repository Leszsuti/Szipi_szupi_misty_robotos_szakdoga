import gymnasium as gym
from gymnasium import spaces
import numpy as np
from csinaljonmarvalamit import *
import threading
import time
import keyboard

class MistyEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.frame_manager = FrameManager()
        self.step_counter = 0

        self.action_space = spaces.Box(
            low=-1,
            high=1,
            shape=(2,),
            dtype=np.float32
        )
        self.observation_space = spaces.Box(
            low=-1,
            high=1,
            shape=(1,),
            dtype=np.float32
        )

        # self.observation_space = spaces.Box(
        #     low=0,
        #     high=255,
        #     shape=(320, 240, 3),
        #     dtype=np.uint8
        # )

        self.tivadar = Tivadar()
        self.tivadar.start_events()


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        val = self.tivadar.get_current_observation_easy_mode()
        obs = np.array([val if val is not None else 0.5], dtype=np.float32)
        return obs, {}

    def step(self, action):
        self.step_counter += 1
        print(self.step_counter)
        action = np.clip(action, -1, 1)
        yaw = float(action[0] * 30)
        yaw = self.clamp(yaw, -30, 30)
        fw = float(action[1]) > 0
        gym_data_before = self.tivadar.get_gym_data()

        sec = 1
        print(type(fw))
        print(fw)
        if fw:
            print("valami")
            self.tivadar.drive_time(100, 0, sec)
        else:
            self.tivadar.drive_yaw(yaw, sec)

        self.tivadar.interrupt_while_robot_is_moving(1, 4)

        self.tivadar.update_x_diff()
        current_x_diff = self.tivadar.get_current_observation_easy_mode()
        obs = np.array([current_x_diff], dtype=np.float32)
        reward = self.tivadar.request_reward(yaw_from_agent=yaw, forward_from_agent=fw)
        gym_data_after = self.tivadar.get_gym_data()

        # self.frame_manager.save_numbered_frames(
        #     self.tivadar.get_current_observation(),
        #     "observation",
        #     f"agent[ yaw:{yaw} fw:{fw} reward:{reward} ]   trainer[yaw:{gym_data.turn} fw:{gym_data.forward} avg_x:{gym_data.avg_x} ]"
        # )
        # self.frame_manager.counter-=1
        self.frame_manager.save_numbered_frames(
            gym_data_after.diff_image,
            "observation_diff",
            f"agent[\nyaw:{yaw}\nfw:{fw}\nreward:{reward}\n]\ntrainer[\nx_diff:{gym_data_after.x_diff}\nfw:{gym_data_after.forward}\nprev_x_diff:{gym_data_after.prev_x_diff}\n]"
        )
        print(f"agent[\nyaw:{yaw}\nfw:{fw}\nreward:{reward}\n]\ntrainer[\nx_diff:{gym_data_after.x_diff}\nfw:{gym_data_after.forward}\nprev_x_diff:{gym_data_after.prev_x_diff}\n]")
        cv2.imshow("hsv",gym_data_after.diff_image)
        cv2.waitKey(1)



        terminated = False
        truncated = False
        if keyboard.is_pressed('q'):
            truncated = True
        if keyboard.is_pressed('e'):
            terminated = True

        info = {}

        return obs, reward, terminated, truncated, info

    def clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)
