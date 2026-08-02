import pytest

from pokecon.command import PythonCommand
from pokecon.utils import get_available_camera_id, get_available_ports, get_scripts


def test_get_scripts():
    scripts = get_scripts()
    assert 'A連打' in scripts
    assert '下+A連打' in scripts
    assert 'ZL+A連打' in scripts
    assert all(issubclass(c, PythonCommand) for c in scripts.values())


def test_get_scripts_reload():
    scripts = get_scripts()
    reloaded = get_scripts(old=list(scripts.keys()))
    assert scripts.keys() == reloaded.keys()


def test_get_available_camera_id(qapp):
    try:
        cameras = get_available_camera_id()
    except RuntimeError:
        pytest.skip('カメラデバイスが接続されていない')
    assert all(isinstance(i, int) for i in cameras)
    assert all(isinstance(name, str) and name for name in cameras.values())


def test_get_available_ports():
    try:
        ports = get_available_ports()
    except RuntimeError:
        pytest.skip('シリアルポートが存在しない')
    assert ports == sorted(ports)
    assert all(isinstance(p, str) for p in ports)
