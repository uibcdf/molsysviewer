import json
import pytest
import sys
from types import ModuleType

pytest.importorskip("anywidget")
pytest.importorskip("traitlets")

from molsysviewer import demo
from molsysviewer.standalone import build_standalone0_html, launch_standalone0, main
import molsysviewer.standalone_qt as standalone_qt
from molsysviewer.standalone_qt import QT_IMPORT_ERROR, create_standalone_qt0_window, main as qt_main


def test_build_standalone0_html_writes_file(tmp_path):
    view = demo["dialanine"]
    outfile = tmp_path / "standalone0.html"

    result = build_standalone0_html(view, str(outfile), include_popout=False)

    assert result == str(outfile.resolve())
    assert outfile.exists()
    text = outfile.read_text(encoding="utf-8")
    assert "MolSysViewer Standalone 0" in text


def test_build_standalone0_html_supports_lite_runtime_urls(tmp_path):
    view = demo["dialanine"]
    outfile = tmp_path / "standalone0-lite.html"

    result = build_standalone0_html(
        view,
        str(outfile),
        include_popout=False,
        mode="lite",
        runtime_urls=["file:///tmp/molsysviewer-viewer.js", "https://example.invalid/viewer.js"],
    )

    assert result == str(outfile.resolve())
    text = outfile.read_text(encoding="utf-8")
    assert 'type="module"' in text
    assert "requirejs" not in text
    assert "file:///tmp/molsysviewer-viewer.js" in text


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
    def _raise():
        raise ImportError(QT_IMPORT_ERROR)

    monkeypatch.setattr(standalone_qt, "_import_qt", _raise)
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

        def addMenu(self, title):
            menu = FakeMenu(title)
            self.actions.append(menu)
            return menu

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
            self.scripts = []

        def setUrl(self, url):
            self.url = url

        def page(self):
            return self

        def runJavaScript(self, script):
            self.scripts.append(script)

    class FakeFileDialog:
        selected = ""
        saved = ""

        @staticmethod
        def getOpenFileName(_parent=None, _title="", _dir="", _filter=""):
            return FakeFileDialog.selected, "Molecular systems (*)"

        @staticmethod
        def getSaveFileName(_parent=None, _title="", _dir="", _filter=""):
            return FakeFileDialog.saved, "HTML files (*.html)"

    class FakeInputDialog:
        value = ""
        accepted = True
        item = ""

        @staticmethod
        def getText(_parent=None, _title="", _label=""):
            return FakeInputDialog.value, FakeInputDialog.accepted

        @staticmethod
        def getItem(_parent=None, _title="", _label="", _items=(), _current=0, _editable=False):
            return FakeInputDialog.item, FakeInputDialog.accepted

    class FakeMessageBox:
        calls = []

        @staticmethod
        def information(_parent=None, title="", text=""):
            FakeMessageBox.calls.append((title, text))

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
    module_widgets.QFileDialog = FakeFileDialog
    module_widgets.QInputDialog = FakeInputDialog
    module_widgets.QMainWindow = FakeMainWindow
    module_widgets.QMessageBox = FakeMessageBox
    module_web.QWebEngineView = FakeWebView

    monkeypatch.setitem(sys.modules, "PySide6", module_root)
    monkeypatch.setitem(sys.modules, "PySide6.QtCore", module_core)
    monkeypatch.setitem(sys.modules, "PySide6.QtGui", module_gui)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", module_widgets)
    monkeypatch.setitem(sys.modules, "PySide6.QtWebEngineWidgets", module_web)
    monkeypatch.setattr(
        "molsysviewer.standalone_qt._qt_shell_state_path",
        lambda: tmp_path / "standalone_qt0_state.json",
    )

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
    assert [menu.title for menu in runtime["window"].menu_bar.menus] == ["File", "View", "Export", "Help"]
    file_menu = runtime["window"].menu_bar.menus[0]
    demo_menu = file_menu.actions[1]
    recent_menu = file_menu.actions[2]
    load_pdbid_action = file_menu.actions[3]
    load_source_action = file_menu.actions[4]
    restore_last_action = file_menu.actions[5]
    close_action = file_menu.actions[6]
    assert demo_menu.title == "Load Demo"
    assert recent_menu.title == "Recent"
    assert recent_menu.actions[0].text == "No recent sources"
    FakeFileDialog.selected = str(tmp_path / "picked-system.pdb")
    calls = []
    monkeypatch.setattr(
        "molsysviewer.standalone_qt._rebuild_qt_html",
        lambda molecular_system, *, html_path, title: calls.append((molecular_system, html_path, title)) or html_path,
    )
    file_menu.actions[0].triggered._callbacks[0]()
    assert calls == [(str(tmp_path / "picked-system.pdb"), str(outfile.resolve()), "Qt Prototype")]
    assert runtime["webview"].url == f"file://{outfile.resolve()}"
    assert runtime["window"].status_bar.messages[-1] == "Loaded file: picked-system.pdb"
    assert runtime["window"].title == "Qt Prototype · picked-system.pdb"
    assert recent_menu.actions[0].text == "picked-system.pdb"
    demo_action = next(action for action in demo_menu.actions if action.text == "pentalanine")
    demo_action.triggered._callbacks[0]()
    assert calls[-1][1:] == (str(outfile.resolve()), "Qt Prototype")
    assert type(calls[-1][0]).__name__ == "MolSysView"
    assert runtime["window"].status_bar.messages[-1] == "Loaded demo: pentalanine"
    assert runtime["window"].title == "Qt Prototype · pentalanine"
    assert recent_menu.actions[0].text == "pentalanine"
    assert recent_menu.actions[1].text == "picked-system.pdb"
    FakeInputDialog.value = "1crn"
    load_pdbid_action.triggered._callbacks[0]()
    assert calls[-1] == ("1crn", str(outfile.resolve()), "Qt Prototype")
    assert runtime["window"].status_bar.messages[-1] == "Loaded PDB ID: 1crn"
    assert runtime["window"].title == "Qt Prototype · 1crn"
    assert recent_menu.actions[0].text == "1crn"
    assert recent_menu.actions[1].text == "pentalanine"
    FakeInputDialog.value = "molsysmt.MolSys"
    load_source_action.triggered._callbacks[0]()
    assert calls[-1] == ("molsysmt.MolSys", str(outfile.resolve()), "Qt Prototype")
    assert runtime["window"].status_bar.messages[-1] == "Loaded source: molsysmt.MolSys"
    assert runtime["window"].title == "Qt Prototype · molsysmt.MolSys"
    assert recent_menu.actions[0].text == "molsysmt.MolSys"
    assert recent_menu.actions[1].text == "1crn"
    restore_last_action.triggered._callbacks[0]()
    assert calls[-1] == ("molsysmt.MolSys", str(outfile.resolve()), "Qt Prototype")
    assert runtime["window"].status_bar.messages[-1] == "Loaded source: molsysmt.MolSys"
    recent_menu.actions[1].triggered._callbacks[0]()
    assert runtime["window"].status_bar.messages[-1] == "Loaded PDB ID: 1crn"
    assert runtime["window"].title == "Qt Prototype · 1crn"
    view_menu = runtime["window"].menu_bar.menus[1]
    for action in view_menu.actions:
        assert action.triggered._callbacks
        action.triggered._callbacks[0]()
    scripts = runtime["webview"].scripts
    assert any('"panel":"navigate"' in script for script in scripts)
    assert any('"panel":"workbench"' in script for script in scripts)
    assert any('"expanded":false' in script and '"panel":null' in script for script in scripts)
    export_menu = runtime["window"].menu_bar.menus[2]
    FakeFileDialog.saved = str(tmp_path / "exported-view.html")
    export_menu.actions[0].triggered._callbacks[0]()
    exported = tmp_path / "exported-view.html"
    assert exported.exists()
    assert runtime["window"].status_bar.messages[-1] == "Exported HTML: exported-view.html"
    figure_calls = []
    monkeypatch.setattr(
        "molsysviewer.standalone_qt._export_qt_figure",
        lambda molecular_system, *, output_filename, title: figure_calls.append(
            (molecular_system, output_filename, title)
        ) or output_filename,
    )
    FakeFileDialog.saved = str(tmp_path / "exported-figure.png")
    export_menu.actions[1].triggered._callbacks[0]()
    assert len(figure_calls) == 1
    assert figure_calls[0][0] == "1crn"
    assert figure_calls[0][1:] == (str((tmp_path / "exported-figure.png").resolve()), "Qt Prototype")
    assert runtime["window"].status_bar.messages[-1] == "Exported Figure: exported-figure.png"
    help_menu = runtime["window"].menu_bar.menus[3]
    help_menu.actions[0].triggered._callbacks[0]()
    assert FakeMessageBox.calls
    assert FakeMessageBox.calls[-1][0] == "About MolSysViewer Qt Prototype"
    help_menu.actions[1].triggered._callbacks[0]()
    assert runtime["window"].status_bar.messages[-1] == "Current source: 1crn"
    help_menu.actions[2].triggered._callbacks[0]()
    assert runtime["window"].status_bar.messages[-1] == "Loaded PDB ID: 1crn"
    close_action.triggered._callbacks[0]()
    assert runtime["window"].closed is True
    persisted = (tmp_path / "standalone_qt0_state.json").read_text(encoding="utf-8")
    assert '"kind": "pdb_id"' in persisted
    assert '"loaded_label": "1crn"' in persisted
    assert '"last_source"' in persisted


