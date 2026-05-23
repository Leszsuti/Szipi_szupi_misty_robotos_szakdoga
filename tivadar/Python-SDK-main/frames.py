import time
import os
import cv2


class FrameManager:
    def __init__(self, path = "D:\\SZTE\\2026\\szakdoga\\tivadar\\Python-SDK-main\\frames"):
        self.path = path
        self.counter = 0

    def save_frame(self, frame, frame_name, data_str):
        with open(self.path + "\\data_strings\\" + frame_name + ".txt", "w") as f:
            f.write(data_str)
        if frame is None:
            print("ez most bizony nem lett elmentve (nincs kep)")
            return
        path = self.path + "\\pictures\\" + frame_name + ".png"
        cv2.imwrite(path, frame)


    def save_numbered_frames(self, frame, frame_name, data_str):
        self.save_frame(frame, frame_name + str(self.counter), data_str)
        self.counter += 1

    def set_counter(self, counter):
        self.counter = counter

    def read_and_show_frame(self, frame_name, window_name):
        frame_path = self.path + "\\pictures\\" + frame_name + ".png"
        text_path = self.path + "\\data_strings\\" + frame_name + ".txt"

        try:
            frame = cv2.imread(frame_path)
            cv2.imshow(window_name, frame)
        except:
            print("ezt bizony nem nyitotta meg", frame_path)
        try:
            with open(text_path, "r") as f:
                data_str = f.read()
                print(text_path)
                print(data_str)
        except:
            print("ezt bizony nem nyitotta meg", text_path)
        cv2.waitKey(1)
        print ()

    def read_and_show_in_order(self, frame_name, key):
        self.read_and_show_frame(frame_name + str(self.counter - 1), "before")
        self.read_and_show_frame(frame_name + str(self.counter),"after")
        #s
        if key == 115:
            self.counter += 1
            return
        #w
        if key == 119:
            self.counter -= 1
            return
        return

    def read_txt_data(self):
        txt_list = os.listdir(self.path + "\\data_strings")
        out=[]
        for i in txt_list:
            with open(f"{self.path}\\data_strings\\{i}", "r") as f:
                data_str = f.read()
                out.append(data_str)
        return out



if __name__ == "__main__":
    frame_manager = FrameManager()
    key = 115
    frame_manager.read_and_show_in_order( "normal", key)
    while True:
        key = cv2.waitKey(1)
        if key == 115 or key == 119:
            frame_manager.read_and_show_in_order( "normal", key)