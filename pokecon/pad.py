import math
from collections import OrderedDict
from enum import IntFlag, IntEnum, Enum, auto

from pokecon.logger import get_logger
from pokecon.ports import SerialSender


# direction value definitions
MIN = 0
CENTER = 128
MAX = 255


logger = get_logger(__name__)


class Button(IntFlag):
    Y = auto()
    B = auto()
    A = auto()
    X = auto()
    L = auto()
    R = auto()
    ZL = auto()
    ZR = auto()
    MINUS = auto()
    PLUS = auto()
    L_CLICK = auto()
    R_CLICK = auto()
    HOME = auto()
    CAPTURE = auto()


class Hat(IntEnum):
    TOP = 0
    TOP_RIGHT = 1
    RIGHT = 2
    BTM_RIGHT = 3
    BTM = 4
    BTM_LEFT = 5
    LEFT = 6
    TOP_LEFT = 7
    CENTER = 8


class Stick(Enum):
    LEFT = auto()
    RIGHT = auto()


class Tilt(Enum):
    UP = auto()
    RIGHT = auto()
    DOWN = auto()
    LEFT = auto()
    R_UP = auto()
    R_RIGHT = auto()
    R_DOWN = auto()
    R_LEFT = auto()


class Direction(Enum):
    # Left stick for ease of use
    UP = (Stick.LEFT, 90)
    RIGHT = (Stick.LEFT, 0)
    DOWN = (Stick.LEFT, -90)
    LEFT = (Stick.LEFT, -180)
    UP_RIGHT = (Stick.LEFT, 45)
    DOWN_RIGHT = (Stick.LEFT, -45)
    DOWN_LEFT = (Stick.LEFT, -135)
    UP_LEFT = (Stick.LEFT, 135)
    # Right stick for ease of use
    R_UP = (Stick.RIGHT, 90)
    R_RIGHT = (Stick.RIGHT, 0)
    R_DOWN = (Stick.RIGHT, -90)
    R_LEFT = (Stick.RIGHT, -180)
    R_UP_RIGHT = (Stick.RIGHT, 45)
    R_DOWN_RIGHT = (Stick.RIGHT, -45)
    R_DOWN_LEFT = (Stick.RIGHT, -135)
    R_UP_LEFT = (Stick.RIGHT, 135)

    def __init__(self, stick, degree):
        self.stick = stick
        self.degree = degree
        degree = math.radians(degree)
        # We set stick X and Y from 0 to 255, so they are calculated as below.
        # X = 127.5*cos(theta) + 127.5
        # Y = 127.5*sin(theta) + 127.5
        self.x = math.ceil(127.5 * math.cos(degree) + 127.5)
        self.y = math.floor(127.5 * math.sin(degree) + 127.5)

    def __eq__(self, other):
        if type(other) is not Direction:
            return False

        if self.stick == other.stick and self.degree == other.degree:
            return True
        else:
            return False

    @property
    def tilt(self):
        values = []
        if self.stick == Stick.LEFT:
            if self.x < CENTER:
                values.append(Tilt.LEFT)
            elif self.x > CENTER:
                values.append(Tilt.RIGHT)

            if self.y < CENTER - 1:
                values.append(Tilt.DOWN)
            elif self.y > CENTER - 1:
                values.append(Tilt.UP)

        elif self.stick == Stick.RIGHT:
            if self.x < CENTER:
                values.append(Tilt.R_LEFT)
            elif self.x > CENTER:
                values.append(Tilt.R_RIGHT)

            if self.y < CENTER - 1:
                values.append(Tilt.R_DOWN)
            elif self.y > CENTER - 1:
                values.append(Tilt.R_UP)
        return values