def test_load_qt_shell_state_restores_recent_sources(tmp_path, monkeypatch):
    state_path = tmp_path / "standalone_qt0_state.json"
    state_path.write_text(
        json.dumps(
            {
                "recent_sources": [
                    {"kind": "source", "value": "molsysmt.MolSys", "loaded_label": "molsysmt.MolSys"},
                    {"kind": "pdb_id", "value": "1crn", "loaded_label": "1crn"},
                ],
                "last_source": {"kind": "pdb_id", "value": "1crn", "loaded_label": "1crn"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("molsysviewer.standalone_qt._qt_shell_state_path", lambda: state_path)

    state = standalone_qt._load_qt_shell_state()

    assert [item["loaded_label"] for item in state["recent_sources"]] == ["molsysmt.MolSys", "1crn"]
    assert state["last_source"]["loaded_label"] == "1crn"


def test_qt_standalone_main_supports_no_exec(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "molsysviewer.standalone_qt.launch_standalone_qt0",
        lambda *args, **kwargs: {"html_path": str((tmp_path / "qt-main.html").resolve())},
    )

    code = qt_main(["dialanine", "--demo", "--output", str(tmp_path / "qt-main.html"), "--no-exec"])

    assert code == 0
    assert str((tmp_path / "qt-main.html").resolve()) in capsys.readouterr().out
    assert QT_IMPORT_ERROR.startswith("PySide6")
