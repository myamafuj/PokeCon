import sys

from PySide2.QtWidgets import QApplication

from pokecon.window import Window


def main():
    app = QApplication(sys.argv)
    geometry = app.primaryScreen().geometry()
    w = Window(__file__)
    w.show()
    frame_size = w.frameSize()
    if geometry.width() <= 1920:
        w.move(geometry.width() / 3 - frame_size.width() / 3,
               geometry.height() / 2 - frame_size.height() / 2)
    else:
        w.move(geometry.width() / 2 - frame_size.width() / 2,
               geometry.height() / 2 - frame_size.height() / 2)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
