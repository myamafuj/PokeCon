from pathlib import Path

from PySide2.QtCore import (
    QEvent,
    Qt,
    QUrl,
    Slot
)
from PySide2.QtGui import (
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

from pokecon.capture import Capture, CaptureThread
from pokecon.command import ImageProcPythonCommand
from pokecon.keybord import KeyboardController
from pokecon.pad import Input
from pokecon.ports import SerialSender
from pokecon.monitor import LogWindow
from pokecon.utils import get_scripts, get_available_ports


VER = '1.0.0'
W = 1280
H = 720
FPS = 45


class Window(QMainWindow):
    def __init__(self, root):
        super().__init__()
        # unique settings
        # path
        self.root = Path(root).parent
        self.dir_img = self.root.joinpath('screenshot')
        # log
        self.log_w = LogWindow()
        # Thread in charge of updating the image
        self.cap = Capture(W, H, FPS, self.dir_img)
        self.th = CaptureThread(self.cap)
        self.th.finished.connect(self.close)
        self.th.change_pixmap_signal.connect(self.update_image)
        # serial
        self.ports = get_available_ports()
        self.ser = SerialSender()
        self.ser.open(self.ports[0])
        # keyboard
        self.input = Input(self.ser)
        self.keyboard = None
        # scripts
        self.scripts = get_scripts()
        self.current_script = None

        # Title and dimensions
        self.setWindowTitle(f'PokeCon v{VER}')
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint |
                            Qt.WindowType.WindowCloseButtonHint |
                            Qt.WindowType.WindowMinimizeButtonHint)

        # Main menu bar
        # self.menu = self.menuBar()
        #
        # self.menu_main = self.menu.addMenu('File')
        # self.exit = QAction('Exit', self)
        # self.exit.triggered.connect(QApplication.quit)
        # self.menu_main.addAction(self.exit)
        #
        # self.menu_camera = self.menu.addMenu('Camera')
        #
        # self.menu_ports = self.menu.addMenu('Ports')
        #
        # self.menu_about = self.menu.addMenu('&Help')
        # self.about = QAction('About Qt', self)
        # self.about.triggered.connect(QApplication.aboutQt)
        # self.menu_about.addAction(self.about)

        # Create a label for the display camera
        self.label_video = QLabel(self)
        self.label_video.setFixedSize(W, H)

        # image group
        self.group_image = QGroupBox('image')
        self.group_image.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        image_layout = QHBoxLayout()

        self.buttons_image = {}
        for key in ['screenshot', 'open']:
            self.buttons_image[key] = QPushButton(key)
            self.buttons_image[key].setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            image_layout.addWidget(self.buttons_image[key])

        self.group_image.setLayout(image_layout)

        # command group
        self.group_command = QGroupBox('command')
        self.group_command.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        command_layout = QHBoxLayout()

        self.combobox = QComboBox()
        for key in self.scripts.keys():
            self.combobox.addItem(key)

        command_layout.addWidget(QLabel('script:'), 12)
        command_layout.addWidget(self.combobox, 40)

        self.buttons_command = {}
        for key in ['reload', 'start', 'stop', 'log']:
            self.buttons_command[key] = QPushButton(key)
            self.buttons_command[key].setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            command_layout.addWidget(self.buttons_command[key], 12)

        self.group_command.setLayout(command_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.group_image, 30)
        bottom_layout.addWidget(self.group_command, 70)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.label_video)
        layout.addLayout(bottom_layout)

        # Central widget
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connections
        self.buttons_image['screenshot'].clicked.connect(self.cap.screenshot)
        self.buttons_image['open'].clicked.connect(self.open_dir)
        self.combobox.currentTextChanged.connect(self.set_current_script)
        self.buttons_command['reload'].clicked.connect(self.reload_scrips)
        self.buttons_command['start'].clicked.connect(self.start_command)
        self.buttons_command['stop'].clicked.connect(self.stop_command)
        self.buttons_command['log'].clicked.connect(self.show_log_window)

        self.th.start()

    @Slot(QImage)
    def update_image(self, image):
        self.label_video.setPixmap(QPixmap.fromImage(image))

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
        self.scripts = get_scripts()
        self.combobox.clear()
        for key in self.scripts.keys():
            self.combobox.addItem(key)
        key = self.combobox.currentText()
        self.set_current_script(key)
        self.buttons_command['reload'].setEnabled(True)

    def start_command(self):
        if self.current_script is None:
            key = self.combobox.currentText()
            cls = self.scripts[key]
            if issubclass(cls, ImageProcPythonCommand):
                self.current_script = cls(self.cap)
            else:
                self.current_script = cls()
        self.current_script.start(self.ser, self.start_command_post_process)
        self.buttons_command['start'].setEnabled(False)

    def start_command_post_process(self):
        self.buttons_command['start'].setEnabled(True)

    def stop_command(self):
        self.current_script.end(self.ser)
        self.buttons_command['start'].setEnabled(True)

    def start_keyboard(self):
        self.keyboard.start()

    def stop_keyboard(self):
        self.keyboard.stop()

    def show_log_window(self):
        self.buttons_command['log'].setEnabled(False)
        geometry = QApplication.primaryScreen().geometry()
        frame_size = self.frameSize()
        self.log_w.resize(600, frame_size.height() - 46)
        self.log_w.move(geometry.width() / 2 + frame_size.width() / 2,
                        geometry.height() / 2 - frame_size.height() / 2)
        self.log_w.show()
        self.buttons_command['log'].setEnabled(True)

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
        self.th.stop()
        self.log_w.close()
        event.accept()
        self.deleteLater()
