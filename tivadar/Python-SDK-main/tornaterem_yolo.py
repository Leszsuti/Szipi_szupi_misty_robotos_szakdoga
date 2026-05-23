import gymnasium as gym
from gymnasium import spaces
import numpy as np
from csinaljonmarvalamit import *
import threading
import time
import keyboard

class RewardLogger:
    def __init__(self):
        self.reward_list = []
        self.reward_sum = 0
        self.reward_list_list = []
    def add(self, reward):
        self.reward_list.append(reward)
        self.reward_sum += reward
    def next_round(self):
        self.reward_list_list.append(self.reward_list)
        self.reward_list = []
        self.reward_sum = 0
    def to_string_next_round(self):
        out = "Rewards:\n"
        for i in self.reward_list_list:
            out += f"{sum(i)}, {i}\n"
        return out
    def to_string(self):
        out = "Rewards:\n"
        out += f"{self.reward_sum}"
        return out


class DataPocket:
    def __init__(self,
                 x_diff = 0,
                 visible = 0,
                 d_left = 0,
                 d_center = 0,
                 d_right = 0,
                 d_back = 0,
                 b_fl = 0,
                 b_fr = 0,
                 b_bl = 0,
                 b_br = 0,
                 linear_v = 0,
                 angular_v = 0,
                 reward = 0):
        self.x_diff = x_diff
        self.visible = visible
        self.d_left = d_left
        self.d_center = d_center
        self.d_right = d_right
        self.d_back = d_back
        self.b_fl = b_fl
        self.b_fr = b_fr
        self.b_bl = b_bl
        self.b_br = b_br
        self.linear_v = linear_v
        self.angular_v = angular_v
        self.reward = reward
    def to_list(self):
        l = list()
        l.append(self.x_diff)
        l.append(self.visible)
        l.append(self.d_left)
        l.append(self.d_center)
        l.append(self.d_right)
        l.append(self.d_back)
        l.append(self.b_fl)
        l.append(self.b_fr)
        l.append(self.b_bl)
        l.append(self.b_br)
        l.append(self.linear_v)
        l.append(self.angular_v)
        l.append(self.reward)
        return l

class DataContainer:
    def __init__(self, size):
        self.size = size
        self.data_list = list()
        for i in range(size):
            self.data_list.append(DataPocket())
    def push(self, data:DataPocket):
        self.data_list.append(data)
        if len(self.data_list) > self.size:
            self.data_list.pop(0)
    def to_list(self):
        l = list()
        for d in self.data_list:
            l.extend(d.to_list())
        return l



class MistyEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.frame_manager = FrameManager()
        self.step_counter = 0
        self.stopped = False
        self.data_container = DataContainer(8)
        self.reward_logger = RewardLogger()

        self.action_space = spaces.Box(
            low=-1,
            high=1,
            shape=(2,),
            dtype=np.float32
        )
        self.observation_space = spaces.Box(
            low=-1,
            high=1,
            shape=(13 * self.data_container.size,),
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
        obs = self.get_current_observation(0,0,0)
        return obs, {}

    def step(self, action):
        action = np.clip(action, -1, 1)
        fw = float(action[0] * 16)
        yaw = float(action[1] * 32)
        self.tivadar.drive(fw, yaw)
        frame_str = self.get_frame_string(fw,yaw)

        reward = self.request_reward(action[0],action[1])
        frame_str += f"\nreward: {reward}"
        self.frame_manager.save_numbered_frames(self.tivadar.state.get_current_frame(),"normal",frame_str)
        obs = self.get_current_observation(action[0],action[1],reward)
        cv2.imshow("normal",self.tivadar.state.get_current_frame())
        yolo_rectangle = self.tivadar.yolo_misty.get_something_position(self.tivadar.state.get_current_frame(),self.tivadar.target_object_id,get_img=True)
        if yolo_rectangle is not None:
            cv2.imshow("yolo",yolo_rectangle.img)
        key = cv2.waitKey(1)

        self.reward_logger.add(reward)

        terminated = self.is_terminated()
        truncated = False
        if key == ord('q'):
            truncated = True
        if key == ord('t'):
            terminated = True

        if truncated:
            print('truncated')
            self.reward_logger.next_round()
            print(self.reward_logger.to_string_next_round())
            self.tivadar.misty.stop()
        if terminated:
            print('terminated, wasd esc')
            self.reward_logger.next_round()
            print(self.reward_logger.to_string_next_round())
            self.tivadar.misty.stop()
            self.tivadar.wasd()

        self.step_counter += 1
        print(str(self.step_counter) + ".")
        print(self.reward_logger.to_string())
        info = {}
        return obs, reward, terminated, truncated, info

    def clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)

    def get_current_observation(self, fw, yaw, reward):
        target_pos = self.tivadar.get_target_position_yolo()
        visible = 1
        if target_pos is None:
            target_pos = 0
            visible = 0
        distances = self.tivadar.state.get_current_distances()
        bumps = self.tivadar.state.get_current_bumps()
        stopped_number = 0
        if self.stopped:
            stopped_number = 1

        data_pocket = DataPocket(x_diff=target_pos,
                                 visible=visible,
                                 d_left= distances.left,
                                 d_center= distances.center,
                                 d_right= distances.right,
                                 d_back= distances.back,
                                 b_fl = bumps.get_front_left(),
                                 b_fr = bumps.get_front_right(),
                                 b_bl = bumps.get_back_left(),
                                 b_br = bumps.get_back_right(),
                                 linear_v = fw,
                                 angular_v = yaw,
                                 reward = reward)
        self.data_container.push(data_pocket)
        obs = self.data_container.to_list()

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
        target_pos = self.tivadar.get_target_position_yolo()

        if target_pos is None:
            yaw_reward = yaw * 0.1
        else:
            x_diff_reward = (1 - abs(target_pos))
            fw_reward = max(fw,0) * x_diff_reward

        if bumps.front_left or bumps.front_right or bumps.back_left or bumps.back_right:
            bump_reward = -4
        if distances.center < 0.3 and target_pos is not None:
            distance_reward = x_diff_reward
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
        frame_str = (
                     f"fw: {fw}\n"
                     f"yaw: {yaw}\n\n"
                     f"Distances:\n"
                     f"left: {distances.left}\n"
                     f"right: {distances.right}\n"
                     f"center: {distances.center}\n"
                     f"back: {distances.back}\n\n"
                     f"Bumps:\n"
                     f"front_left: {bumps.front_left}\n"
                     f"front_right: {bumps.front_right}\n"
                     f"back_left: {bumps.back_left}\n"
                     f"back_right: {bumps.back_right}\n\n"
                     f"target_pos: {self.tivadar.get_target_position_yolo()}")

        return frame_str







