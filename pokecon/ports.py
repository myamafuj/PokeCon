from serial import Serial
from serial.serialutil import SerialException

from pokecon.logger import get_logger


logger = get_logger(__name__)


class SerialSender:
    def __init__(self, show_serial=False):
        self.ser = None
        self.show_serial = show_serial

    def open(self, port):
        try:
            self.ser = Serial(port, 9600)
            logger.info(f'Successfully connected to {port}')
            return True
        except IOError:
            logger.error('COM Port: cannot be established', exc_info=True)
            return False

    def close(self):
        self.ser.close()

    def is_open(self):
        return self.ser is not None and self.ser.isOpen()

    def write(self, row):
        try:
            self.ser.write((row + '\r\n').encode('utf-8'))
        except SerialException:
            logger.error('SerialException', exc_info=True)
        except AttributeError:
            logger.error('Attempting to use a port that is not open', exc_info=True)

        # Show sending serial datas
        if self.show_serial:
            logger.debug(row)
