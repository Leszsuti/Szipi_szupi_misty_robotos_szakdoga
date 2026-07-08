import threading


class GymData:
    def __init__(self, x_diff = None, prev_x_diff = None, forward = None, diff_image = None ):
        self.x_diff = x_diff
        self.prev_x_diff = prev_x_diff
        self.forward=forward
        self.diff_image = diff_image

class HSV:
    def __init__(self, base, range, s_min, s_max, v_min, v_max):
        self.base = base
        self.range = range
        self.s_min = s_min
        self.s_max = s_max
        self.v_min = v_min
        self.v_max = v_max
        self.first_load = True

    def set_base(self, base): self.base = base
    def set_range(self, range): self.range = range
    def set_S_min(self, s_min): self.s_min = s_min
    def set_S_max(self, s_max): self.s_max = s_max
    def set_V_min(self, v_min): self.v_min = v_min
    def set_V_max(self, v_max): self.v_max = v_max
    def save_settings(self):
        with open(".\\frames\\settings.txt", "w") as file:
            str_=f"{self.base}\n{self.range}\n{self.s_min}\n{self.s_max}\n{self.v_min}\n{self.v_max}"
            file.write(str_)
    def load_settings(self):
        try:
            with open(".\\frames\\settings.txt", "r") as file:
                lines = file.readlines()
                self.base = int(lines[0])
                self.range = int(lines[1])
                self.s_min = int(lines[2])
                self.s_max = int(lines[3])
                self.v_min = int(lines[4])
                self.v_max = int(lines[5])
                self.first_load = False
            return True
        except:
            print("be kene allitani a parametereket ocsisajt")
            return False
class Distances:
    def __init__(self, left=0, center=0, right=0, back=0):
        self.left = left
        self.center = center
        self.right = right
        self.back = back
    def set_distance(self, distance, direction):
        if distance > 1:
            distance = 1
        if direction == 'Left':
            self.left = distance
        if direction == 'Center':
            self.center = distance
        if direction == 'Right':
            self.right = distance
        if direction == 'Back':
            self.back = distance
    def to_string(self):
        return f"{self.left} {self.center} {self.right} {self.back}"
    def all_gt_zero(self):
        return self.left > 0 and self.center > 0 and self.right > 0 and self.back > 0

class BumpSensors:
    def __init__(self, front_left = False, front_right = False, back_left = False, back_right = False):
        self.front_left = front_left
        self.front_right = front_right
        self.back_left = back_left
        self.back_right = back_right
    def set_bump_sensor(self, bump_sensor, direction):
        if direction == 'brl':
            self.back_left = bump_sensor
        if direction == 'brr':
            self.back_right = bump_sensor
        if direction == 'bfl':
            self.front_left = bump_sensor
        if direction == 'bfr':
            self.front_right = bump_sensor
    def get_front_left(self):
        if self.front_left: return 1
        return 0
    def get_front_right(self):
        if self.front_right: return 1
        return 0
    def get_back_left(self):
        if self.back_left: return 1
        return 0
    def get_back_right(self):
        if self.back_right: return 1
        return 0
    def to_string(self):
        return f"{self.front_left} {self.front_right} {self.back_left} {self.back_right}"


class MistyState:
    def __init__(self):
        self._current_frame = None
        self._current_move = None
        self._current_yaw = None
        self._current_distances = Distances()
        self._current_bumps = BumpSensors()
        self.lock = threading.Lock()
        self.yaw_lock = threading.Lock()
        self.distance_lock = threading.Lock()
        self.bump_lock = threading.Lock()

    def set_current_frame(self, current_frame):
        with self.lock:
            self._current_frame = current_frame
    def set_current_move(self, current_move):
        with self.lock:
            self._current_move = current_move
    def set_current_yaw(self, current_yaw):
        with self.yaw_lock:
            self._current_yaw = current_yaw
    def set_current_distances(self, current_distance, direction):
        with self.distance_lock:
            self._current_distances.set_distance(current_distance, direction)
    def set_current_bumps(self, bump_sensor, direction):
        with self.bump_lock:
            self._current_bumps.set_bump_sensor(bump_sensor, direction)

    def get_current_frame(self):
        with self.lock:
            if self._current_frame is None:
                return None
            return self._current_frame.copy()
    def get_current_move(self):
        with self.lock:
            if self._current_move is None:
                return None
            return self._current_move.copy()
    def get_current_yaw(self):
        with self.yaw_lock:
            return self._current_yaw
    def get_current_distances(self):
        with self.distance_lock:
            distances = Distances(self._current_distances.left, self._current_distances.center, self._current_distances.right, self._current_distances.back)
            return distances
    def get_current_bumps(self):
        with self.bump_lock:
            bumps = BumpSensors(self._current_bumps.front_left, self._current_bumps.front_right, self._current_bumps.back_left, self._current_bumps.back_right)
            return bumps
