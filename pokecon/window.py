import logging

import pyaudio
from PySide2.QtCore import (
    QEvent,
    QObject,
    Qt,
    QSize,
    QTimer,
    QUrl,
    Signal,
    Slot
)
from PySide2.QtGui import (
    QIcon,
    QImage,
    QPixmap,
    QDesktopServices
)
from PySide2.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)

from pokecon.capture import Capture
from pokecon.command import ImageProcPythonCommand
from pokecon.config import Config
from pokecon.keybord import KeyboardController
from pokecon.monitor import InfoWindow, SignalHandler
from pokecon.pad import Input, Button
from pokecon.ports import SerialSender
from pokecon.utils import get_scripts, get_available_camera_id, get_available_ports


VER = '2.0.0'


class MouseController(QObject):
    left_pressed = Signal()
    left_released = Signal()
    right_pressed = Signal()
    right_released = Signal()
    middle_pressed = Signal()
    middle_released = Signal()

    def press_event(self, ev):
        if ev.button() == Qt.LeftButton:
            self.left_pressed.emit()
        elif ev.button() == Qt.RightButton:
            self.right_pressed.emit()
        elif ev.button() == Qt.MiddleButton:
            self.middle_pressed.emit()

    def release_event(self, ev):
        if ev.button() == Qt.LeftButton:
            self.left_released.emit()
        elif ev.button() == Qt.RightButton:
            self.right_released.emit()
        elif ev.button() == Qt.MiddleButton:
            self.middle_released.emit()