# serial format
class SerialFormat:
    def __init__(self):
        # This format structure needs to be the same as the one written in Joystick.c
        self.format = OrderedDict([
            ('btn', 0),  # send bit array for buttons
            ('hat', Hat.CENTER),
            ('lx', CENTER),
            ('ly', CENTER),
            ('rx', CENTER),
            ('ry', CENTER),
        ])

        self.L_stick_changed = False
        self.R_stick_changed = False

    def set_button(self, commands):
        for c in commands:
            self.format['btn'] |= c

    def unset_button(self, commands):
        for c in commands:
            self.format['btn'] &= ~c

    def reset_all_buttons(self):
        self.format['btn'] = 0

    def set_hat(self, commands):
        if not commands:
            self.format['hat'] = Hat.CENTER
        else:
            self.format['hat'] = commands[0]  # takes only first element

    def unset_hat(self):
        self.format['hat'] = Hat.CENTER

    def set_any_direction(self, commands):
        for c in commands:
            if c.stick == Stick.LEFT:
                if self.format['lx'] != c.x or self.format['ly'] != 255 - c.y:
                    self.L_stick_changed = True

                self.format['lx'] = c.x
                self.format['ly'] = 255 - c.y  # NOTE: y axis directs under
            elif c.stick == Stick.RIGHT:
                if self.format['rx'] != c.x or self.format['ry'] != 255 - c.y:
                    self.R_stick_changed = True

                self.format['rx'] = c.x
                self.format['ry'] = 255 - c.y

    def unset_direction(self, commands):
        if Tilt.UP in commands or Tilt.DOWN in commands:
            self.format['ly'] = CENTER
            self.format['lx'] = self.fix_other_axis(self.format['lx'])
            self.L_stick_changed = True
        if Tilt.RIGHT in commands or Tilt.LEFT in commands:
            self.format['lx'] = CENTER
            self.format['ly'] = self.fix_other_axis(self.format['ly'])
            self.L_stick_changed = True
        if Tilt.R_UP in commands or Tilt.R_DOWN in commands:
            self.format['ry'] = CENTER
            self.format['rx'] = self.fix_other_axis(self.format['rx'])
            self.R_stick_changed = True
        if Tilt.R_RIGHT in commands or Tilt.R_LEFT in commands:
            self.format['rx'] = CENTER
            self.format['ry'] = self.fix_other_axis(self.format['ry'])
            self.R_stick_changed = True

    # Use this to fix an `either` tilt to max when the other axis sets to 0
    @staticmethod
    def fix_other_axis(fix_target):
        if fix_target == CENTER:
            return CENTER
        else:
            return 0 if fix_target < CENTER else 255

    def reset_all_directions(self):
        self.format['lx'] = CENTER
        self.format['ly'] = CENTER
        self.format['rx'] = CENTER
        self.format['ry'] = CENTER
        self.L_stick_changed = True
        self.R_stick_changed = True

    @property
    def str(self):
        # set bits array with stick flags
        send_btn = int(self.format['btn']) << 2
        str_l = ''
        if self.L_stick_changed:
            send_btn |= 0x2
            str_l = format(self.format['lx'], 'x') + ' ' + format(self.format['ly'], 'x')
        str_r = ''
        if self.R_stick_changed:
            send_btn |= 0x1
            str_r = format(self.format['rx'], 'x') + ' ' + format(self.format['ry'], 'x')
        str_btn = format(send_btn, '#06x')
        str_hat = str(int(self.format['hat']))

        str_format = ' '.join([str_btn, str_hat, str_l, str_r])

        self.L_stick_changed = False
        self.R_stick_changed = False

        return str_format  # the last space is not needed


# handles serial input to Joystick.c
class Input:
    def __init__(self, ser: SerialSender):
        self.ser = ser
        self.format = SerialFormat()
        self.holding = []

    def press(self, commands):
        if not isinstance(commands, list):
            commands = [commands]

        for c in self.holding:
            if c not in commands:
                commands.append(c)

        # print to log
        logger.debug(commands)

        self.format.set_button([c for c in commands if type(c) is Button])
        self.format.set_hat([c for c in commands if type(c) is Hat])
        self.format.set_any_direction([c for c in commands if type(c) is Direction])

        self.ser.write(self.format.str)

    def press_end(self, commands):
        if not isinstance(commands, list):
            commands = [commands]

        # get tilting direction from angles
        tilts = []
        for d in [btn for btn in commands if type(btn) is Direction]:
            tilts.extend(d.tilt)

        self.format.unset_button([c for c in commands if type(c) is Button])
        self.format.unset_hat()
        self.format.unset_direction(tilts)

        self.ser.write(self.format.str)

    def hold(self, commands):
        if not isinstance(commands, list):
            commands = [commands]

        for c in commands:
            if c in self.holding:
                logger.warning(f'{c.name} is already in holding state')
                return

            self.holding.append(c)

        self.press(commands)

    def hold_end(self, commands):
        if not isinstance(commands, list):
            commands = [commands]

        for c in commands:
            self.holding.remove(c)

        self.press_end(commands)

    def end(self):
        self.ser.write('end')
