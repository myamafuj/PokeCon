import logging
from pathlib import Path

from PySide2.QtCore import (
    QEvent,
    Qt,
    QSize,
    QTimer,
    QUrl,
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
from pokecon.keybord import KeyboardController
from pokecon.pad import Input
from pokecon.ports import SerialSender
from pokecon.monitor import InfoWindow, SignalHandler
from pokecon.utils import get_scripts, get_available_camera_id, get_available_ports


VER = '1.1.1'
W_DISPLAY = 1280
H_DISPLAY = 720
FPS_DISPLAY = 45
W_CAP = 1920
H_CAP = 1080
FPS_CAP = 45


class Window(QMainWindow):
    def __init__(self, root):
        super().__init__()
        # unique settings
        # log
        self.logger = logging.getLogger()
        formatter = logging.Formatter(' %(asctime)s [%(levelname)s] %(name)s: %(message)s')
        self.signal_handler = SignalHandler()
        self.signal_handler.setFormatter(formatter)
        self.signal_handler.setLevel(logging.INFO)
        self.signal_handler.emitter.message.connect(self.write)
        self.logger.addHandler(self.signal_handler)
        # self.statusBar()
        # path
        self.root = Path(root).parent
        self.dir_img = self.root.joinpath('screenshot')
        # log
        self.info_window = InfoWindow()
        # capture
        self.cap_devices = get_available_camera_id()
        self.default_camera_id = list(self.cap_devices.values())[0]
        self.cap = Capture(self.default_camera_id, W_CAP, H_CAP, FPS_CAP, self.dir_img)
        # serial
        self.ports = get_available_ports()
        self.default_port = self.ports[0]
        self.ser = SerialSender()
        self.ser.open(self.default_port)
        # keyboard
        self.input = Input(self.ser)
        self.keyboard = None
        # scripts
        self.scripts = get_scripts()
        self.current_script = None
        # settings
        self.geometry = QApplication.primaryScreen().geometry()
        self.display_size_list = ['1920x1080', '1280x720']
        self.default_display_size = self.display_size_list[1]
        self.settings_window = SettingsWindow(self)

        # Title and dimensions
        self.setWindowTitle(f'PokeCon v{VER}')
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint |
                            Qt.WindowType.WindowCloseButtonHint |
                            Qt.WindowType.WindowMinimizeButtonHint)

        # Create a label for the display camera
        self.label_video = QLabel(self)
        self.label_video.setFixedSize(*[int(x) for x in self.default_display_size.split('x')])

        # settings
        self.button_settings = QPushButton('')
        self.button_settings.setIcon(QIcon(str(self.root.joinpath('assets/settings.png'))))
        self.button_settings.setIconSize(QSize(32, 32))
        self.button_settings.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # image group
        self.group_image = QGroupBox('screenshot')
        self.group_image.setTitle('')
        self.group_image.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        image_layout = QHBoxLayout()

        self.image_label = QLabel('screenshot:')
        image_layout.addWidget(self.image_label, 5)

        self.buttons_image = {}
        for key in ['save', 'open']:
            self.buttons_image[key] = QPushButton(key)
            self.buttons_image[key].setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            image_layout.addWidget(self.buttons_image[key], 10)

        self.group_image.setLayout(image_layout)

        # command group
        self.group_command = QGroupBox('command')
        self.group_command.setTitle('')
        self.group_command.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        command_layout = QHBoxLayout()

        self.command_label = QLabel('command:')
        command_layout.addWidget(self.command_label, 5)

        self.combobox_command = QComboBox()
        for key in self.scripts.keys():
            self.combobox_command.addItem(key)

        command_layout.addWidget(self.combobox_command, 20)

        self.buttons_command = {}
        for key in ['reload', 'start/stop', 'log']:
            self.buttons_command[key] = QPushButton(key)
            self.buttons_command[key].setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            command_layout.addWidget(self.buttons_command[key], 10)
        self.buttons_command['start/stop'].setText('start')

        self.group_command.setLayout(command_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.button_settings, 5)
        bottom_layout.addWidget(self.group_image, 25)
        bottom_layout.addWidget(self.group_command, 55)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.label_video)
        layout.addLayout(bottom_layout)

        # Central widget
        self.widget = QWidget(self)
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)

        # Connections
        self.button_settings.clicked.connect(self.show_settings_window)
        self.buttons_image['save'].clicked.connect(self.cap.screenshot)
        self.buttons_image['open'].clicked.connect(self.open_dir)
        self.combobox_command.currentTextChanged.connect(self.set_current_script)
        self.buttons_command['reload'].clicked.connect(self.reload_scrips)
        self.buttons_command['start/stop'].clicked.connect(self.command)
        self.buttons_command['log'].clicked.connect(self.show_log_window)

        # video
        self.video_timer = QTimer()
        millisecond = int(1000.0 / FPS_DISPLAY)
        self.video_timer.setTimerType(Qt.CoarseTimer)  # Qt.PreciseTimerとの負荷比較したい
        self.video_timer.timeout.connect(self.next_frame)
        self.video_timer.start(millisecond)

    def next_frame(self):
        ret, frame = self.cap.read()
        if ret:
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
            pix = QPixmap.fromImage(img)
            pix = pix.scaled(self.label_video.width(), self.label_video.height(),
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label_video.setPixmap(pix)

    @Slot(str)
    def write(self, msg):
        self.statusBar().showMessage(msg)

    def show_settings_window(self):
        self.settings_window.show()

    def open_dir(self):
        QDesktopServices.openUrl(QUrl(f'file:///{self.dir_img}'))

    def set_current_script(self, key):
        if key:
            cls_ = self.scripts[key]
            if issubclass(cls_, ImageProcPythonCommand):
                self.current_script = cls_(self.cap)
            else:
                self.current_script = cls_()

    def reload_scrips(self):
        self.buttons_command['reload'].setEnabled(False)
        self.combobox_command.clear()
        del self.scripts
        self.scripts = get_scripts()
        for key in self.scripts.keys():
            self.combobox_command.addItem(key)
        key = self.combobox_command.currentText()
        self.set_current_script(key)
        self.buttons_command['reload'].setEnabled(True)

    def command(self):
        if self.buttons_command['start/stop'].text() == 'start':
            self.command_pre_process()
            self.start_command()

        elif self.buttons_command['start/stop'].text() == 'stop':
            self.stop_command()
            self.command_post_process()

    def start_command(self):
        if self.current_script is None:
            key = self.combobox_command.currentText()
            cls = self.scripts[key]
            if issubclass(cls, ImageProcPythonCommand):
                self.current_script = cls(self.cap)
            else:
                self.current_script = cls()
        self.current_script.start(self.ser, self.command_post_process)

    def command_pre_process(self):
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

    def stop_command(self):
        self.current_script.end(self.ser)

    def show_log_window(self):
        self.buttons_command['log'].setEnabled(False)
        frame_size = self.frameSize()
        self.info_window.resize(654, frame_size.height() - 46)
        if self.geometry.width() <= 1920:
            self.info_window.move(self.geometry.width() / 3 + frame_size.width() * 2 / 3,
                                  self.geometry.height() / 2 - frame_size.height() / 2)
        else:
            self.info_window.move(self.geometry.width() / 2 + frame_size.width() / 2,
                                  self.geometry.height() / 2 - frame_size.height() / 2)
        self.info_window.show()
        self.buttons_command['log'].setEnabled(True)

    def set_display_size(self, size: str):
        self.label_video.setFixedSize(*[int(x) for x in size.split('x')])
        self.widget.adjustSize()
        self.adjustSize()
        frame_size = self.frameSize()
        if self.geometry.width() <= 1920:
            self.move(self.geometry.width() / 3 + frame_size.width() / 3,
                      self.geometry.height() / 2 - frame_size.height() / 2)
        else:
            self.move(self.geometry.width() / 2 - frame_size.width() / 2,
                      self.geometry.height() / 2 - frame_size.height() / 2)

    def event(self, event):
        if event.type() == QEvent.WindowActivate or event.type() == QEvent.FocusIn:
            self.keyboard = KeyboardController(self.input)
            self.keyboard.start()
        elif event.type() == QEvent.WindowDeactivate or event.type() == QEvent.FocusOut:
            self.keyboard.stop()
            self.keyboard = None
        return super().event(event)

    # def keyPressEvent(self, e):
    #     if e.key() == Qt.Key.Key_Q:
    #         self.th.stop()
    #         sys.exit()

    def closeEvent(self, event):
        self.video_timer.stop()
        self.cap.release()
        self.info_window.close()
        self.settings_window.close()
        event.accept()


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
        for key in self.parent().cap_devices.keys():
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
            self.combobox_display.addItem(key)
        self.combobox_display.setCurrentText(self.parent().default_display_size)

        display_layout.addWidget(self.combobox_display, 10)

        self.group_display.setLayout(display_layout)

        layout.addWidget(self.group_video)
        layout.addWidget(self.group_ports)
        layout.addWidget(self.group_display)
        self.setLayout(layout)

        self.combobox_display.currentTextChanged.connect(self.parent().set_display_size)
