from pokecon.pad import Button, Direction, Hat, Input, SerialFormat, Stick, Tilt


class DummySender:
    def __init__(self):
        self.sent = []

    def write(self, row):
        self.sent.append(row)


class TestDirection:
    def test_stick_xy(self):
        assert (Direction.UP.x, Direction.UP.y) == (128, 255)
        assert (Direction.DOWN.x, Direction.DOWN.y) == (128, 0)
        assert (Direction.RIGHT.x, Direction.RIGHT.y) == (255, 127)
        assert (Direction.LEFT.x, Direction.LEFT.y) == (0, 127)

    def test_tilt(self):
        assert Direction.UP.tilt == [Tilt.UP]
        assert Direction.RIGHT.tilt == [Tilt.RIGHT]
        assert set(Direction.DOWN_LEFT.tilt) == {Tilt.DOWN, Tilt.LEFT}
        assert Direction.R_UP.tilt == [Tilt.R_UP]

    def test_equality(self):
        assert Direction.UP == Direction.UP
        assert Direction.UP != Direction.R_UP
        assert Direction.UP != 'UP'


class TestSerialFormat:
    def test_initial_state(self):
        sf = SerialFormat()
        assert sf.str.split() == ['0x0000', '8']

    def test_button(self):
        sf = SerialFormat()
        sf.set_button([Button.A])
        # Button.A(=4)を2ビット左シフトした値がボタンビット列
        assert sf.str.split() == ['0x0010', '8']
        sf.unset_button([Button.A])
        assert sf.str.split() == ['0x0000', '8']

    def test_hat(self):
        sf = SerialFormat()
        sf.set_hat([Hat.TOP])
        assert sf.str.split() == ['0x0000', '0']
        sf.unset_hat()
        assert sf.str.split() == ['0x0000', '8']

    def test_left_stick(self):
        sf = SerialFormat()
        sf.set_any_direction([Direction.UP])
        # 左スティック変化フラグ(0x2)が立ち、y軸は反転して送信される
        assert sf.str.split() == ['0x0002', '8', '80', '0']
        # 送信後はフラグが落ち、スティック値は省略される
        assert sf.str.split() == ['0x0000', '8']

    def test_right_stick(self):
        sf = SerialFormat()
        sf.set_any_direction([Direction.R_RIGHT])
        assert sf.str.split() == ['0x0001', '8', 'ff', '80']

    def test_unset_direction(self):
        sf = SerialFormat()
        sf.set_any_direction([Direction.UP])
        _ = sf.str
        sf.unset_direction([Tilt.UP])
        assert sf.str.split() == ['0x0002', '8', '80', '80']

    def test_reset_all(self):
        sf = SerialFormat()
        sf.set_button([Button.A, Button.B])
        sf.set_any_direction([Direction.UP, Direction.R_DOWN])
        _ = sf.str
        sf.reset_all_buttons()
        sf.reset_all_directions()
        assert sf.str.split() == ['0x0003', '8', '80', '80', '80', '80']


class TestInput:
    def test_press_and_release(self):
        ser = DummySender()
        input_ = Input(ser)
        input_.press(Button.A)
        input_.press_end(Button.A)
        assert ser.sent[0].split() == ['0x0010', '8']
        assert ser.sent[1].split() == ['0x0000', '8']

    def test_hold_is_kept_on_press(self):
        ser = DummySender()
        input_ = Input(ser)
        input_.hold(Button.ZL)
        input_.press(Button.A)
        # ZL(=64)とA(=4)の合成値が送信される
        assert ser.sent[1].split() == ['0x0110', '8']
        input_.hold_end(Button.ZL)
        assert input_.holding == []

    def test_hold_direction(self):
        ser = DummySender()
        input_ = Input(ser)
        input_.hold(Direction.DOWN)
        input_.press(Button.A)
        # 下入力(ly=ff)を維持したままAが送信される
        assert ser.sent[1].split() == ['0x0010', '8']
        assert input_.holding == [Direction.DOWN]

    def test_end(self):
        ser = DummySender()
        input_ = Input(ser)
        input_.end()
        assert ser.sent == ['end']
