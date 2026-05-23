import random
from multiprocessing import Process, Queue, Manager
import time

import pygame
import math
# import playground_util as pu
from . import playground_util as pu



#-------Window-------
WIDTH = 1600
HEIGHT = 900

#------Colors--------
BACKGROUND = (19,19,19)
DRAW_COLOR = (255,0,0)
ROBOT_COLOR = (255,255,255)
D_SENSOR_COLOR = (0, 255, 0)
W_SENSOR_COLOR = (0, 255, 255)
TEXT_COLOR = (255,255,255)
TARGET_COLOR = (255,255,0)

#----Robot physics
ROBOT_WIDTH = pu.meter_to_pixel(0.2)
ROBOT_HEIGHT = pu.meter_to_pixel(0.3)
MAX_SPEED = pu.meter_per_sec_to_pixel(0.5)
MAX_STEER_RATE = 0.5

class Robot:
    def __init__(self, screen):
        self.x = screen.get_width()/2
        self.y = screen.get_height()/2
        self.local_corners = [
            (-ROBOT_WIDTH / 2, -ROBOT_HEIGHT / 2),
            (ROBOT_WIDTH / 2, -ROBOT_HEIGHT / 2),
            (ROBOT_WIDTH / 2, ROBOT_HEIGHT / 2),
            (-ROBOT_WIDTH / 2, ROBOT_HEIGHT / 2),
        ]
        self.corners = [(0, 0), (0, 0), (0, 0), (0, 0)]
        self.b_fl = False
        self.b_fr = False
        self.b_bl = False
        self.b_br = False

        self.distance_sensors = [
            {"pos": (-ROBOT_WIDTH/2, -ROBOT_HEIGHT/2), "angle": 0},
            {"pos": (0, -ROBOT_HEIGHT/2), "angle": 0},
            {"pos": (ROBOT_WIDTH/2, -ROBOT_HEIGHT/2), "angle": 0},
            {"pos": (0, ROBOT_HEIGHT / 2), "angle": 180}
        ]
        self.max_distance_m = 4
        self.max_distance = pu.meter_to_pixel(self.max_distance_m)
        self.d_fl = {"start":(0, 0), "end":(0, 0), "distance_px":0, "distance_m":0, "normalized_distance":0}
        self.d_fc = {"start":(0, 0), "end":(0, 0), "distance_px":0, "distance_m":0, "normalized_distance":0}
        self.d_fr = {"start":(0, 0), "end":(0, 0), "distance_px":0, "distance_m":0, "normalized_distance":0}
        self.d_bc = {"start":(0, 0), "end":(0, 0), "distance_px":0, "distance_m":0, "normalized_distance":0}

        self.view_data = {"angle":20, "max_distance":pu.meter_to_pixel(4)}
        self.target_data = {"distance_px":0, "distance_m":0, "angle_from_center_degree":0, "angle_from_center_turns":0, "visible":False, "angle_in_view":0}


        self.angle = 0
        self.angle_speed = 0
        self.normalized_angle_speed = 0
        self.speed = 0
        self.normalized_speed = 0

    def get_robot_data(self):
        target_pos = 0
        if self.target_data["visible"]:
            target_pos = self.target_data["angle_in_view"]
        return pu.RobotData(
            b_fl=self.b_fl,
            b_fr=self.b_fr,
            b_bl=self.b_bl,
            b_br=self.b_br,
            d_fl=self.d_fl["normalized_distance"],
            d_fc=self.d_fc["normalized_distance"],
            d_fr=self.d_fr["normalized_distance"],
            d_bc=self.d_bc["normalized_distance"],
            target_visible=self.target_data["visible"],
            target_pos_in_view=target_pos,
        )

    def draw(self, surface):
        font = pygame.font.SysFont(None, 24)

        robot_surface = pygame.Surface((ROBOT_WIDTH, ROBOT_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(robot_surface, ROBOT_COLOR, (0,0,ROBOT_WIDTH,ROBOT_HEIGHT), border_radius=3)
        rotated_surface = pygame.transform.rotate(robot_surface, -self.angle)
        rect = rotated_surface.get_rect(center=(self.x, self.y))
        surface.blit(rotated_surface, rect)
        if self.b_fl:
            pygame.draw.circle(surface, DRAW_COLOR, self.corners[0],4)
        else:
            pygame.draw.circle(surface, D_SENSOR_COLOR, self.corners[0], 6)
        if self.b_fr:
            pygame.draw.circle(surface, DRAW_COLOR, self.corners[1],4)
        else:
            pygame.draw.circle(surface, D_SENSOR_COLOR, self.corners[1], 6)
        if self.b_bl:
            pygame.draw.circle(surface, DRAW_COLOR, self.corners[2],4)
        else:
            pygame.draw.circle(surface, D_SENSOR_COLOR, self.corners[2], 6)
        if self.b_br:
            pygame.draw.circle(surface, DRAW_COLOR, self.corners[3],4)
        else:
            pygame.draw.circle(surface, D_SENSOR_COLOR, self.corners[3], 6)

        pygame.draw.line(surface, D_SENSOR_COLOR, self.d_fl["start"], self.d_fl["end"], 3)
        pygame.draw.line(surface, D_SENSOR_COLOR, self.d_fc["start"], self.d_fc["end"], 3)
        pygame.draw.line(surface, D_SENSOR_COLOR, self.d_fr["start"], self.d_fr["end"], 3)
        pygame.draw.line(surface, D_SENSOR_COLOR, self.d_bc["start"], self.d_bc["end"], 3)

        text = font.render(f"{self.d_fl['distance_m']:.2f}, {self.d_fl['normalized_distance']:.2f}", True, TEXT_COLOR)
        surface.blit(text, self.d_fl["end"])
        text = font.render(f"{self.d_fc['distance_m']:.2f}, {self.d_fc['normalized_distance']:.2f}", True, TEXT_COLOR)
        surface.blit(text, self.d_fc["end"])
        text = font.render(f"{self.d_fr['distance_m']:.2f}, {self.d_fr['normalized_distance']:.2f}", True, TEXT_COLOR)
        surface.blit(text, self.d_fr["end"])
        text = font.render(f"{self.d_bc['distance_m']:.2f}, {self.d_bc['normalized_distance']:.2f}", True, TEXT_COLOR)
        surface.blit(text, self.d_bc["end"])

        l_end_x, l_end_y = pu.rotate(0, self.view_data["max_distance"], self.angle - self.view_data["angle"] + 180)
        r_end_x, r_end_y = pu.rotate(0, self.view_data["max_distance"], self.angle + self.view_data["angle"] + 180)
        l_end = (self.x + l_end_x, self.y + l_end_y)
        r_end = (self.x + r_end_x, self.y + r_end_y)
        pygame.draw.line(surface, W_SENSOR_COLOR, (self.x, self.y), l_end, 3)
        pygame.draw.line(surface, W_SENSOR_COLOR, (self.x, self.y), r_end, 3)
        text = font.render(f"{self.target_data["distance_m"]:.2f}, {self.target_data["angle_from_center_turns"]:.2f}, {self.target_data["visible"]}, {self.target_data["angle_in_view"]:.2f}", True, TEXT_COLOR)
        surface.blit(text, (self.x, self.y + 60))

    # self.view_data = {"angle": 20, "max_distance": pu.meter_to_pixel(1)}
    # self.target_data = {"distance_px": 0, "distance_m": 0, "angle_from_center_degree": 0, "angle_from_center_turns": 0}
    def set_view(self, target):
        dx = target.get_x() - self.x
        dy = target.get_y() - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        target_angle = math.degrees(math.atan2(dx, -dy))
        relative_angle = target_angle - self.angle
        while relative_angle > 180:
            relative_angle -= 360
        while relative_angle < -180:
            relative_angle += 360
        self.target_data = {
            "distance_px": distance,
            "distance_m": pu.pixel_to_meter(distance),
            "angle_from_center_degree": relative_angle,
            "angle_from_center_turns": relative_angle / 360,
            "visible": abs(relative_angle) < self.view_data["angle"],
            "angle_in_view": relative_angle / self.view_data["angle"],
        }



    def set_bumps(self, track, target):
        self.b_fl = False
        self.b_fr = False
        self.b_bl = False
        self.b_br = False
        surface = pu.s_blit(track.track_surface, target.target_surface)
        x, y = self.corners[0]
        if pu.is_in_rect(x, y, 0, 0, WIDTH, HEIGHT) and pu.is_pixel_color_list((int(x), int(y)), [DRAW_COLOR, TARGET_COLOR], surface):
            self.b_fl = True
        x, y = self.corners[1]
        if pu.is_in_rect(x, y, 0, 0, WIDTH, HEIGHT) and pu.is_pixel_color_list((int(x), int(y)), [DRAW_COLOR, TARGET_COLOR], surface):
            self.b_fr = True
        x, y = self.corners[2]
        if pu.is_in_rect(x, y, 0, 0, WIDTH, HEIGHT) and pu.is_pixel_color_list((int(x), int(y)), [DRAW_COLOR, TARGET_COLOR], surface):
            self.b_bl = True
        x, y = self.corners[3]
        if pu.is_in_rect(x, y, 0, 0, WIDTH, HEIGHT) and pu.is_pixel_color_list((int(x), int(y)), [DRAW_COLOR, TARGET_COLOR], surface):
            self.b_br = True

    def get_distance_sensor_position(self, sensor):
        ox, oy = sensor["pos"]
        rx, ry = pu.rotate(ox, oy, self.angle)
        sx = self.x + rx
        sy = self.y + ry
        angle = self.angle + sensor["angle"]
        return sx, sy, angle

    def set_distance_sensors(self, track, target):
        state_list = []
        surface = pu.s_blit(track.track_surface, target.target_surface)
        for sensor in self.distance_sensors:
            sx, sy, angle = self.get_distance_sensor_position(sensor)
            dx = math.sin(math.radians(angle))
            dy = -math.cos(math.radians(angle))
            found = False
            for i in range(0, self.max_distance):
                px = int(sx + dx * i)
                py = int(sy + dy * i)
                if not pu.is_in_rect(px, py, 0, 0, WIDTH, HEIGHT):
                    break
                if pu.is_pixel_color_list((px,py), [DRAW_COLOR, TARGET_COLOR], surface):
                    state_list.append({"start":(sx,sy), "end":(px,py), "distance_px":i, "distance_m":pu.pixel_to_meter(i), "normalized_distance":pu.pixel_to_meter(i) / self.max_distance_m})
                    found = True
                    break
            if not found:
                state_list.append({"start":(sx,sy), "end":(int(sx + dx * self.max_distance),int(sy + dy * self.max_distance)), "distance_px":self.max_distance, "distance_m":pu.pixel_to_meter(self.max_distance), "normalized_distance":1})
        self.d_fl = state_list[0]
        self.d_fc = state_list[1]
        self.d_fr = state_list[2]
        self.d_bc = state_list[3]

    def set_sensors(self, track, target):
        self.update_corners()
        self.set_bumps(track, target)
        self.set_distance_sensors(track, target)
        self.set_view(target)



    def update_corners(self):
        self.corners = []
        angle = math.radians(self.angle)
        for x, y in self.local_corners:
            rx = x * math.cos(angle) - y * math.sin(angle)
            ry = x * math.sin(angle) + y * math.cos(angle)
            self.corners.append((self.x + rx, self.y + ry))
    def update_wasd(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and not (self.b_fl or self.b_fr or self.b_bl or self.b_br):
            self.angle -= 1
        if keys[pygame.K_d] and not (self.b_fl or self.b_fr or self.b_bl or self.b_br):
            self.angle += 1
        if keys[pygame.K_w] and not (self.b_fl or self.b_fr):
            self.speed = MAX_SPEED
        elif keys[pygame.K_s] and not (self.b_bl or self.b_br):
            self.speed = -MAX_SPEED
        else:
            self.speed = 0

        self.angle = self.angle % 360

        self.x += math.sin(math.radians(self.angle)) * self.speed
        self.y -= math.cos(math.radians(self.angle)) * self.speed


    def update_agent(self, forward, yaw):
        self.normalized_speed += (forward - self.normalized_speed) * 0.125
        self.normalized_speed = pu.clamp(self.normalized_speed, -1, 1)
        self.speed = self.normalized_speed * MAX_SPEED
        if (self.b_fl or self.b_fr) and self.speed >= 0:
            self.normalized_speed = 0
            self.speed = 0
        if (self.b_bl or self.b_br) and self.speed < 0:
            self.normalized_speed = 0
            self.speed = 0
        if not (self.b_fl or self.b_fr or self.b_bl or self.b_br):
            self.normalized_angle_speed += (yaw - self.normalized_angle_speed) * 0.125
            self.normalized_angle_speed = pu.clamp(self.normalized_angle_speed, -1, 1)
            self.angle += self.normalized_angle_speed * MAX_STEER_RATE
        self.angle = self.angle % 360

        self.x += math.sin(math.radians(self.angle)) * self.speed
        self.y -= math.cos(math.radians(self.angle)) * self.speed


    def spawn(self, min_x, max_x, min_y, max_y, min_angle, max_angle):
        self.x = int(random.randint(min_x, max_x))
        self.y = int(random.randint(min_y, max_y))
        self.angle = int(random.randint(min_angle, max_angle))



class Track:
    def __init__(self):
        self.track_surface = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        self.track_surface.fill((0,0,0,0))
        self.drawing = False
        self.last_pos = None
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.drawing = True
                self.last_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.drawing = False
        if event.type == pygame.MOUSEMOTION and self.drawing:
            current_pos = pygame.mouse.get_pos()
            pygame.draw.line(
                self.track_surface,
                DRAW_COLOR,
                self.last_pos,
                current_pos,
                8
            )
            self.last_pos = current_pos
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            self.track_surface.fill((0,0,0,0))
    def draw(self, surface):
        surface.blit(self.track_surface, (0, 0))

class Target:
    def __init__(self):
        self.pos = (0,0)
        self.size = 10
        self.target_surface = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        self.target_surface.fill((0,0,0,0))
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                self.target_surface.fill((0,0,0,0))
                self.pos = pygame.mouse.get_pos()
                pygame.draw.circle(self.target_surface, TARGET_COLOR, self.pos, int(self.size))
    def draw(self, surface):
        surface.blit(self.target_surface, (0, 0))
    def get_x(self):
        return self.pos[0]
    def get_y(self):
        return self.pos[1]


class Playground:
    def __init__(self, operator):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.playground_operator = operator

        self.robot = Robot(self.screen)
        self.track = Track()
        self.target = Target()
        self.running = False
        self.FIXED_DT = 1/60
        self.clock = pygame.time.Clock()
        self.accumulator = 0


    def render(self):
        self.screen.fill(BACKGROUND)
        self.track.draw(self.screen)
        self.target.draw(self.screen)
        self.robot.draw(self.screen)
        pygame.display.flip()

    def update_prepare(self):
        self.track.update()
        self.robot.set_sensors(self.track, self.target)
        self.robot.update_wasd()

    def update_agent(self, forward, yaw):
        self.track.update()
        self.robot.set_sensors(self.track, self.target)
        self.robot.update_agent(forward, yaw)

    def prepare(self):
        self.running = True
        while self.running:
            frame_time = self.clock.tick(60) / 1000
            self.accumulator += frame_time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.track.handle_event(event)
                self.target.handle_event(event)
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                self.running = False
            while self.accumulator >= self.FIXED_DT:
                self.update_prepare()
                self.accumulator -= self.FIXED_DT
                self.playground_operator.set_robot_data(self.robot.get_robot_data())
            self.render()
        self.playground_operator.command["started"] = True

    def run_with_agent(self):
        self.running = True
        while self.running:
            frame_time = self.clock.tick(60) / 1000
            self.accumulator += frame_time
            if self.playground_operator.command["reset"]:
                self.robot.spawn(400,WIDTH - 400,200,HEIGHT - 200,0,360)
                self.playground_operator.reset()
                self.playground_operator.command["reset"] = False
            if self.playground_operator.command["stop"]:
                self.stop()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.track.handle_event(event)
                self.target.handle_event(event)
            while self.accumulator >= self.FIXED_DT:
                self.playground_operator.set_robot_data(self.robot.get_robot_data())
                self.update_agent(self.playground_operator.get_robot_input()["fw"], self.playground_operator.get_robot_input()["yaw"])
                self.accumulator -= self.FIXED_DT
            self.render()



    def stop(self):
        self.running = False
        time.sleep(0.1)
        pygame.quit()


# def render(robot, track, target):
#     screen.fill(BACKGROUND)
#     track.draw(screen)
#     target.draw(screen)
#     robot.draw(screen)
#     pygame.display.flip()
#
#
# def update_physics(dt, robot, track, target):
#     track.update()
#     robot.update_wasd()
#     robot.set_bumps(track, target)
#     robot.set_distance_sensors(track, target)
#     robot.set_view(target)


def main():
    manager = Manager()
    operator = pu.PlaygroundDataOperator(manager)

    playground = Playground(operator)
    playground.prepare()
    playground.stop()

if __name__ == '__main__':
    main()