class QVideoLabel(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mouse = MouseController()

    def mousePressEvent(self, ev):
        self.mouse.press_event(ev)
        return QLabel.mousePressEvent(self, ev)

    def mouseReleaseEvent(self, ev):
        self.mouse.release_event(ev)
        return QLabel.mouseReleaseEvent(self, ev)


class Window(QMainWindow):
    def __init__(self, root, parent=None):
        super().__init__(parent)
        # unique settings
        # path
        self.root = root
        # conf
        self.config = Config()
        self.config.read()
        # status bar
        self.statusBar().setContentsMargins(16, 0, 0, 0)
        # history
        self.button_history = QPushButton()
        self.button_history.setIcon(QIcon(str(self.root.joinpath('assets/history.png'))))
        self.button_history.setIconSize(QSize(20, 20))
        self.button_history.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.statusBar().addPermanentWidget(self.button_history)
        # volume
        self.button_volume = QPushButton()
        if self.config.audio.volume:
            self.button_volume.setIcon(QIcon(str(self.root.joinpath('assets/volume_on.png'))))
        else:
            self.button_volume.setIcon(QIcon(str(self.root.joinpath('assets/volume_off.png'))))
        self.button_volume.setIconSize(QSize(20, 20))
        self.button_volume.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.statusBar().addPermanentWidget(self.button_volume)
        # settings
        self.button_settings = QPushButton()
        self.button_settings.setIcon(QIcon(str(self.root.joinpath('assets/settings.png'))))
        self.button_settings.setIconSize(QSize(20, 20))
        self.button_settings.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.statusBar().addPermanentWidget(self.button_settings)
        # log
        self.logger = logging.getLogger()
        formatter = logging.Formatter(' %(asctime)s [%(levelname)s] %(name)s: %(message)s')
        self.signal_handler = SignalHandler()
        self.signal_handler.setFormatter(formatter)
        self.signal_handler.setLevel(logging.INFO)
        self.signal_handler.emitter.message.connect(self.write)
        self.logger.addHandler(self.signal_handler)
        self.info_window = InfoWindow(self)
        # capture
        self.cap_devices = get_available_camera_id()
        if self.config.capture.camera_id not in self.cap_devices.keys():
            self.config.capture.camera_id = 0
        self.cap = Capture(self.config.capture.camera_id,
                           self.config.capture.width,
                           self.config.capture.height,
                           self.config.capture.fps,
                           self.root.joinpath('screenshot'))
        # serial
        self.ports = get_available_ports()
        if self.config.serial.port not in self.ports:
            self.config.serial.port = self.ports[0]
        self.ser = SerialSender()
        self.ser.open(self.config.serial.port)
        # keyboard
        self.input = Input(self.ser)
        self.keyboard = None
        # scripts
        self.scripts = get_scripts()
        self.current_script = None
        # settings
        self.screen_rect = QApplication.primaryScreen().geometry()
        if self.screen_rect.width() <= 1920:
            self.display_size_list = [(1280, 720), (960, 540)]
        else:
            self.display_size_list = [(1920, 1080), (1280, 720), (960, 540)]
        self.display_size = (self.config.app.width, self.config.app.height)
        self.settings_window = SettingsWindow(self)

        # title
        self.setWindowTitle(f'PokeCon v{VER}')
        self.setWindowIcon(QIcon(str(self.root.joinpath('assets/icon.png'))))
        try:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(f'myamafuj.pokecon.{VER}')
        except ImportError:
            pass

        # label for the display camera
        self.label_video = QVideoLabel()
        self.label_video.setMinimumSize(self.config.app.width, self.config.app.height)
        self.label_video.setMaximumSize(self.screen_rect.size())
        self.label_video.resize(self.config.app.width, self.config.app.height)

        # image group
        self.group_image = QGroupBox('screenshot')
        self.group_image.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        image_layout = QHBoxLayout()
        self.buttons_image = {}
        for key in ['save', 'open']:
            self.buttons_image[key] = QPushButton(key)
            self.buttons_image[key].setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            image_layout.addWidget(self.buttons_image[key], 1)
        self.group_image.setLayout(image_layout)

        # command group
        self.group_command = QGroupBox('command')
        self.group_command.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        command_layout = QHBoxLayout()
        self.combobox_command = QComboBox()
        for key in self.scripts.keys():
            self.combobox_command.addItem(key)
        command_layout.addWidget(self.combobox_command, 2)
        self.buttons_command = {}
        for key in ['start/stop', 'reload']:
            self.buttons_command[key] = QPushButton(key)
            self.buttons_command[key].setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            command_layout.addWidget(self.buttons_command[key], 1)
        self.buttons_command['start/stop'].setText('start')
        self.group_command.setLayout(command_layout)

        # top layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.label_video, alignment=Qt.AlignCenter)

        # bottom layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.group_image, 1)
        bottom_layout.addWidget(self.group_command, 2)

        # main layout
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)

        # central widget
        self.widget = QWidget(self)
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)

        # connections
        self.buttons_image['save'].clicked.connect(self.cap.screenshot)
        self.buttons_image['open'].clicked.connect(self.open_dir)
        self.combobox_command.currentTextChanged.connect(self.set_current_script)
        self.buttons_command['reload'].clicked.connect(self.reload_scrips)
        self.buttons_command['start/stop'].clicked.connect(self.command)
        self.button_volume.clicked.connect(self.switch_volume)
        self.button_history.clicked.connect(self.show_log_window)
        self.button_settings.clicked.connect(self.settings_window.show)

        self.label_video.mouse.left_pressed.connect(self.left_mouse_press)
        self.label_video.mouse.right_pressed.connect(self.right_mouse_press)
        self.label_video.mouse.middle_pressed.connect(self.middle_mouse_press)
        self.label_video.mouse.left_released.connect(self.left_mouse_release)
        self.label_video.mouse.right_released.connect(self.right_mouse_release)
        self.label_video.mouse.middle_released.connect(self.middle_mouse_release)

        # video
        self.video_timer = QTimer()
        millisecond = int(1000.0 / self.config.app.fps)
        self.video_timer.setTimerType(Qt.CoarseTimer)  # Qt.PreciseTimerとの負荷比較したい
        self.video_timer.timeout.connect(self.next_frame)
        self.video_timer.start(millisecond)

        # audio
        self.p = pyaudio.PyAudio()
        if self.config.audio.volume:
            self.start_audio()
        else:
            self.stream = None

        # flag
        self.is_playing = False
        self.is_loaded = False
        self.other_width = self.size().width() - self.label_video.size().width()
        self.other_height = self.size().height() - self.label_video.size().height()

    def next_frame(self):
        ret, frame = self.cap.read()
        if ret:
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
            pix = QPixmap.fromImage(img)
            pix = pix.scaled(self.label_video.width(), self.label_video.height(),
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)  # 負荷
            self.label_video.setPixmap(pix)

    def left_mouse_press(self):
        if not self.is_playing:
            self.input.press(Button.A)

    def right_mouse_press(self):
        if not self.is_playing:
            self.input.press(Button.B)

    def middle_mouse_press(self):
        if not self.is_playing:
            self.input.press(Button.X)

    def left_mouse_release(self):
        if not self.is_playing:
            self.input.press_end(Button.A)

    def right_mouse_release(self):
        if not self.is_playing:
            self.input.press_end(Button.B)

    def middle_mouse_release(self):
        if not self.is_playing:
            self.input.press_end(Button.X)

    @Slot(str)
    def write(self, msg):
        self.statusBar().showMessage(msg)

    def open_dir(self):
        QDesktopServices.openUrl(QUrl(f'file:///{self.root.joinpath("screenshot")}'))

    def set_current_script(self, key):
        if key:
            cls_ = self.scripts[key]
            if issubclass(cls_, ImageProcPythonCommand):
                self.current_script = cls_(self.cap)
            else:
                self.current_script = cls_()

    def reload_scrips(self):
        self.buttons_command['reload'].setEnabled(False)
        before = self.combobox_command.currentText()
        self.combobox_command.clear()
        self.scripts = get_scripts(old=list(self.scripts.keys()))
        for key in self.scripts.keys():
            self.combobox_command.addItem(key)
        if before not in self.scripts.keys():
            before = self.combobox_command.currentText()
        self.combobox_command.setCurrentText(before)
        self.set_current_script(before)
        self.buttons_command['reload'].setEnabled(True)

    def command(self):
        if self.buttons_command['start/stop'].text() == 'start':
            self.command_pre_process()
            self.start_command()

        elif self.buttons_command['start/stop'].text() == 'stop':
            self.stop_command()

    def start_command(self):
        self.is_playing = True
        if self.current_script is None:
            key = self.combobox_command.currentText()
            cls = self.scripts[key]
            if issubclass(cls, ImageProcPythonCommand):
                self.current_script = cls(self.cap)
            else:
                self.current_script = cls()
        self.current_script.start(self.ser, self.command_post_process)

    def command_pre_process(self):
        if self.keyboard is not None:
            self.keyboard.stop()
            self.keyboard = None
        self.is_playing = True
        self.settings_window.combobox_video.setEnabled(False)
        self.settings_window.combobox_ports.setEnabled(False)
        self.combobox_command.setEnabled(False)
        self.buttons_command['reload'].setEnabled(False)
        self.buttons_command['start/stop'].setText('stop')

    def command_post_process(self):
        self.settings_window.combobox_video.setEnabled(True)
        self.settings_window.combobox_ports.setEnabled(True)
        self.combobox_command.setEnabled(True)
        self.buttons_command['reload'].setEnabled(True)
        self.buttons_command['start/stop'].setText('start')
        self.is_playing = False
        if self.keyboard is None and (self.hasFocus() or self.isActiveWindow()):
            self.keyboard = KeyboardController(self.input)
            self.keyboard.start()
        self.current_script = None

    def stop_command(self):
        self.current_script.end()

    def start_audio(self):
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            input=True,
            output=True,
            stream_callback=lambda input_data, c, t, s: (input_data, pyaudio.paContinue)
        )
        self.stream.start_stream()

    def switch_volume(self):
        if self.config.audio.volume:
            self.stream.stop_stream()
            self.stream.close()
            self.button_volume.setIcon(QIcon(str(self.root.joinpath('assets/volume_off.png'))))
            self.config.audio.volume = False
        else:
            self.start_audio()
            self.button_volume.setIcon(QIcon(str(self.root.joinpath('assets/volume_on.png'))))
            self.config.audio.volume = True

    def move_center(self):
        self.move(self.screen_rect.width() / 2 - self.frameSize().width() / 2,
                  self.screen_rect.height() / 2 - self.frameSize().height() / 2)

    def move_aside(self):
        self.move(self.screen_rect.width() / 3 + self.frameSize().width() / 3,
                  self.screen_rect.height() / 2 - self.frameSize().height() / 2)

    def move_log_window(self):
        _, top, right, _ = self.frameGeometry().getCoords()
        self.info_window.move(right + 1, top)

    def show_log_window(self):
        self.info_window.setFixedHeight(self.sizeHint().height())
        if self.screen_rect.width() <= 1920:
            self.move_aside()
        self.move_log_window()
        self.info_window.show()

    def set_display_size(self, size: str):
        self.config.app.width, self.config.app.height = tuple([int(x) for x in size.split('x')])
        self.label_video.setMinimumSize(self.config.app.width, self.config.app.height)
        self.label_video.setMaximumSize(self.config.app.width, self.config.app.height)
        self.label_video.resize(self.config.app.width, self.config.app.height)
        self.widget.adjustSize()
        self.adjustSize()
        self.label_video.setMaximumSize(self.screen_rect.size())
        self.other_width = self.size().width() - self.label_video.size().width()
        self.other_height = self.size().height() - self.label_video.size().height()
        if self.info_window.isVisible() and self.screen_rect.width() <= 1920:
            self.move_aside()
            self.info_window.setFixedHeight(self.sizeHint().height())
            self.move_log_window()
        elif self.info_window.isVisible():
            self.move_center()
            self.info_window.setFixedHeight(self.sizeHint().height())
            self.move_log_window()
        else:
            self.move_center()

    def event(self, event):
        if event.type() == QEvent.WindowActivate or event.type() == QEvent.FocusIn:
            if not self.is_playing:
                self.keyboard = KeyboardController(self.input)
                self.keyboard.start()
        elif event.type() == QEvent.WindowDeactivate or event.type() == QEvent.FocusOut:
            if self.keyboard is not None:
                self.keyboard.stop()
                self.keyboard = None
        return super().event(event)

    def resizeEvent(self, event) -> None:
        if not self.is_loaded:
            super().resizeEvent(event)
            self.move_center()
            self.is_loaded = True
            self.other_width = self.size().width() - self.label_video.size().width()
            self.other_height = self.size().height() - self.label_video.size().height()
        else:
            width = event.size().width() - self.other_width
            height = event.size().height() - self.other_height
            if height >= int(width*9/16):
                self.label_video.resize(width, int(width*9/16))
            else:
                self.label_video.resize(int(height*16/9), height)
            super().resizeEvent(event)

    def closeEvent(self, event):
        self.ser.close()
        self.video_timer.stop()
        self.cap.release()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.info_window.close()
        self.settings_window.close()
        self.config.write()
        if self.current_script is not None:
            self.stop_command()
        super().closeEvent(event)


