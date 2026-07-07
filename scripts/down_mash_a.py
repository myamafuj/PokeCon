from pokecon.command import PythonCommand
from pokecon.pad import Button, Direction


# 下入力しながらA連打（1秒間隔）
class DownMashA(PythonCommand):
    NAME = "下+A連打"

    def __init__(self):
        super().__init__()

    def do(self):
        self.hold(Direction.DOWN)
        while True:
            self.press(Button.A, wait=0.25)
