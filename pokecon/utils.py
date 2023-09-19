import importlib
import inspect
import os
from glob import glob
from pathlib import Path

from serial.tools import list_ports

from pokecon.command import PythonCommand


def get_scripts(path_dir=Path('scripts')):
    scripts = {}
    files = glob(str(path_dir.joinpath('**', '*.py')), recursive=True)
    for f in files:
        name = '.'.join(f[:-3].split(os.sep)).replace('...', '..')
        m = importlib.import_module(name)
        list_c = inspect.getmembers(m, inspect.isclass)
        for tuple_c in list_c:
            _, c = tuple_c
            if issubclass(c, PythonCommand) and hasattr(c, 'NAME'):
                scripts[c.NAME] = c
    return scripts


def get_available_ports():
    return sorted([port for port, _, _ in list_ports.comports()])
