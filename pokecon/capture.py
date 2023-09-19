import datetime
import time

import cv2
from PySide2.QtCore import (
    Qt,
    QThread,
    Signal
)
from PySide2.QtGui import QImage


class Capture:
    def __init__(self, w, h, fps, path_dir):
        super().__init__()
        self.w = w
        self.h = h
        self.fps = fps
        self.src = cv2.VideoCapture(0)
        self.ref = None
        self.frame = None
        self.path_dir = path_dir

    def read(self):
        self.ref, self.frame = self.src.read()
        return self.ref, self.frame

    def isOpened(self):
        return self.src.isOpened()

    def release(self):
        return self.src.release()

    def screenshot(self):
        now = datetime.datetime.now()
        path = self.path_dir.joinpath(f'screenshot_{now:%Y%m%d%H%M%S}.png')
        path.parent.mkdir(exist_ok=True)
        cv2.imwrite(str(path), self.frame)


class CaptureThread(QThread):
    change_pixmap_signal = Signal(QImage)

    def __init__(self, cap):
        super().__init__()
        self.status = True
        self.cap = cap

    def run(self):
        while self.status:
            start_time = time.perf_counter_ns()
            ret, frame = self.cap.read()
            if ret:
                h, w, ch = frame.shape
                img = QImage(frame, w, h, QImage.Format.Format_BGR888)
                if self.cap.w != w or self.cap.h != h:
                    img = img.scaled(self.cap.w, self.cap.h, Qt.KeepAspectRatio)
                self.change_pixmap_signal.emit(img)
            end_time = time.perf_counter_ns()
            a0 = int(1000/self.cap.fps - (end_time - start_time)/1000000)
            if a0 > 0:
                self.msleep(a0)
        self.cap.release()

    def stop(self):
        self.status = False
        self.wait()
