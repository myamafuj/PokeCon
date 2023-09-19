import os

from serial import Serial
from serial.serialutil import SerialException


class SerialSender:
    def __init__(self, show_serial=False):
        self.ser = None
        self.show_serial = show_serial

    def open(self, port):
        try:
            print(f'connecting to {port}')
            self.ser = Serial(port, 9600)
            return True
        except IOError as e:
            print('COM Port: cannot be established')
            print(e)
            return False

    def close(self):
        self.ser.close()

    def isOpen(self):
        return self.ser is not None and self.ser.isOpen()

    def write(self, row):
        try:
            self.ser.write((row + '\r\n').encode('utf-8'))
        except SerialException as e:
            print(e)
        except AttributeError:
            print('Attempting to use a port that is not open')

        # Show sending serial datas
        if self.show_serial:
            print(row)
