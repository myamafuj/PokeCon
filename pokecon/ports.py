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
            logger.info(f'connecting to {port}')
            self.ser = Serial(port, 9600)
            return True
        except IOError:
            logger.exception('COM Port: cannot be established')
            return False

    def close(self):
        self.ser.close()

    def isOpen(self):
        return self.ser is not None and self.ser.isOpen()

    def write(self, row):
        try:
            self.ser.write((row + '\r\n').encode('utf-8'))
        except SerialException:
            logger.exception()
        except AttributeError:
            logger.exception('Attempting to use a port that is not open')

        # Show sending serial datas
        if self.show_serial:
            logger.debug(row)
