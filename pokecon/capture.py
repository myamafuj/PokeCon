import datetime

import cv2

from pokecon.logger import get_logger


logger = get_logger(__name__)


class Capture:
    def __init__(self, camera_id, w, h, fps, path_dir):
        super().__init__()
        self.src = cv2.VideoCapture(camera_id)
        self.w = w
        self.h = h
        self.fps = fps
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
        filename = f'screenshot_{datetime.datetime.now():%Y%m%d%H%M%S}.png'
        path = self.path_dir.joinpath(filename)
        path.parent.mkdir(exist_ok=True)
        cv2.imwrite(str(path), self.frame)
        logger.info(f'successfully saved image: {filename}')