class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Settings')
        self.setWindowFlags(Qt.Window |
                            Qt.WindowType.CustomizeWindowHint |
                            Qt.WindowType.WindowCloseButtonHint)

        # メインレイアウト
        layout = QVBoxLayout()

        # video group
        self.group_video = QGroupBox('video')

        video_layout = QHBoxLayout()

        self.combobox_video = QComboBox()
        for key in self.parent().cap_devices.values():
            self.combobox_video.addItem(key)

        video_layout.addWidget(self.combobox_video, 20)

        self.group_video.setLayout(video_layout)

        # ports group
        self.group_ports = QGroupBox('ports')

        ports_layout = QHBoxLayout()

        self.combobox_ports = QComboBox()
        for key in self.parent().ports:
            self.combobox_ports.addItem(key)

        ports_layout.addWidget(self.combobox_ports, 10)

        self.group_ports.setLayout(ports_layout)

        # display group
        self.group_display = QGroupBox('display')

        display_layout = QHBoxLayout()

        self.combobox_display = QComboBox()
        for key in self.parent().display_size_list:
            self.combobox_display.addItem('x'.join(map(str, key)))
        self.combobox_display.setCurrentText(
            f'{self.parent().config.app.width}x{self.parent().config.app.height}'
        )

        display_layout.addWidget(self.combobox_display, 10)

        self.group_display.setLayout(display_layout)

        layout.addWidget(self.group_video)
        layout.addWidget(self.group_ports)
        layout.addWidget(self.group_display)
        self.setLayout(layout)

        self.combobox_display.currentTextChanged.connect(self.parent().set_display_size)

    def closeEvent(self, event) -> None:
        if self.parent().screen_rect.width() <= 1920:
            self.parent().move_center()
        super().closeEvent(event)
