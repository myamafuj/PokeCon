from abc import ABCMeta
from pathlib import Path
from time import sleep
import threading

import cv2

from pokecon.pad import Input


TEMPLATE_PATH = Path(__file__).parent / '../templates/'


# the class For notifying stop signal is sent from Main window
class StopThread(Exception):
    pass


class Command:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.isRunning = False

    @classmethod
    def start(cls, ser, post_process=None):
        pass

    @classmethod
    def end(cls, ser):
        pass


# Python command
class PythonCommand(Command):
    def __init__(self):
        super().__init__()
        self.input = None
        self.thread = None
        self.alive = True
        self.post_process = None

    @classmethod
    def do(cls):
        pass

    def do_safe(self, ser):
        if self.input is None:
            self.input = Input(ser)

        try:
            if self.alive:
                self.do()
                self.finish()
        except StopThread:
            print('-- finished successfully. --')
        except:
            if self.input is None:
                self.input = Input(ser)
            print('interruppt')
            import traceback
            traceback.print_exc()
            self.input.end()
            self.alive = False

    def start(self, ser, post_process=None):
        self.alive = True
        self.post_process = post_process
        if not self.thread:
            self.thread = threading.Thread(target=self.do_safe, args=(ser,))
            self.thread.start()

    def end(self, ser):
        self.send_stop_request()

    def send_stop_request(self):
        if self.check_if_alive():  # try if we can stop now
            self.alive = False
            print('-- sent a stop request. --')

    # NOTE: Use this function if you want to get out from a command loop by yourself
    def finish(self):
        self.alive = False
        self.end(self.input.ser)

    # press button at duration times(s)
    def press(self, buttons, duration=0.1, wait=0.1):
        self.input.press(buttons)
        self.wait(duration)
        self.input.press_end(buttons)
        self.wait(wait)
        self.check_if_alive()

    # press button at duration times(s) repeatedly
    def press_rep(self, buttons, repeat, duration=0.1, interval=0.1, wait=0.1):
        for i in range(0, repeat):
            self.press(buttons, duration, 0 if i == repeat - 1 else interval)
        self.wait(wait)

    # add hold buttons
    def hold(self, buttons, wait=0.1):
        self.input.hold(buttons)
        self.wait(wait)

    # release holding buttons
    def hold_end(self, buttons):
        self.input.hold_end(buttons)
        self.check_if_alive()

    # do nothing at wait time(s)
    def wait(self, wait):
        sleep(wait)
        self.check_if_alive()

    def check_if_alive(self):
        if not self.alive:
            self.input.end()
            self.input = None
            self.thread = None

            if not self.post_process is None:
                self.post_process()
                self.post_process = None

            # raise exception for exit working thread
            raise StopThread('exit successfully')
        else:
            return True


class ImageProcPythonCommand(PythonCommand):
    def __init__(self, cap):
        super().__init__()
        self.cap = cap

    # Judge if current screenshot contains a template using template matching
    # It's recommended that you use gray_scale option unless the template color wouldn't be cared for performace
    # 現在のスクリーンショットと指定した画像のテンプレートマッチングを行います
    # 色の違いを考慮しないのであればパフォーマンスの点からuse_grayをTrueにしてグレースケール画像を使うことを推奨します
    def is_contain_template(self,
                            template_path,
                            threshold=0.7,
                            use_gray=True,
                            show_value=False,
                            area=None,
                            tmp_area=None):

        if tmp_area is None:
            tmp_area = []
        if area is None:
            area = []

        # Read a current image
        _, src = self.cap.read()
        src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY) if use_gray else src
        src = src[area[2]:area[3], area[0]:area[1]] if area else src

        # Read a template image
        path = TEMPLATE_PATH / template_path
        templ = cv2.imread(str(path),
                              cv2.IMREAD_GRAYSCALE if use_gray else cv2.IMREAD_COLOR)
        templ = templ[tmp_area[2]:tmp_area[3], tmp_area[0]:tmp_area[1]] if tmp_area else templ
        w, h = templ.shape[1], templ.shape[0]

        method = cv2.TM_CCOEFF_NORMED
        res = cv2.matchTemplate(src, templ, method)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if show_value:
            print(template_path + ' ZNCC value: ' + str(max_val))

        if max_val > threshold:
            if use_gray:
                src = cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)

            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            cv2.rectangle(src, top_left, bottom_right, (255, 0, 255), 2)
            return True
        else:
            return False

    # Get interframe difference binarized image
    # フレーム間差分により2値化された画像を取得
    def get_interframe_diff(self, frame1, frame2, frame3, threshold):
        diff1 = cv2.absdiff(frame1, frame2)
        diff2 = cv2.absdiff(frame2, frame3)

        diff = cv2.bitwise_and(diff1, diff2)

        # binarize
        img_th = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)[1]

        # remove noise
        mask = cv2.medianBlur(img_th, 3)
        return mask

    # Take a screenshot (saved in /SerialController/Captures/)
    # スクリーンショットを取得
    def screenshot(self):
        self.cap.screenshot()