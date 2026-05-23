import cv2
from ultralytics import YOLO

class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def to_string(self):
        return f"x={self.x}, y={self.y}"

class Rectangle:
    def __init__(self, x1, y1, x2, y2, img = None):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.img = img

    def center(self):
        c1 = (self.x1 + self.x2) / 2
        c2 = (self.y1 + self.y2) / 2
        return Coordinate(c1, c2)

class YoloMisty:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")

    def get_result(self, img):
        return self.model(img, show=False)[0].plot()

    def print_names(self):
        print(self.model.names)

    def get_something_position(self, img, id_of_something = 39, get_img = False):
        results = self.model(img, classes=[id_of_something], show=False, verbose=False)
        r = results[0]
        best_box = None
        best_conf = 0
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf > best_conf:
                best_conf = conf
                best_box = box
        if best_box is not None:
            x1, y1, x2, y2 = best_box.xyxy[0]
            if get_img:
                return Rectangle(x1, y1, x2, y2, r.plot())
            return Rectangle(x1, y1, x2, y2)
        return None


