import pytest
import sys
from types import ModuleType

pytest.importorskip("anywidget")
pytest.importorskip("traitlets")

from molsysviewer import demo
from molsysviewer.standalone import build_standalone0_html, launch_standalone0, main
from molsysviewer.standalone_qt import QT_IMPORT_ERROR, create_standalone_qt0_window, main as qt_main


def test_build_standalone0_html_writes_file(tmp_path):
    view = demo["dialanine"]
    outfile = tmp_path / "standalone0.html"

    result = build_standalone0_html(view, str(outfile), include_popout=False)

    assert result == str(outfile.resolve())
    assert outfile.exists()
    text = outfile.read_text(encoding="utf-8")
    assert "MolSysViewer Standalone 0" in text


def test_launch_standalone0_can_skip_browser(tmp_path):
    view = demo["dialanine"]
    outfile = tmp_path / "launch.html"

    result = launch_standalone0(view, str(outfile), open_browser=False, include_popout=False)

    assert result == str(outfile.resolve())
    assert outfile.exists()


def test_standalone_main_supports_demo_mode_without_browser(tmp_path, capsys):
    outfile = tmp_path / "cli.html"

    code = main(["dialanine", "--demo", "--no-browser", "--output", str(outfile)])

    assert code == 0
    assert outfile.exists()
    assert str(outfile.resolve()) in capsys.readouterr().out


def test_standalone_main_supports_empty_host_without_browser(tmp_path, capsys):
    outfile = tmp_path / "empty.html"

    code = main(["--no-browser", "--output", str(outfile)])

    assert code == 0
    assert outfile.exists()
    assert str(outfile.resolve()) in capsys.readouterr().out
    text = outfile.read_text(encoding="utf-8")
    assert "no molecular system has been loaded yet" in text
    assert "molsysviewer dialanine --demo" in text
    assert "empty-demo-dialanine.html" in text
    assert (tmp_path / "empty-demo-dialanine.html").exists()


def test_create_standalone_qt0_window_raises_informative_import_error(monkeypatch):
    for name in [
        "PySide6",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtWebEngineWidgets",
    ]:
        monkeypatch.delitem(sys.modules, name, raising=False)

    with pytest.raises(ImportError, match="PySide6 with Qt WebEngine is required"):
        create_standalone_qt0_window(None)


def test_create_standalone_qt0_window_builds_minimal_runtime(monkeypatch, tmp_path):
    module_core = ModuleType("PySide6.QtCore")
    module_gui = ModuleType("PySide6.QtGui")
    module_widgets = ModuleType("PySide6.QtWidgets")
    module_web = ModuleType("PySide6.QtWebEngineWidgets")
    module_root = ModuleType("PySide6")

    class FakeSignal:
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

    class FakeAction:
        def __init__(self, text, _parent=None):
            self.text = text
            self.triggered = FakeSignal()

    class FakeMenu:
        def __init__(self, title):
            self.title = title
            self.actions = []

        def addAction(self, action):
            self.actions.append(action)
            return action

    class FakeMenuBar:
        def __init__(self):
            self.menus = []

        def addMenu(self, title):
            menu = FakeMenu(title)
            self.menus.append(menu)
            return menu

    class FakeStatusBar:
        def __init__(self):
            self.messages = []

        def showMessage(self, message):
            self.messages.append(message)

    class FakeMainWindow:
        def __init__(self):
            self.title = None
            self.size = None
            self.central_widget = None
            self.menu_bar = FakeMenuBar()
            self.status_bar = FakeStatusBar()
            self.shown = False
            self.closed = False

        def setWindowTitle(self, title):
            self.title = title

        def resize(self, width, height):
            self.size = (width, height)

        def setCentralWidget(self, widget):
            self.central_widget = widget

        def menuBar(self):
            return self.menu_bar

        def statusBar(self):
            return self.status_bar

        def show(self):
            self.shown = True

        def close(self):
            self.closed = True

    class FakeWebView:
        def __init__(self, _parent=None):
            self.url = None

        def setUrl(self, url):
            self.url = url

    class FakeQUrl:
        @staticmethod
        def fromLocalFile(path):
            return f"file://{path}"

    class FakeApplication:
        _instance = None

        def __init__(self, argv):
            self.argv = list(argv)
            self.exec_calls = 0
            FakeApplication._instance = self

        @classmethod
        def instance(cls):
            return cls._instance

        def exec(self):
            self.exec_calls += 1
            return 0

    module_core.QUrl = FakeQUrl
    module_gui.QAction = FakeAction
    module_widgets.QApplication = FakeApplication
    module_widgets.QMainWindow = FakeMainWindow
    module_web.QWebEngineView = FakeWebView

    monkeypatch.setitem(sys.modules, "PySide6", module_root)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", module_core)
    monkeypatch.setitem(sys.modules, "PySide6.QtGui", module_gui)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", module_widgets)
    monkeypatch.setitem(sys.modules, "PySide6.QtWebEngineWidgets", module_web)

    outfile = tmp_path / "qt0.html"
    runtime = create_standalone_qt0_window(
        demo["dialanine"],
        output_filename=str(outfile),
        title="Qt Prototype",
        width=1200,
        height=800,
    )

    assert runtime["html_path"] == str(outfile.resolve())
    assert runtime["window"].title == "Qt Prototype"
    assert runtime["window"].size == (1200, 800)
    assert runtime["webview"].url == f"file://{outfile.resolve()}"
    assert [menu.title for menu in runtime["window"].menu_bar.menus] == ["File", "View", "Export"]


def test_qt_standalone_main_supports_no_exec(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "molsysviewer.standalone_qt.launch_standalone_qt0",
        lambda *args, **kwargs: {"html_path": str((tmp_path / "qt-main.html").resolve())},
    )

    code = qt_main(["dialanine", "--demo", "--output", str(tmp_path / "qt-main.html"), "--no-exec"])

    assert code == 0
    assert str((tmp_path / "qt-main.html").resolve()) in capsys.readouterr().out
    assert QT_IMPORT_ERROR.startswith("PySide6")
