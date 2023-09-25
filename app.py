import os
import sys
from pathlib import Path

from PySide2.QtWidgets import QApplication

from pokecon.window import Window


def main():
    root = Path(sys.argv[0]).parent
    sys.path.append(str(root))
    app = QApplication(sys.argv)
    w = Window(root)
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
