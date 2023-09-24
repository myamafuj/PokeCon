from configparser import ConfigParser, NoOptionError
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PysideConfig:
    width: int = 1280
    height: int = 720
    fps: int = 60


@dataclass
class SerialConfig:
    port: str = ''


@dataclass
class CaptureConfig:
    camera_id: int = 0
    width: int = 1920
    height: int = 1080
    fps: int = 60


@dataclass
class AudioConfig:
    volume: bool = True


class Config:
    def __init__(self):
        self.path = Path('conf/pokecon.ini')
        self.pyside: PysideConfig = PysideConfig()
        self.serial: SerialConfig = SerialConfig()
        self.capture: CaptureConfig = CaptureConfig()
        self.audio: AudioConfig = AudioConfig()

    def read(self):
        if self.path.exists():
            config = ConfigParser()
            config.read(self.path, encoding='utf-8')
            for section in ['pyside', 'serial', 'capture', 'audio']:
                r = eval(f'self.{section}')
                for k in vars(r):
                    attr = type(getattr(r, k))
                    try:
                        if attr is int:
                            setattr(r, k, config.getint(section, k))
                        elif attr is float:
                            setattr(r, k, config.getfloat(section, k))
                        elif attr is bool:
                            setattr(r, k, config.getboolean(section, k))
                        elif attr is str:
                            setattr(r, k, config.get(section, k))
                    except NoOptionError:
                        print('WARNING : {} NO OPTION'.format(k))

    def write(self):
        self.path.parent.mkdir(exist_ok=True)
        config = ConfigParser()
        for section in ['pyside', 'serial', 'capture', 'audio']:
            r = eval(f'self.{section}')
            config[section] = {}
            for k in vars(r):
                config[section][k] = str(getattr(r, k))
        with open(self.path, 'w', encoding='utf-8') as f:
            config.write(f)
