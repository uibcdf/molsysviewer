"""Real Qt widget receiving for status access and saved window geometry."""

import json
import sys
from pathlib import Path


def main():
    import molsysviewer.standalone_qt as standalone
    from molsysviewer.standalone_qt.chrome import _install_window_chrome
    from molsysviewer.standalone_qt.geometry import _capture_geometry, _restore_geometry
    from molsysviewer.standalone_qt.status import _StatusMessage
    from molsysviewer.standalone_qt.utils import (
        _capture_window_size,
        _load_qt_shell_state,
        _persist_shell_state,
        _show_status,
    )
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtTest import QTest

    app = QtWidgets.QApplication([])
    window = QtWidgets.QMainWindow()
    window.resize(700, 500)
    web = QtWidgets.QWidget()
    qt = {"QtCore": QtCore, "QtGui": QtGui, "QtWidgets": QtWidgets}
    chrome = _install_window_chrome(window=window, webview=web, qt=qt)
    window.show()
    app.processEvents()
    standalone._qt_shell_state_path = lambda: Path(sys.argv[1]).with_name("state.json")
    try:
        for name in ("error.png", "loading.png", "rendering.png", "timeout.html"):
            _show_status(window, f"Exported: {name}", kind="info")
            assert chrome.status_timer.isActive()
            assert "#dc3545" not in chrome.status.styleSheet()
        _show_status(window, "Download interrupted: figure.png: disconnected", kind="error")
        assert not chrome.status_timer.isActive()
        assert "#dc3545" in chrome.status.styleSheet()
        _show_status(window, _StatusMessage("Preparing the system", "progress"))
        assert not chrome.status_timer.isActive()
        message = "Could not load file: " + "a long filename " * 25
        _show_status(window, message, kind="error")
        app.processEvents()
        target = app.widgetAt(chrome.status.mapToGlobal(chrome.status.rect().center()))
        assert target is chrome.status, target
        QTest.mouseClick(chrome.status, QtCore.Qt.MouseButton.LeftButton)
        app.processEvents()
        text = chrome.details.findChild(QtWidgets.QPlainTextEdit, "molsysviewerStatusText")
        assert text.toPlainText() == message and text.isReadOnly()
        copy = chrome.details.findChild(QtWidgets.QPushButton, "molsysviewerCopyStatus")
        QTest.mouseClick(copy, QtCore.Qt.MouseButton.LeftButton)
        assert app.clipboard().text() == message
        chrome.details.close()
        app.processEvents()
        assert chrome.details is None
        normal = _capture_window_size(window)
        geometry = _capture_geometry(window)
        window.showMaximized()
        app.processEvents()
        assert _capture_window_size(window) == normal
        assert _capture_geometry(window)["width"] == geometry["width"]
        _persist_shell_state({}, window=window)
        saved = _load_qt_shell_state()
        assert saved["window_size"] == normal
        assert saved["window_maximized"] is True
        window.showFullScreen()
        app.processEvents()
        assert _capture_window_size(window) == normal
        assert chrome.fullscreen_status.isVisible()
        _show_status(window, "Ready.", kind="ready")
        assert not chrome.fullscreen_status.isVisible()
        assert not chrome.status.isVisible()
        assert chrome.last_status == message
        window.showNormal()
        app.processEvents()
        restored = QtWidgets.QMainWindow()
        _install_window_chrome(window=restored, webview=QtWidgets.QWidget(), qt=qt)
        _restore_geometry(
            restored, app, qt, {"window_geometry": {**geometry, "x": 99999, "y": -99999}, "window_maximized": True}
        )
        assert restored.isMaximized()
        restored.showNormal()
        app.processEvents()
        assert app.primaryScreen().availableGeometry().contains(restored.geometry()), restored.geometry()
        _restore_geometry(
            restored,
            app,
            qt,
            {"window_size": {"width": 700, "height": 500}, "window_maximized": True},
            width=600,
            height=400,
        )
        assert not restored.isMaximized()
        assert restored.width() == 600 and restored.height() == 400
        _restore_geometry(restored, app, qt, {"window_size": {"width": 650, "height": 450}})
        assert restored.width() == 650 and restored.height() == 450
        restored.close()
        Path(sys.argv[1]).write_text(
            json.dumps({"status": True, "details": True, "geometry": True, "platform": app.platformName()})
        )
    finally:
        window.close()
        app.processEvents()


if __name__ == "__main__":
    main()
