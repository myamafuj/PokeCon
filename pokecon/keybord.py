from pynput.keyboard import Key, Listener

from pokecon.logger import get_logger
from pokecon.pad import Input, Button, Hat, Direction


logger = get_logger(__name__)


# This handles keyboard interactions
class Keyboard:
    def __init__(self):
        self.listener = Listener(on_press=self.on_press,
                                 on_release=self.on_release)

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()

    def on_press(self, key):
        try:
            logger.info(f'alphanumeric key {key.char} pressed')
        except AttributeError:
            logger.info(f'special key {key} pressed')

    def on_release(self, key):
        logger.info(f'{key} released')


# This regards a keyboard inputs as Switch controller
class KeyboardController(Keyboard):
    def __init__(self, input_: Input):
        super().__init__()
        self.input = input_
        self.holding = []
        self.holding_direction = []

        self.key_map = {
            'l': Button.A,
            'k': Button.B,
            'j': Button.X,
            'i': Button.Y,
            'q': Button.L,
            'e': Button.R,
            'u': Button.ZL,
            'o': Button.ZR,
            Key.shift_l: Button.L_CLICK,
            Key.shift_r: Button.R_CLICK,
            Key.ctrl_l: Button.MINUS,
            Key.ctrl_r: Button.PLUS,
            'h': Button.HOME,
            'f': Button.CAPTURE,
            'w': Direction.UP,
            'd': Direction.RIGHT,
            's': Direction.DOWN,
            'a': Direction.LEFT,
            Key.up: Hat.TOP,
            Key.right: Hat.RIGHT,
            Key.down: Hat.BTM,
            Key.left: Hat.LEFT,
        }
        # self.inverse_key_map = {v: k for k, v in self.key_map.items()}
        self.direction_key = [k for k, v in self.key_map.items() if type(v) is Direction]

    def inverse_lookup(self, x):
        for k, v in self.key_map.items():
            if x == v:
                return k

    def on_press(self, key):
        # for debug (show row key data)
        # super().on_press(key)

        if key is None:
            logger.warning('unknown key has input')

        try:
            key_ = key.char
        # for special keys
        except AttributeError:
            key_ = key

        if key_ in self.holding or key_ in self.holding_direction:
            return

        for k in self.key_map.keys():
            if key_ == k and key_ in self.direction_key:
                self.holding_direction.append(key_)
                self.press_direction(self.holding_direction)
            elif key_ == k:
                self.input.press(self.key_map[k])
                self.holding.append(key_)

    def on_release(self, key):
        if key is None:
            logger.warning('unknown key has released')

        try:
            key_ = key.char
        # for special keys
        except AttributeError:
            key_ = key

        if key_ in self.holding_direction:
            self.holding_direction.remove(key_)
            self.input.press_end(self.key_map[key_])
            self.press_direction(self.holding_direction)
        elif key_ in self.holding:
            self.holding.remove(key_)
            self.input.press_end(self.key_map[key_])

    def press_direction(self, direction):
        if len(direction) == 0:
            return
        elif len(direction) == 1:
            self.input.press(self.key_map[direction[0]])
        elif len(direction) > 1:
            valid_direction = direction[-2:]  # set only last 2 directions

            if self.inverse_lookup(Direction.UP) in valid_direction:
                if self.inverse_lookup(Direction.RIGHT) in valid_direction:
                    self.input.press(Direction.UP_RIGHT)
                elif self.inverse_lookup(Direction.LEFT) in valid_direction:
                    self.input.press(Direction.UP_LEFT)
            elif self.inverse_lookup(Direction.DOWN) in valid_direction:
                if self.inverse_lookup(Direction.RIGHT) in valid_direction:
                    self.input.press(Direction.DOWN_LEFT)
                elif self.inverse_lookup(Direction.LEFT) in valid_direction:
                    self.input.press(Direction.DOWN_RIGHT)
