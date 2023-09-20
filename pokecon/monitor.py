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
    QDialog,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout
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


class LogWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Log')
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint |
                            Qt.WindowType.WindowCloseButtonHint)

        # メインレイアウト
        layout = QVBoxLayout()

        # 結果出力窓
        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.logger = logging.getLogger()
        formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
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

    def clear_log(self):
        self.editor.clear()

    def closeEvent(self, event):
        event.accept()
