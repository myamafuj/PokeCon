import sys
from PySide2.QtCore import (
    Qt
)
from PySide2.QtGui import (
    QColor,
    QTextCursor
)
from PySide2.QtWidgets import (
    QDialog,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout
)


class Logger:
    def __init__(self, editor, out=None, color=None):
        self.editor = editor  # 結果出力用エディタ
        self.out = out  # 標準出力・標準エラーなどの出力オブジェクト
        # 結果出力時の色(Noneが指定されている場合、エディタの現在の色を入れる)
        if not color:
            self.color = editor.textColor()
        else:
            self.color = color

    def write(self, message):
        # カーソルを文末に移動。
        self.editor.moveCursor(QTextCursor.End)

        # color変数に値があれば、元カラーを残してからテキストのカラーを
        # 変更する。
        self.editor.setTextColor(self.color)

        # 文末にテキストを追加。
        self.editor.insertPlainText(message)

        # 出力オブジェクトが指定されている場合、そのオブジェクトにmessageを
        # 書き出す。
        if self.out:
            self.out.write(message)


class LogWindow(QDialog):
    def __init__(self, parent=None):
        # ログウィンドウのサンプル本体の初期化。-------------------------------
        super().__init__(parent)
        self.setWindowTitle('Log Window')
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint |
                            Qt.WindowType.WindowCloseButtonHint)
        # ---------------------------------------------------------------------

        # メインレイアウト。
        layout = QVBoxLayout()

        # 結果出力窓。=========================================================
        self.result = QTextEdit()
        self.result.setReadOnly(True)  # 編集不可に設定。
        self.result.setUndoRedoEnabled(False)  # Undo・Redo不可に設定。
        self.result.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # 標準出力と標準エラー出力の結果を結果出力窓に書き出すよう関連付ける。
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = Logger(self.result, sys.stdout)
        sys.stderr = Logger(self.result, sys.stderr, QColor(255, 0, 0))

        layout.addWidget(self.result)
        # =====================================================================

        self.button = QPushButton('clear')
        # self.button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.button.clicked.connect(self.clear_log)

    def clear_log(self):
        self.result.clear()

    def closeEvent(self, event):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        event.accept()
