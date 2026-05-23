
import websocket

from mistyPy.Robot import Robot
from mistyPy.Events import Events
import time
import keyboard
import cv2
import numpy as np
import threading
from frames import FrameManager
from util import *
from yolo import *





# 192.168.1.249
class Tivadar:
    def __init__(self, robot = Robot("192.168.1.249")):
        self.misty = robot
        self.frame_manager = FrameManager()
        self.state = MistyState()
        self.yolo_misty = YoloMisty()
        self.target_object_id = 39
        self.image_width = 240
        self.image_height = 320
        self.stream_flag = False
        self.yaw_flag = False
        self.distance_flag = False
        self.bump_flag = False
        self.prev_x_diff = None
        self.current_x_diff = None
        self.hsv = HSV(0, 0, 0, 0, 0, 0)
        self.last_hsv_frame = None
        self.misty.move_head(20, 0 ,0 ,100)

    def get_state(self):
        return self.state

    def get_current_observation(self):
        normal_image = self.state.get_current_frame()
        gray = cv2.cvtColor(normal_image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 32, 64)
        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        obs = cv2.add(normal_image,edges_bgr)
        # obs = cv2.resize(obs, (self.image_width, self.image_height))
        return obs

    def get_current_observation_easy_mode(self):
        x_diff = self.current_x_diff
        if x_diff is None:
            return 0.5
        return x_diff


    def update_x_diff(self):
        self.prev_x_diff = self.current_x_diff
        # self.current_x_diff = self.get_ball_position()
        self.current_x_diff = self.get_target_position_hsv()


    def start_events(self):
        if self.stream_flag is False and self.yaw_flag is False and self.distance_flag is False and self.bump_flag is False:
            self.stream_flag = True
            self.yaw_flag = True
            self.distance_flag = True
            self.bump_flag = True
            t_stream = threading.Thread(target=self.stream, daemon=True)
            t_yaw = threading.Thread(target=self.yaw_event, daemon=True)
            t_distance = threading.Thread(target=self.distance_event, daemon=True)
            t_bump = threading.Thread(target=self.bump_event, daemon=True)
            t_stream.start()
            t_yaw.start()
            t_distance.start()
            t_bump.start()
            while True:
                time.sleep(0.1)
                print("waiting...")
                if self.state.get_current_frame() is not None and self.state.get_current_move() is not None and self.state.get_current_yaw() is not None and self.state.get_current_distances().all_gt_zero():
                    break

    def stop_events(self):
        self.stream_flag = False
        self.yaw_flag = False
        self.distance_flag = False
        self.bump_flag = False
        self.misty.unregister_event('yaw_event')
        self.misty.unregister_event('distance_event')
        self.misty.unregister_event('bump_event')


    def yaw_event(self):
        def yaw_callback(data):
            yaw = data["message"]["yaw"]
            self.state.set_current_yaw(yaw)

        self.misty.register_event(event_name='yaw_event',event_type=Events.IMU,callback_function=yaw_callback, keep_alive=True)
        print("yaw_event started")
        # self.misty.keep_alive()
    def distance_event(self):
        def distance_callback(data):
            self.state.set_current_distances(data["message"]["distanceInMeters"], data["message"]["sensorPosition"])
        self.misty.register_event(event_name='distance_event', event_type=Events.TimeOfFlight, callback_function=distance_callback, keep_alive=True)
    def bump_event(self):
        def bump_callback(data):
            self.state.set_current_bumps(data["message"]["isContacted"], data["message"]["sensorId"])
        self.misty.register_event(event_name='bump_event', event_type=Events.BumpSensor, callback_function=bump_callback, keep_alive=True)


    def drive_time(self, linearVelocity, angularVelocity, sec):
        print("drive started")
        self.misty.drive_time(linearVelocity=linearVelocity, angularVelocity=angularVelocity, timeMs=sec*1000)


    # def fw(self, distance):
    #     distance_counter = DistanceCounter(0.06, distance)
    #     def stop(data):
    #         distance_counter.push(data["message"]["distanceInMeters"])
    #         if distance_counter.counter >= 8:
    #             self.misty.stop()
    #         print(data["message"]["status"], " - ", data["message"]["distanceInMeters"], " - ", distance_counter.counter)
    #
    #     self.misty.register_event(event_name="Time of flight" ,event_type=Events.TimeOfFlight, callback_function=stop, keep_alive=True, debounce=100)
    #     # self.misty.drive(20,0)
    #     self.misty.keep_alive()

    def drive_yaw(self, relative_yaw, sec):
        current_yaw = self.state.get_current_yaw()
        # print(self.state.get_current_yaw())
        target = float((current_yaw + relative_yaw)%360)
        # print(target , "_")
        self.misty.drive_arc(heading=target,radius=0, timeMs=sec*1000, reverse=False)
        # while True:
        #     print(self.state.get_current_yaw())
        #     print(target, "_")
        #     print(((target - self.state.get_current_yaw()) + 180) % 360 - 180, " diff")
        #     if abs(((target - self.state.get_current_yaw()) + 180) % 360 - 180) < 3:
        #         break
        #     time.sleep(0.01)

    def drive(self, linear_velocity, angular_velocity):
        self.misty.drive(linear_velocity,angular_velocity)

    def picture(self, filename, counter):
        misty = self.misty
        base64_ = False
        misty.take_picture(base64=base64_, fileName=filename, width=800,height= 600,displayOnScreen=False,overwriteExisting=True)
        # response = misty.get_image(filename + ".jpg", base64_)
        response = misty.get_image(filename + ".jpg", base64_)
        # response2 = misty.get_image_list()
        if response.status_code != 200:
            print("Szar")
            return
        with open("pictures/pikcsör" + str(counter) + ".jpg", "wb") as f:
            f.write(response.content)
        # print(response.text)
        # print("-------------")
        # print(response2.text)
        img = np.frombuffer(response.content, dtype=np.uint8)
        frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
        cv2.imshow("Misty camera", frame)
        cv2.waitKey(1)

    # ws://192.168.1.249:5678
    # https://github.com/ultralytics/ultralytics/blob/main/README.md
    def stream(self):
        misty = self.misty
        misty.stop_video_streaming()
        time.sleep(1)
        misty.start_video_streaming(5678, 90, self.image_width, self.image_height, 100, False)
        time.sleep(1)
        print("Stream started")

        ws = websocket.WebSocket()
        ws.connect("ws://192.168.1.249:5678")
        i=0
        prev = None
        diff_image_buffer = list()
        while self.stream_flag is True:
            data = ws.recv()
            if isinstance(data, str):
                print(data)
                continue
            img = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(img, cv2.IMREAD_COLOR)

            self.state.set_current_frame(frame)

            # gmask = (green > 110) & (blue < 150) & (red < 150)
            # gm_image = gmask.astype(np.uint8)*255
            # cv2.imshow("Green mask", gm_image)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # blur = cv2.GaussianBlur(gray, (5, 5), 0)
            # edges = cv2.Canny(blur, 100, 150)
            # cv2.namedWindow("Edges", cv2.WINDOW_NORMAL)
            # cv2.resizeWindow("Edges", 480, 640)
            # cv2.imshow("Edges", edges

            if i>=1:
                gray_ = cv2.blur(gray, (2, 2))
                prev_ = cv2.blur(prev, (2, 2))
                difference_ = cv2.absdiff(gray_, prev_)
                difference = difference_ > 16
                diff_image = difference.astype(np.uint8)*255
                diff_image_buffer.append(diff_image)
                if len(diff_image_buffer)>4:
                    diff_image_buffer.pop(0)

                sum_diff_image = diff_image_buffer[0]
                for k in diff_image_buffer:
                    sum_diff_image = cv2.add(sum_diff_image, k)

                kernel = np.ones((2, 2), np.uint8)
                sum_diff_image = cv2.morphologyEx(sum_diff_image, cv2.MORPH_OPEN, kernel)

                self.state.set_current_move(sum_diff_image)
                # cv2.imshow("Diff video", sum_diff_image)
                # if cv2.waitKey(1) == 27:
                #     break
                prev = gray
            if i == 0:
                prev = gray
                i+=1
        misty.stop_video_streaming()
        ws.close()

    def interrupt_while_robot_is_moving(self, delay_sec, threshold_sec):
        # positions = []
        # size = 4
        time.sleep(delay_sec)
        # while True:
        #     time.sleep(0.1)
        #     pos = self.get_ball_position()
        #     if pos is None:
        #         pos=0
        #     positions.append(pos)
        #     if len(positions)>size:
        #         positions.pop(0)
        #     if len(positions)<size or None in positions:
        #         continue
        #     min_=min(positions)
        #     max_=max(positions)
        #
        #     if abs(max_ - min_)<4:
        #         print("positions: ", positions)
        #         break
        threshold = 256
        buffer = []
        size = 8
        up_direction = False
        changed_direction = False
        timer = time.time()
        while True:
            white_pixels = cv2.countNonZero(self.state.get_current_move())
            buffer.append(white_pixels)
            if len(buffer) < size:
                continue
            if len(buffer) > size:
                buffer.pop(0)
            abs_diff_avg=0
            for i in range(len(buffer)-1):
                abs_diff_avg += abs(buffer[i]-buffer[i+1])
            direction_avg = (buffer[-1] - buffer[0])/size
            abs_diff_avg /= size
            if direction_avg > 0:
                up_direction = True
            if up_direction is True and direction_avg < 0:
                changed_direction = True
            # print("direction_avg:", direction_avg, " abs_diff:", abs_diff_avg, "timer:", time.time()-timer)
            if (changed_direction is True and abs_diff_avg < threshold and abs(direction_avg)<threshold/4) or time.time()-timer>threshold_sec:
                break

            time.sleep(0.1)


    def get_target_position_move(self, show = False):
        diff_image = self.state.get_current_move()
        if diff_image is None:
            return None
        sum_y=0
        sum_x=0
        white_counter = 0
        origo_diff_y=None
        origo_diff_x=None
        for y in range(self.image_height):
            for x in range(self.image_width):
                if diff_image[y][x] == 255:
                    sum_y+=y
                    sum_x+=x
                    white_counter+=1
        if white_counter > self.image_width * self.image_height * 0.002:
            avg_y = int(sum_y/white_counter)
            avg_x = int(sum_x/white_counter)

            color_diff = cv2.cvtColor(diff_image, cv2.COLOR_GRAY2BGR)
            color_diff[avg_y-2 : avg_y+2,avg_x-2 : avg_x+2] = (0,255,0)
            diff_image = color_diff

            #balra -0.5 jobbra +0.5
            origo_diff_y=((self.image_height-avg_y)/self.image_height)-0.5
            origo_diff_x=((self.image_width-avg_x)/self.image_width)-0.5
        else:
            print("nincs mozgas")

        if show:
            cv2.namedWindow("Diff3", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Diff3", self.image_width*2, self.image_height*2)
            cv2.imshow("Diff3", diff_image)
            cv2.waitKey(1)
            print("avg_x: ",origo_diff_x)
        self.current_x_diff = origo_diff_x
        return origo_diff_x

    def hsv_trackbar(self):
        self.hsv = HSV(0,89,0,255,0,255)
        cv2.namedWindow("Beallitasok")
        if self.hsv.load_settings() is False:
            cv2.createTrackbar("H_base", "Beallitasok", 0, 179, self.hsv.set_base)
            cv2.createTrackbar("H_range", "Beallitasok", 89, 89, self.hsv.set_range)
            cv2.createTrackbar("S_min", "Beallitasok", 0, 255, self.hsv.set_S_min)
            cv2.createTrackbar("S_max", "Beallitasok", 255, 255, self.hsv.set_S_max)
            cv2.createTrackbar("V_min", "Beallitasok", 0, 255, self.hsv.set_V_min)
            cv2.createTrackbar("V_max", "Beallitasok", 255, 255, self.hsv.set_V_max)
        else:
            cv2.createTrackbar("H_base", "Beallitasok", self.hsv.base, 179, self.hsv.set_base)
            cv2.createTrackbar("H_range", "Beallitasok", self.hsv.range,89, self.hsv.set_range)
            cv2.createTrackbar("S_min", "Beallitasok", self.hsv.s_min ,255, self.hsv.set_S_min)
            cv2.createTrackbar("S_max", "Beallitasok", self.hsv.s_max, 255, self.hsv.set_S_max)
            cv2.createTrackbar("V_min", "Beallitasok", self.hsv.v_min, 255, self.hsv.set_V_min)
            cv2.createTrackbar("V_max", "Beallitasok", self.hsv.v_max, 255, self.hsv.set_V_max)

    def get_target_position_hsv(self, settings_mode = False, print_data=False):
        frame = self.state.get_current_frame()
        if frame is None:
            return None
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv=self.hsv
        if hsv.first_load is True:
            if hsv.load_settings() is False and settings_mode is False:
                if print_data: print("hsv_position_hiba")
                return None
            if hsv.load_settings() is False and settings_mode is True:
                if print_data: print("meg nincs semmi mentve")
        h_low = hsv.base-hsv.range
        h_high = hsv.base+hsv.range

        result_frame = None
        if h_low >= 0 and h_high < 180:
            lower = np.array([h_low, hsv.s_min, hsv.v_min])
            upper = np.array([h_high, hsv.s_max, hsv.v_max])
            result_frame = cv2.inRange(hsv_frame, lower, upper)
        elif h_low < 0 and h_high < 180:
            lower1 = np.array([180 + h_low, hsv.s_min, hsv.v_min])
            upper1 = np.array([179, hsv.s_max, hsv.v_max])
            lower2 = np.array([0, hsv.s_min, hsv.v_min])
            upper2 = np.array([h_high, hsv.s_max, hsv.v_max])
            tmp_frame1 = cv2.inRange(hsv_frame, lower1, upper1)
            tmp_frame2 = cv2.inRange(hsv_frame, lower2, upper2)
            result_frame = cv2.bitwise_or(tmp_frame1, tmp_frame2)
        elif h_low >= 0 and h_high >= 180:
            lower1 = np.array([h_low, hsv.s_min, hsv.v_min])
            upper1 = np.array([179, hsv.s_max, hsv.v_max])
            lower2 = np.array([0, hsv.s_min, hsv.v_min])
            upper2 = np.array([h_high-180, hsv.s_max, hsv.v_max])
            tmp_frame1 = cv2.inRange(hsv_frame, lower1, upper1)
            tmp_frame2 = cv2.inRange(hsv_frame, lower2, upper2)
            result_frame = cv2.bitwise_or(tmp_frame1, tmp_frame2)

        kernel = np.ones((4, 4), np.uint8)
        result_frame = cv2.erode(result_frame, kernel, iterations=1)
        self.last_hsv_frame = result_frame

        if result_frame is None:
            if print_data: print("hsv position hiba")

        sum_y = 0
        sum_x = 0
        white_counter = 0
        origo_diff_y = None
        origo_diff_x = None
        for y in range(self.image_height):
            for x in range(self.image_width):
                if result_frame[y][x] == 255:
                    sum_y += y
                    sum_x += x
                    white_counter += 1
        diff_image=None
        if white_counter > self.image_width * self.image_height * 0.002:
            avg_y = int(sum_y / white_counter)
            avg_x = int(sum_x / white_counter)

            color_diff = cv2.cvtColor(result_frame, cv2.COLOR_GRAY2BGR)
            color_diff[avg_y - 2: avg_y + 2, avg_x - 2: avg_x + 2] = (0, 255, 0)
            diff_image = color_diff

            # balra +0.5 jobbra -0.5
            origo_diff_y = ((self.image_height - avg_y) / self.image_height) - 0.5
            origo_diff_x = ((self.image_width - avg_x) / self.image_width) - 0.5
        else:
            if print_data: print("nincs tény")

        if settings_mode is True and diff_image is not None:
            if print_data: print("avg_x: ",origo_diff_x)
            hsv.save_settings()
        self.current_x_diff = origo_diff_x
        if diff_image is not None:
            self.last_hsv_frame = diff_image
        return origo_diff_x

    def pid(self, target, process_variable):
        diff = (target - process_variable)*0.2
        if diff > 20:
            diff = 20
        if diff < -20:
            diff = -20
        return diff

    def get_gym_data(self):
        if abs(self.get_current_observation_easy_mode()) < 0.1:
            desired_fw = True
        else:
            desired_fw = False
        return GymData(x_diff=self.current_x_diff,prev_x_diff=self.prev_x_diff, diff_image=self.last_hsv_frame, forward=desired_fw)

    def request_reward(self, yaw_from_agent, forward_from_agent):
        obs = self.get_current_observation_easy_mode()
        x_diff = self.current_x_diff
        if obs < 0.1:
            desired_fw = True
        else:
            desired_fw = False
        fw_equals = (desired_fw == forward_from_agent)

        if x_diff is None and fw_equals is True:
            return yaw_from_agent*0.008
        if x_diff is None and fw_equals is False:
            return -0.5

        if fw_equals is True:
            fw_reward = 0.5
        else:
            fw_reward = -0.5
        x_diff_reward = 0.5 - obs
        reward = x_diff_reward + fw_reward + 0.5
        return reward

    def test(self, szam):
        for i in range(1000):
            cv2.imshow("normal", self.state.get_current_frame())
            self.get_target_position_move(True)

    def hsv_setter(self):
        self.start_events()
        self.hsv_trackbar()
        self._running = True
        def hsv_loop():
            while self._running:
                self.get_target_position_hsv(True, True)
                time.sleep(0.1)
        t = threading.Thread(target=hsv_loop, daemon=True)
        t.start()
        cv2.namedWindow("hsv", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("hsv", self.image_width * 2, self.image_height * 2)
        cv2.namedWindow("normal", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("normal", self.image_width * 2, self.image_height * 2)
        stopped = False
        while True:
            key = cv2.waitKey(1)
            if key == ord('a'):
                self.drive(0, 20)
                stopped = False
            elif key == ord('d'):
                self.drive(0, -20)
                stopped = False
            elif key == ord('w'):
                self.drive(10, 0)
                stopped = False
            elif key == ord('s'):
                self.drive(-10, 0)
                stopped = False
            elif stopped is False:
                self.misty.stop()
                stopped = True

            if self.last_hsv_frame is not None:
                cv2.imshow("hsv", self.last_hsv_frame)
            cv2.imshow("normal", self.state.get_current_frame())
            if key == 27:
                self._running = False
                t.join()
                break
        self.misty.stop()
        self.stop_events()

    def object_setter(self):
        self.start_events()
        cv2.namedWindow("normal", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("normal", self.image_width * 2, self.image_height * 2)
        cv2.namedWindow("yolo")
        stopped = False
        while True:
            key = cv2.waitKey(1)
            if key == ord('a'):
                self.drive(0, 20)
                stopped = False
            elif key == ord('d'):
                self.drive(0, -20)
                stopped = False
            elif key == ord('w'):
                self.drive(10, 0)
                stopped = False
            elif key == ord('s'):
                self.drive(-10, 0)
                stopped = False
            elif stopped is False:
                self.misty.stop()
                stopped = True

            frame = self.state.get_current_frame()
            cv2.imshow("normal", frame)
            rectangle = self.yolo_misty.get_something_position(frame, self.target_object_id, get_img=True)
            if rectangle is not None:
                cv2.imshow("yolo", rectangle.img)
                print(rectangle.center().to_string())

            if key == 27:
                break
        self.misty.stop()
        self.stop_events()

    def get_target_position_yolo(self):
        rectangle = self.yolo_misty.get_something_position(self.state.get_current_frame(), self.target_object_id, get_img=False)
        if rectangle is not None:
            center = rectangle.center()
            position = (((self.image_width - center.x) / self.image_width) - 0.5) * 2
            return position
        return None

    def wasd(self):
        self.start_events()
        cv2.namedWindow("wasd", cv2.WINDOW_NORMAL)
        stopped = False
        while True:
            key = cv2.waitKey(1)
            if key == ord('a'):
                self.drive(0, 20)
                stopped = False
            elif key == ord('d'):
                self.drive(0, -20)
                stopped = False
            elif key == ord('w'):
                self.drive(20, 0)
                stopped = False
            elif key == ord('s'):
                self.drive(-20, 0)
                stopped = False
            elif stopped is False:
                self.misty.stop()
                stopped = True
            cv2.imshow("wasd", self.state.get_current_frame())
            if key == 27:
                cv2.destroyWindow("wasd")
                break


if __name__ == "__main__":
    tivadar = Tivadar()
    tivadar.start_events()
    tivadar.test(1)
    tivadar.stop_events()

    # while True:
    #     time.sleep(1.1)
    #     pos = tivadar.get_ball_position()
    #     if pos is not None:
    #         turn = tivadar.pid(0,pos)
    #         print("turn1")
    #         tivadar.drive(0,-turn,2)
    #         print("turn2")
    #         if -5 < turn < 5:
    #             tivadar.drive(10,0, 2)
    #             print("fw")
    #     if pos is None:
    #         tivadar.drive(0, -40, 2)
    #
    #
    #
    #
    #     if cv2.waitKey(1) == 27:
    #         break

    # while True:
    #     # tivadar.drive_yaw(10,1)
    #     # tivadar.get_ball_position()
    #     # tivadar.interrupt_while_robot_is_moving(1)
    #     # tivadar.drive_to_the_ball()
    #     # frame = tivadar.state.get_current_frame()
    #     # diff = tivadar.state.get_current_move()
    #     # if frame is None or diff is None:
    #     #     print("no frame")
    #     #     continue
    #     # cv2.imshow("Misty camera", frame)
    #     # cv2.imshow("Diff", diff)
    #     # if cv2.waitKey(1) == 27:
    #     #      break
    #     time.sleep(1)
    #     obser = tivadar.get_current_observation()
    #     cv2.imshow("observation", obser)
    #     if cv2.waitKey(1) == 27:
    #         break












# tivadar.turn_right(20, 10)
# time.sleep(0.1)
# for i in range(8):
#     print(i)
#     tivadar.picture("pikcsör",i)
#     # time.sleep(0.01)

#tivadar.misty.stop()

# tivadar.drive(-10,0,2)





