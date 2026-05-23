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
        self.stopped = False

        self.action_space = spaces.Box(
            low=-1,
            high=1,
            shape=(3,),
            dtype=np.float32
        )
        self.observation_space = spaces.Box(
            low=-4,
            high=4,
            shape=(9,),
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
        obs = self.get_current_observation()
        return obs, {}

    def step(self, action):
        self.step_counter += 1
        print(self.step_counter)
        action = np.clip(action, -1, 1)
        fw = float(action[0] * 10)
        yaw = float(action[1] * 10)
        # stop = float(action[2])
        self.tivadar.drive(fw, yaw)
        # if stop > 0:
        #     self.tivadar.misty.stop()
        #     self.stopped = True
        # else:
        #     self.stopped = False
        frame_str = self.get_frame_string(fw,yaw)
        self.tivadar.update_x_diff()

        reward = self.request_reward(fw,yaw)
        frame_str += f"\nreward: {reward}"
        self.frame_manager.save_numbered_frames(self.tivadar.state.get_current_frame(),"normal",frame_str)
        obs = self.get_current_observation()
        cv2.imshow("hsv",self.tivadar.last_hsv_frame)
        cv2.imshow("normal",self.tivadar.state.get_current_frame())
        cv2.waitKey(1)



        terminated = self.is_terminated()
        truncated = False
        if keyboard.is_pressed('q'):
            truncated = True
        if keyboard.is_pressed('t'):
            terminated = True

        if truncated:
            print('truncated')
            self.tivadar.misty.stop()
        if terminated:
            self.tivadar.misty.stop()
            while True:
                print("terminated, press e : ",self.tivadar.state.get_current_bumps().to_string())
                if keyboard.is_pressed('e'):
                    break

        info = {}

        return obs, reward, terminated, truncated, info

    def clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)

    def get_current_observation(self):
        x_diff = self.tivadar.current_x_diff
        if x_diff is None:
            x_diff = 0.5
        distances = self.tivadar.state.get_current_distances()
        bumps = self.tivadar.state.get_current_bumps()
        stopped_number = 0
        if self.stopped:
            stopped_number = 1
        obs = list()
        obs.append(x_diff)
        obs.append(distances.left)
        obs.append(distances.center)
        obs.append(distances.right)
        obs.append(distances.back)
        obs.append(bumps.get_front_left())
        obs.append(bumps.get_front_right())
        obs.append(bumps.get_back_left())
        obs.append(bumps.get_back_right())
        # obs.append(stopped_number)
        return np.array(obs, dtype=np.float32)


    def request_reward(self,fw,yaw):
        fw_reward = 0
        yaw_reward = 0
        bump_reward = 0
        x_diff_reward = 0
        distance_reward = 0
        bumps = self.tivadar.state.get_current_bumps()
        distances = self.tivadar.state.get_current_distances()
        x_diff = self.tivadar.current_x_diff

        if x_diff is None:
            yaw_reward = yaw * 0.2
        else:
            x_diff_reward = (0.5 - abs(x_diff)) + 0.5
            fw_reward = fw * x_diff_reward

        if bumps.front_left or bumps.front_right or bumps.back_left or bumps.back_right:
            bump_reward = -2
        if (bumps.front_left or bumps.front_right) and x_diff is not None:
            bump_reward = x_diff_reward
        reward = x_diff_reward + distance_reward + fw_reward + yaw_reward + bump_reward
        return reward

    def is_terminated(self):
        bumps = self.tivadar.state.get_current_bumps()
        if bumps.front_left or bumps.front_right or bumps.back_left or bumps.back_right:
            return True
        return False

    def get_frame_string(self, fw, yaw):
        distances = self.tivadar.state.get_current_distances()
        bumps = self.tivadar.state.get_current_bumps()
        frame_str = (f"Distances:\n"
                     f"fw: {fw}\n"
                     f"yaw: {yaw}\n"
                     f"left: {distances.left}\n"
                     f"right: {distances.right}\n"
                     f"center: {distances.center}\n"
                     f"back: {distances.back}\n"
                     f"Bumps:\n"
                     f"front_left: {bumps.front_left}\n"
                     f"front_right: {bumps.front_right}\n"
                     f"back_left: {bumps.back_left}\n"
                     f"back_right: {bumps.back_right}\n"
                     f"x_diff: {self.tivadar.current_x_diff}")

        return frame_str







