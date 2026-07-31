import logging


def test_import_all_qt_modules():
    # PySide6移行後もGUI関連モジュールがimportできること
    import app  # noqa: F401
    import pokecon.monitor  # noqa: F401
    import pokecon.window  # noqa: F401


def test_info_window(qapp):
    from pokecon.monitor import InfoWindow

    window = InfoWindow()
    try:
        window.write('hello')
        assert 'hello' in window.editor.toPlainText()
        window.clear_log()
        assert window.editor.toPlainText() == ''
    finally:
        logging.getLogger().removeHandler(window.signal_handler)


def test_signal_handler_emits_message(qapp):
    from pokecon.monitor import SignalHandler

    handler = SignalHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    received = []
    handler.emitter.message.connect(received.append)
    logger = logging.getLogger('test_signal_handler')
    logger.addHandler(handler)
    logger.warning('ログ出力テスト')
    assert received == ['ログ出力テスト']
