import logging

from PySide2.QtCore import (
    QObject,
    Qt,
    Signal,
    Slot
)
from PySide2.QtGui import (
    QTextCursor
)
from PySide2.QtWidgets import (
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)


class QTextSignal(QObject):
    message = Signal(str)


class SignalHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.emitter = QTextSignal()

    def emit(self, record):
        msg = self.format(record)
        self.emitter.message.emit(msg)


class InfoWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Info')
        self.setWindowFlags(Qt.Window |
                            Qt.WindowType.CustomizeWindowHint |
                            Qt.WindowType.WindowCloseButtonHint)

        # メインレイアウト
        self.setFixedWidth(540)
        layout = QVBoxLayout()

        # 結果出力窓
        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.logger = logging.getLogger()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:\n%(message)s\n')
        self.signal_handler = SignalHandler()
        self.signal_handler.setFormatter(formatter)
        self.signal_handler.setLevel(logging.INFO)
        self.signal_handler.emitter.message.connect(self.write)
        self.logger.addHandler(self.signal_handler)

        layout.addWidget(self.editor)

        self.button = QPushButton('clear')
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.button.clicked.connect(self.clear_log)

    @Slot(str)
    def write(self, msg):
        self.editor.moveCursor(QTextCursor.End)
        self.editor.insertPlainText(msg + '\n')
        self.editor.moveCursor(QTextCursor.End)

    def clear_log(self):
        self.editor.clear()
