from pokecon.config import Config


def test_defaults():
    config = Config()
    assert config.app.width == 1280
    assert config.app.height == 720
    assert config.capture.camera_id == 0
    assert config.audio.volume is True


def test_read_without_file_keeps_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = Config()
    config.read()
    assert config.app.width == 1280
    assert config.serial.port == ''


def test_write_read_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = Config()
    config.app.width = 960
    config.app.height = 540
    config.serial.port = 'COM5'
    config.capture.camera_id = 1
    config.audio.volume = False
    config.write()

    loaded = Config()
    loaded.read()
    assert loaded.app.width == 960
    assert loaded.app.height == 540
    assert loaded.serial.port == 'COM5'
    assert loaded.capture.camera_id == 1
    assert loaded.audio.volume is False
