from pokecon.command import PythonCommand
from pokecon.pad import Button


# ZL押しっぱなしA連打
class ZLMashA(PythonCommand):
    NAME = "ZL+A連打"

    def __init__(self):
        super().__init__()

    def do(self):
        self.hold(Button.ZL)
        while True:
            self.press(Button.A, wait=0.25)
