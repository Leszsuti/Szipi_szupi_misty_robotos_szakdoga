import math
import copy
import time
from multiprocessing import Manager
import random


def meter_to_pixel(meter):
    return meter * 200

def meter_per_sec_to_pixel(meter_per_sec):
    return meter_per_sec / 60 * 200

def pixel_to_meter(pixel):
    return pixel / 200

def rotate(x, y, angle):
    a = math.radians(angle)
    return (
        x * math.cos(a) - y * math.sin(a),
        x * math.sin(a) + y * math.cos(a)
    )

def is_in_rect(x, y, rect_x, rect_y, width, height):
    return x >= rect_x and y >= rect_y and x < rect_x + width and y < rect_y + height

def is_pixel_color(pixel, color, surface):
    return surface.get_at(pixel)[:3] == color

def is_pixel_color_list(pixel, color_list, surface):
    for color in color_list:
        if surface.get_at(pixel)[:3] == color:
            return True
    return False

def s_blit(surface1, surface2):
    surface11 = surface1.copy()
    surface11.blit(surface2, (0,0))
    return surface11

def sign(x):
    if x < 0:
        return -1
    return 1

def clamp(x, minimum, maximum):
    if x < minimum:
        return minimum
    if x > maximum:
        return maximum
    return x

def multiply_tuple(tuple_in, multiplier):
    return tuple(item * multiplier for item in tuple_in)

class RobotData:
    def __init__(self, b_fl, b_fr, b_bl, b_br, d_fl, d_fc, d_fr, d_bc, target_visible, target_pos_in_view, timestamp = None):
        self.b_fl = b_fl
        self.b_fr = b_fr
        self.b_bl = b_bl
        self.b_br = b_br
        self.d_fl = d_fl
        self.d_fc = d_fc
        self.d_fr = d_fr
        self.d_bc = d_bc
        self.target_visible = target_visible
        self.target_pos_in_view = target_pos_in_view
        if timestamp is None:
            self.timestamp = time.time()
        else:
            self.timestamp = timestamp

class PlaygroundDataOperator:
    def __init__(self, manager):
        self.robot_data_buffer = []
        self.delay = 0.8
        self.delay_random_range = 0.1
        self.robot_data = manager.dict({
            "b_fl": 0,
            "b_fr": 0,
            "b_bl": 0,
            "b_br": 0,
            "d_fl": 0,
            "d_fc": 0,
            "d_fr": 0,
            "d_bc": 0,
            "target_visible": False,
            "target_pos_in_view": 0,
            "timestamp": 0
        })

        self.command = manager.dict()
        self.command["reset"] = False
        self.command["stop"] = False
        self.command["started"] = False

        self.robot_input = manager.dict({
            "fw": 0,
            "yaw": 0
        })
    def reset(self):
        self.robot_data_buffer.clear()
        self.robot_data["b_fl"] = 0
        self.robot_data["b_fr"] = 0
        self.robot_data["b_bl"] = 0
        self.robot_data["b_br"] = 0

        self.robot_data["d_fl"] = 0
        self.robot_data["d_fc"] = 0
        self.robot_data["d_fr"] = 0
        self.robot_data["d_bc"] = 0

        self.robot_data["target_visible"] = False
        self.robot_data["target_pos_in_view"] = 0
        self.robot_data["timestamp"] = 0

    def set_robot_data(self, robot_data):
        self.robot_data_buffer.append(robot_data)
        while len(self.robot_data_buffer) > 0:
            i = self.robot_data_buffer[0]
            if i.timestamp >= time.time() - (self.delay + (random.randint(int(-self.delay_random_range * 100), int(self.delay_random_range * 100)) * 0.01)):
                break
            self.robot_data["b_fl"] = i.b_fl
            self.robot_data["b_fr"] = i.b_fr
            self.robot_data["b_bl"] = i.b_bl
            self.robot_data["b_br"] = i.b_br

            self.robot_data["d_fl"] = i.d_fl
            self.robot_data["d_fc"] = i.d_fc
            self.robot_data["d_fr"] = i.d_fr
            self.robot_data["d_bc"] = i.d_bc

            self.robot_data["target_visible"] = i.target_visible
            self.robot_data["target_pos_in_view"] = i.target_pos_in_view
            self.robot_data["timestamp"] = i.timestamp

            self.robot_data_buffer.pop(0)

    def get_robot_data(self):
        return RobotData(
            b_fl=self.robot_data["b_fl"],
            b_fr=self.robot_data["b_fr"],
            b_bl=self.robot_data["b_bl"],
            b_br=self.robot_data["b_br"],

            d_fl=self.robot_data["d_fl"],
            d_fc=self.robot_data["d_fc"],
            d_fr=self.robot_data["d_fr"],
            d_bc=self.robot_data["d_bc"],

            target_visible=self.robot_data["target_visible"],
            target_pos_in_view=self.robot_data["target_pos_in_view"],
            timestamp=self.robot_data["timestamp"]
        )
    def set_robot_input(self, fw, yaw):
        self.robot_input["fw"] = fw
        self.robot_input["yaw"] = yaw
    def get_robot_input(self):
        return self.robot_input.copy()




# cx, cy = self.x, self.y
#         radius = self.view_data["max_distance"]
#         points = [(cx, cy)]
#         for angle in range(self.angle - self.view_data["angle"], self.angle + self.view_data["angle"]):
#             rad = math.radians(angle - 90)
#             x = cx + math.cos(rad) * radius
#             y = cy + math.sin(rad) * radius
#             points.append((x, y))
#         pygame.draw.polygon(screen, W_SENSOR_COLOR, points)