import importlib
import inspect
import os
from glob import glob
from pathlib import Path

from PySide2.QtMultimedia import QCameraInfo
from serial.tools import list_ports

from pokecon.command import PythonCommand
from pokecon.logger import get_logger


logger = get_logger(__name__)


def _get_class(m):
    list_c = inspect.getmembers(m, inspect.isclass)
    for tuple_c in list_c:
        _, c = tuple_c
        if issubclass(c, PythonCommand) and hasattr(c, 'NAME'):
            if c.NAME is not None:
                return c
    raise RuntimeError('Not found PythonCommand')


def get_scripts(path_dir=Path('scripts'), old=None):
    scripts = {}
    files = glob(str(path_dir.joinpath('**', '*.py')), recursive=True)
    for f in files:
        name = '.'.join(f[:-3].split(os.sep))
        m = importlib.import_module(name)
        c = _get_class(m)
        if old and c.NAME in old:
            m = importlib.reload(m)
            c = _get_class(m)
            logger.info(f'reloaded {c.NAME}')
        scripts[c.NAME] = c
    return scripts


def get_available_camera_id():
    result = {i: device.description() for i, device in enumerate(QCameraInfo.availableCameras())}
    if not result:
        raise RuntimeError('Cannot detect camera device')
    return result


def get_available_ports():
    result = sorted([port for port, _, _ in list_ports.comports()])
    if not result:
        raise RuntimeError('Cannot detect serial ports')
    return result
