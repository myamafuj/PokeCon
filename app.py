import sys

from PySide2.QtWidgets import QApplication

from pokecon.window import Window


def main():
    app = QApplication(sys.argv)
    w = Window(__file__)
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
