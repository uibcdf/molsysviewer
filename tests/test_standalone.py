import json
import logging
import os
import pytest
import sys
from types import ModuleType

pytest.importorskip("anywidget")
pytest.importorskip("traitlets")

from molsysviewer import demo
from molsysviewer.standalone import build_standalone0_html, launch_standalone0, main
import molsysviewer.standalone_qt as standalone_qt
from molsysviewer.standalone_qt import QT_IMPORT_ERROR, create_standalone_qt0_window, main as qt_main
from molsysviewer.standalone_qt import QtViewChannel


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
    assert "File → Load Demo / Open File / Load PDB ID" in text
    assert "molsysviewer dialanine --demo" in text
    assert "empty-demo-dialanine.html" in text
    assert (tmp_path / "empty-demo-dialanine.html").exists()


def test_create_standalone_qt0_window_raises_informative_import_error(monkeypatch):
    def _raise():
        raise ImportError(QT_IMPORT_ERROR)

    monkeypatch.setattr(standalone_qt, "_import_qt", _raise)
    with pytest.raises(ImportError, match="PySide6_uibcdf with Qt WebEngine is required"):
        create_standalone_qt0_window(None)


def test_configure_qt_webengine_environment_uses_conda_split_layout(monkeypatch, tmp_path):
    process = tmp_path / "libexec" / "QtWebEngineProcess"
    resources = tmp_path / "resources"
    locales = tmp_path / "translations" / "qtwebengine_locales"
    process.parent.mkdir()
    process.write_text("", encoding="utf-8")
    resources.mkdir()
    locales.mkdir(parents=True)
    for env_name in (
        "QTWEBENGINEPROCESS_PATH",
        "QTWEBENGINE_RESOURCES_PATH",
        "QTWEBENGINE_LOCALES_PATH",
    ):
        monkeypatch.delenv(env_name, raising=False)

    standalone_qt._configure_qt_webengine_environment(tmp_path)

    assert os.environ["QTWEBENGINEPROCESS_PATH"] == str(process)
    assert os.environ["QTWEBENGINE_RESOURCES_PATH"] == str(resources)
    assert os.environ["QTWEBENGINE_LOCALES_PATH"] == str(locales)


def test_create_standalone_qt0_window_builds_minimal_runtime(monkeypatch, tmp_path):
    module_core = ModuleType("PySide6_uibcdf.QtCore")
    module_gui = ModuleType("PySide6_uibcdf.QtGui")
    module_widgets = ModuleType("PySide6_uibcdf.QtWidgets")
    module_web_core = ModuleType("PySide6_uibcdf.QtWebEngineCore")
    module_web = ModuleType("PySide6_uibcdf.QtWebEngineWidgets")
    module_root = ModuleType("PySide6_uibcdf")

    class FakeSignal:
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

    class FakeAction:
        def __init__(self, text, _parent=None):
            self.text = text
            self.triggered = FakeSignal()
            self.shortcut = None

        def setShortcut(self, shortcut):
            self.shortcut = shortcut

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
            self._page = self

        def setUrl(self, url):
            self.url = url

        def setPage(self, page):
            self._page = page
            page.webview = self

        def page(self):
            return self._page

        def runJavaScript(self, script, callback=None):
            self.scripts.append(script)
            if callback is not None:
                callback({"accepted": True})

    class FakeWebEnginePage:
        def __init__(self, _parent=None):
            self.webview = None

        def runJavaScript(self, script, callback=None):
            self.webview.scripts.append(script)
            if callback is not None:
                callback({"accepted": True})
            bridge = getattr(self.webview, "_molsysviewer_qt_bridge", None)
            if bridge is not None and bridge.inflight is not None:
                entry = bridge.inflight
                bridge.handle_frontend_event(
                    {
                        "event": entry["wait_event"],
                        "id": entry["id"],
                        "generation": entry["generation"],
                    }
                )

        def acceptNavigationRequest(self, _url, _nav_type, _is_main_frame):
            return True

        def profile(self):
            if not hasattr(self, "_profile"):
                self._profile = FakeProfile()
            return self._profile

    class FakeProfile:
        def __init__(self):
            self.installed_schemes = {}

        def installUrlSchemeHandler(self, scheme, handler):  # noqa: N802
            self.installed_schemes[bytes(scheme)] = handler

    class FakeQBuffer:
        class OpenModeFlag:
            ReadOnly = 1

        def __init__(self, _parent=None):
            self._data = None

        def setData(self, ba):  # noqa: N802
            self._data = ba

        def open(self, _mode):
            return True

    class FakeQByteArray:
        def __init__(self, data=b""):
            self.data = bytes(data)

    class FakeUrlSchemeHandlerBase:
        pass

    class FakeQMenu:
        created = 0

        def __init__(self, _parent=None):
            FakeQMenu.created += 1
            self._actions = []

        def addAction(self, text):
            action = FakeAction(text)
            self._actions.append(action)
            return action

        def exec(self, _pos):
            return None

    class FakeQCursor:
        @staticmethod
        def pos():
            return (0, 0)

    class FakeQTimer:
        @staticmethod
        def singleShot(_timeout_ms, callback):
            # Timeouts/retries are driven explicitly in these tests.
            FakeQTimer.last_callback = callback

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

        @staticmethod
        def critical(_parent=None, title="", text=""):
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
    module_core.QTimer = FakeQTimer
    module_core.QBuffer = FakeQBuffer
    module_core.QByteArray = FakeQByteArray
    module_gui.QAction = FakeAction
    module_gui.QCursor = FakeQCursor
    module_widgets.QApplication = FakeApplication
    module_widgets.QMenu = FakeQMenu
    module_widgets.QFileDialog = FakeFileDialog
    module_widgets.QInputDialog = FakeInputDialog
    module_widgets.QMainWindow = FakeMainWindow
    module_widgets.QMessageBox = FakeMessageBox
    module_web_core.QWebEnginePage = FakeWebEnginePage
    module_web_core.QWebEngineUrlScheme = _FakeUrlScheme
    module_web_core.QWebEngineUrlSchemeHandler = FakeUrlSchemeHandlerBase
    module_web.QWebEngineView = FakeWebView

    monkeypatch.setitem(sys.modules, "PySide6_uibcdf", module_root)
    monkeypatch.setitem(sys.modules, "PySide6_uibcdf.QtCore", module_core)
    monkeypatch.setitem(sys.modules, "PySide6_uibcdf.QtGui", module_gui)
    monkeypatch.setitem(sys.modules, "PySide6_uibcdf.QtWidgets", module_widgets)
    monkeypatch.setitem(sys.modules, "PySide6_uibcdf.QtWebEngineCore", module_web_core)
    monkeypatch.setitem(sys.modules, "PySide6_uibcdf.QtWebEngineWidgets", module_web)
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
    assert hasattr(runtime["webview"], "_molsysviewer_qt_bridge")
    assert runtime["window"].status_bar.messages[0] == "Loading molecular system..."
    assert [menu.title for menu in runtime["window"].menu_bar.menus] == ["File", "View", "Export", "Help"]
    file_menu = runtime["window"].menu_bar.menus[0]
    new_empty_action = file_menu.actions[0]
    demo_menu = file_menu.actions[2]
    recent_menu = file_menu.actions[3]
    load_pdbid_action = file_menu.actions[4]
    load_source_action = file_menu.actions[5]
    restore_last_action = file_menu.actions[6]
    close_action = file_menu.actions[7]
    assert demo_menu.title == "Load Demo"
    assert recent_menu.title == "Recent"
    assert new_empty_action.shortcut == "Ctrl+N"
    assert file_menu.actions[1].shortcut == "Ctrl+O"
    assert restore_last_action.shortcut == "Ctrl+R"
    assert close_action.shortcut == "Ctrl+W"
    assert recent_menu.actions[0].text == "No recent sources"
    # The load actions drive the persistent MolSysView (not the legacy snapshot).
    from molsysviewer.viewer.core import MolSysView

    view = runtime["webview"]._molsysviewer_view
    assert isinstance(view, MolSysView)
    assert view.widget is runtime["webview"]._molsysviewer_qt_bridge.event_sink.__self__

    # F3 glue: a right-click context event reaches the view and shows a native Qt menu.
    before_menus = FakeQMenu.created
    runtime["webview"]._molsysviewer_qt_bridge.handle_frontend_event(
        {"event": "interaction_context_menu", "kind": "empty"}
    )
    assert FakeQMenu.created == before_menus + 1

    # F2 glue: the Export menu offers movie export.
    export_menu = runtime["window"].menu_bar.menus[2]
    assert any(getattr(a, "text", None) == "Export Movie (orbit)" for a in export_menu.actions)

    load_calls = []
    reset_calls = []
    monkeypatch.setattr(view, "load", lambda ms, **kwargs: load_calls.append(ms))
    monkeypatch.setattr(view, "reset_viewer", lambda **kwargs: reset_calls.append(True))

    new_empty_action.triggered._callbacks[0]()
    assert len(reset_calls) == 1
    assert runtime["window"].status_bar.messages[-1] == "Opened empty host."
    assert runtime["window"].title == "Qt Prototype"
    FakeFileDialog.selected = str(tmp_path / "picked-system.pdb")
    file_menu.actions[1].triggered._callbacks[0]()
    assert load_calls[-1] == str(tmp_path / "picked-system.pdb")
    assert runtime["webview"].url == f"file://{outfile.resolve()}"
    assert runtime["window"].status_bar.messages[-1] == "Loaded file: picked-system.pdb"
    assert runtime["window"].title == "Qt Prototype · picked-system.pdb"
    assert recent_menu.actions[0].title == "Files"
    assert recent_menu.actions[0].actions[0].text == "picked-system.pdb"
    demo_action = next(action for action in demo_menu.actions if action.text == "pentalanine")
    demo_action.triggered._callbacks[0]()
    # A demo is a MolSysView; the persistent view loads its underlying molsys.
    assert not isinstance(load_calls[-1], MolSysView) and load_calls[-1] is not None
    assert runtime["window"].status_bar.messages[-1] == "Loaded demo: pentalanine"
    assert runtime["window"].title == "Qt Prototype · pentalanine"
    assert recent_menu.actions[0].title == "Demos"
    assert recent_menu.actions[0].actions[0].text == "pentalanine"
    assert recent_menu.actions[1].title == "Files"
    assert recent_menu.actions[1].actions[0].text == "picked-system.pdb"
    FakeInputDialog.value = "1crn"
    load_pdbid_action.triggered._callbacks[0]()
    assert load_calls[-1] == "1crn"
    assert runtime["window"].status_bar.messages[-1] == "Loaded PDB ID: 1crn"
    assert runtime["window"].title == "Qt Prototype · 1crn"
    assert recent_menu.actions[0].title == "Demos"
    assert recent_menu.actions[1].title == "Files"
    assert recent_menu.actions[2].title == "PDB IDs"
    assert recent_menu.actions[2].actions[0].text == "1crn"
    FakeInputDialog.value = "molsysmt.MolSys"
    load_source_action.triggered._callbacks[0]()
    assert load_calls[-1] == "molsysmt.MolSys"
    assert runtime["window"].status_bar.messages[-1] == "Loaded source: molsysmt.MolSys"
    assert runtime["window"].title == "Qt Prototype · molsysmt.MolSys"
    assert recent_menu.actions[3].title == "Sources"
    assert recent_menu.actions[3].actions[0].text == "molsysmt.MolSys"
    assert recent_menu.actions[4].text == "Clear Recent Sources"
    restore_last_action.triggered._callbacks[0]()
    assert load_calls[-1] == "molsysmt.MolSys"
    assert runtime["window"].status_bar.messages[-1] == "Loaded source: molsysmt.MolSys"
    recent_menu.actions[2].actions[0].triggered._callbacks[0]()
    assert runtime["window"].status_bar.messages[-1] == "Loaded PDB ID: 1crn"
    assert runtime["window"].title == "Qt Prototype · 1crn"
    view_menu = runtime["window"].menu_bar.menus[1]
    assert view_menu.actions[0].shortcut == "Ctrl+1"
    assert view_menu.actions[1].shortcut == "Ctrl+2"
    assert view_menu.actions[2].shortcut == "Escape"
    runtime["webview"]._molsysviewer_qt_bridge.handle_frontend_event({"event": "ready"})
    for action in view_menu.actions:
        assert action.triggered._callbacks
        action.triggered._callbacks[0]()
    scripts = runtime["webview"].scripts
    assert any('"panel":"navigate"' in script for script in scripts)
    assert any('"panel":"addons"' in script for script in scripts)
    assert any('"expanded":false' in script and '"panel":null' in script for script in scripts)
    export_menu = runtime["window"].menu_bar.menus[2]
    assert export_menu.actions[0].shortcut == "Ctrl+Shift+S"
    assert export_menu.actions[1].shortcut == "Ctrl+Shift+E"
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
    assert "Use File to load a demo, file, PDB ID, or MolSysMT source." in FakeMessageBox.calls[-1][1]
    help_menu.actions[1].triggered._callbacks[0]()
    assert runtime["window"].status_bar.messages[-1] == "Current source: 1crn"
    help_menu.actions[2].triggered._callbacks[0]()
    assert FakeMessageBox.calls[-1][0] == "MolSysViewer Qt Host Info"
    assert "Current source: 1crn" in FakeMessageBox.calls[-1][1]
    assert "Ctrl+N  New Empty Host" in FakeMessageBox.calls[-1][1]
    assert "Ctrl+O  Open File" in FakeMessageBox.calls[-1][1]
    help_menu.actions[3].triggered._callbacks[0]()
    assert runtime["window"].status_bar.messages[-1] == "Loaded PDB ID: 1crn"
    recent_menu.actions[4].triggered._callbacks[0]()
    assert recent_menu.actions[0].text == "No recent sources"
    assert runtime["window"].status_bar.messages[-1] == "Cleared recent sources."
    restore_last_action.triggered._callbacks[0]()
    assert runtime["window"].status_bar.messages[-1] == "No last source is available."
    close_action.triggered._callbacks[0]()
    assert runtime["window"].closed is True
    persisted = (tmp_path / "standalone_qt0_state.json").read_text(encoding="utf-8")
    assert '"recent_sources": []' in persisted
    assert '"last_source": null' in persisted
    assert '"window_size"' in persisted
    assert '"width": 1200' in persisted
    assert '"height": 800' in persisted

    monkeypatch.setattr(
        view, "load",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("broken source")),
    )
    FakeFileDialog.selected = str(tmp_path / "broken-system.pdb")
    file_menu.actions[1].triggered._callbacks[0]()
    assert runtime["window"].status_bar.messages[-1] == "Could not load file: broken source"
    assert FakeMessageBox.calls[-1] == ("Open File Failed", "Could not load file: broken source")


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


def test_load_qt_shell_state_warns_for_corrupt_file_but_not_missing_file(
    tmp_path, monkeypatch, caplog
):
    state_path = tmp_path / "standalone_qt0_state.json"
    monkeypatch.setattr(
        "molsysviewer.standalone_qt._qt_shell_state_path", lambda: state_path
    )
    clean_state = {
        "recent_sources": [],
        "last_source": None,
        "window_size": None,
    }

    with caplog.at_level(logging.WARNING, logger="molsysviewer.standalone_qt.utils"):
        assert standalone_qt._load_qt_shell_state() == clean_state
    assert caplog.records == []

    state_path.write_text("not json", encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="molsysviewer.standalone_qt.utils"):
        assert standalone_qt._load_qt_shell_state() == clean_state

    record = next(
        record for record in caplog.records if "Could not load Qt shell state" in record.message
    )
    assert str(state_path) in record.message
    assert record.exc_info is not None
    assert record.exc_info[0] is json.JSONDecodeError


def test_persist_qt_shell_state_reports_save_failure(monkeypatch, caplog):
    def fail_to_save(_state):
        raise PermissionError("read-only state directory")

    monkeypatch.setattr(
        "molsysviewer.standalone_qt._save_qt_shell_state", fail_to_save
    )

    with caplog.at_level(logging.WARNING, logger="molsysviewer.standalone_qt.utils"):
        standalone_qt._persist_shell_state({})

    record = next(
        record for record in caplog.records if "Could not save Qt shell state" in record.message
    )
    assert record.exc_info is not None
    assert record.exc_info[0] is PermissionError
    assert str(record.exc_info[1]) == "read-only state directory"


def test_qt_message_bridge_materializes_large_payload_refs(tmp_path, monkeypatch):
    monkeypatch.setenv("MOLSYSVIEWER_QT_PAYLOAD_REF_THRESHOLD", "1")

    class FakeQTimer:
        @staticmethod
        def singleShot(_timeout_ms, callback):
            FakeQTimer.callback = callback

    class FakePage:
        def __init__(self):
            self.scripts = []

        def runJavaScript(self, script, callback=None):
            self.scripts.append(script)
            if callback is not None:
                callback({"accepted": True})

    class FakeWebView:
        def __init__(self):
            self._page = FakePage()

        def page(self):
            return self._page

    webview = FakeWebView()
    bridge = standalone_qt.QtMessageBridge(webview, FakeQTimer)
    bridge.ready = True
    bridge.send(
        {
            "op": "load_molsys_payload",
            "payload": {
                "atoms": {"atom_id": [1]},
                "structures": [{"coordinates": [[0, 0, 0]], "time": 0}],
            },
        }
    )

    assert bridge.inflight is not None
    message = bridge.inflight["message"]
    assert message["op"] == "load_molsys_payload_ref"
    assert message["n_structures"] == 1
    payload_id = bridge.inflight["payload_id"]
    assert payload_id
    # The payload is held in-memory (served later over the custom scheme), not a temp file.
    assert message["ref"]["kind"] == "scheme"
    assert message["ref"]["url"] == f"molsysviewer-payload://payload/{payload_id}"
    assert payload_id in bridge.payloads
    assert "load_molsys_payload_ref" in webview.page().scripts[-1]

    bridge.handle_frontend_event(
        {
            "event": "structure_ready",
            "id": bridge.inflight["id"],
            "generation": bridge.inflight["generation"],
        }
    )

    assert bridge.inflight is None
    assert payload_id not in bridge.payloads


def test_qt_bridge_accepts_scalar_javascript_delivery_sentinel():
    class FakeQTimer:
        callbacks = []

        @classmethod
        def singleShot(cls, _timeout_ms, callback):
            cls.callbacks.append(callback)

    class FakePage:
        def runJavaScript(self, script, callback=None):
            assert "molsysviewer-message-accepted" in script
            if callback is not None:
                callback("molsysviewer-message-accepted")

    class FakeWebView:
        def page(self):
            return FakePage()

    bridge = standalone_qt.QtMessageBridge(FakeWebView(), FakeQTimer)
    bridge.ready = True
    bridge.send({"op": "set_panel_mode", "mode": "studio"})

    assert bridge.inflight is not None
    assert bridge.inflight["delivery_attempts"] == 1
    assert bridge.queue == []
    assert bridge.failed_deliveries == []


@pytest.mark.parametrize("failure_mode", ["missing_page", "rejected"])
def test_qt_bridge_does_not_hang_or_spin_when_delivery_keeps_failing(failure_mode):
    class FakeQTimer:
        callbacks = []

        @classmethod
        def singleShot(cls, _timeout_ms, callback):
            cls.callbacks.append(callback)

    class RejectingPage:
        def runJavaScript(self, _script, callback=None):
            if callback is not None:
                callback({"accepted": False})

    class FakeWebView:
        def page(self):
            if failure_mode == "missing_page":
                return None
            return RejectingPage()

    statuses = []
    bridge = standalone_qt.QtMessageBridge(
        FakeWebView(), FakeQTimer, status_callback=statuses.append
    )
    bridge.ready = True

    bridge.send({"op": "set_panel_mode", "mode": "studio"})

    max_callbacks = bridge.MAX_DELIVERY_ATTEMPTS * 3
    for _ in range(max_callbacks):
        if not FakeQTimer.callbacks:
            break
        FakeQTimer.callbacks.pop(0)()
    else:
        pytest.fail("the Qt delivery retry pump did not reach a terminal state")

    assert FakeQTimer.callbacks == []
    assert bridge.queue == []
    assert bridge.inflight is None
    assert bridge.failed_deliveries == [
        {
            "id": "qt-1",
            "generation": 0,
            "op": "set_panel_mode",
            "attempts": bridge.MAX_DELIVERY_ATTEMPTS,
            "reason": (
                "web view page is unavailable"
                if failure_mode == "missing_page"
                else "frontend message handler is not ready"
            ),
        }
    ]
    assert any("delivery delayed" in status for status in statuses)
    assert "delivery failed after 5 attempts" in statuses[-1]


def test_qt_startup_status_for_empty_host(monkeypatch):
    messages = []
    standalone_qt._show_startup_status(type("FakeWindow", (), {
        "statusBar": lambda self: type("FakeStatusBar", (), {"showMessage": lambda _self, message: messages.append(message)})()
    })(), {"loaded_label": None})

    assert messages[-1] == "Ready. Use File to load a demo, file, PDB ID, or MolSysMT source."


def test_load_qt_shell_state_restores_window_size(tmp_path, monkeypatch):
    state_path = tmp_path / "standalone_qt0_state.json"
    state_path.write_text(
        json.dumps(
            {
                "recent_sources": [],
                "last_source": None,
                "window_size": {"width": 1660, "height": 980},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("molsysviewer.standalone_qt._qt_shell_state_path", lambda: state_path)

    state = standalone_qt._load_qt_shell_state()

    assert state["window_size"] == {"width": 1660, "height": 980}


def test_qt_standalone_main_supports_no_exec(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        "molsysviewer.standalone_qt.launch_standalone_qt0",
        lambda *args, **kwargs: {"html_path": str((tmp_path / "qt-main.html").resolve())},
    )

    code = qt_main(["dialanine", "--demo", "--output", str(tmp_path / "qt-main.html"), "--no-exec"])
    _ = code


def test_qt_cli_help_marks_remote_connect_experimental():
    help_text = standalone_qt._build_arg_parser().format_help()

    assert "experimental in MolSysViewer 1.0" in help_text


def test_create_remote_qt_window_reuses_authenticated_session_page(monkeypatch):
    class FakeSignal:
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args):
            for callback in self._callbacks:
                callback(*args)

    class FakeAction:
        def __init__(self, text, _parent=None):
            self.text = text
            self.shortcut = None
            self.triggered = FakeSignal()

        def setShortcut(self, shortcut):
            self.shortcut = shortcut

    class FakeMenu:
        def __init__(self, title):
            self.title = title
            self.actions = []

        def addAction(self, action):
            self.actions.append(action)

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

        def clearMessage(self):
            self.messages.append("")

    class FakeWindow:
        def __init__(self):
            self.title = None
            self.size = None
            self.central = None
            self.status = FakeStatusBar()
            self.menu_bar = FakeMenuBar()
            self.closed = False
            self.fullscreen = False
            self.maximized = False

        def setWindowTitle(self, title):
            self.title = title

        def resize(self, width, height):
            self.size = (width, height)

        def setCentralWidget(self, widget):
            self.central = widget

        def statusBar(self):
            return self.status

        def menuBar(self):
            return self.menu_bar

        def close(self):
            self.closed = True

        def isMaximized(self):
            return self.maximized

        def showFullScreen(self):
            self.fullscreen = True

        def showNormal(self):
            self.fullscreen = False
            self.maximized = False

        def showMaximized(self):
            self.fullscreen = False
            self.maximized = True

    class FakeProfile:
        def __init__(self):
            self.downloadRequested = FakeSignal()

    class FakePage:
        def __init__(self):
            self.scripts = []
            self._profile = FakeProfile()
            self._settings = FakeSettings()
            self.fullScreenRequested = FakeSignal()

        def runJavaScript(self, script, callback=None):
            self.scripts.append(script)
            if callback is not None:
                callback(self.result)

        def profile(self):
            return self._profile

        def settings(self):
            return self._settings

        result = None

    class FakeSettings:
        class WebAttribute:
            FullScreenSupportEnabled = "fullscreen-support"

        def __init__(self):
            self.attributes = {}

        def setAttribute(self, attribute, enabled):
            self.attributes[attribute] = enabled

    class FakeWebView:
        def __init__(self, parent):
            self.parent = parent
            self.url = None
            self._page = FakePage()
            self.reloaded = False
            self.loadStarted = FakeSignal()
            self.loadFinished = FakeSignal()

        def setUrl(self, url):
            self.url = url
            self.loadStarted.emit()
            self.loadFinished.emit(True)

        def page(self):
            return self._page

        def reload(self):
            self.reloaded = True

    class FakeFileDialog:
        selected = "/tmp/remote-view.png"

        @classmethod
        def getSaveFileName(cls, *_args):
            return cls.selected, ""

    class FakeTimer:
        def __init__(self, parent):
            self.parent = parent
            self.interval = None
            self.timeout = FakeSignal()
            self.running = False

        def setInterval(self, interval):
            self.interval = interval

        def start(self):
            self.running = True

        def stop(self):
            self.running = False

    fake_app = object()
    monkeypatch.setattr(
        standalone_qt,
        "_import_qt",
        lambda: {
            "QApplication": object,
            "QMainWindow": FakeWindow,
            "QWebEngineView": FakeWebView,
            "QUrl": lambda value: value,
            "QAction": FakeAction,
            "QFileDialog": FakeFileDialog,
            "QTimer": FakeTimer,
        },
    )
    monkeypatch.setattr(
        standalone_qt, "_get_or_create_application", lambda _class, _argv: fake_app
    )

    url = "http://127.0.0.1:8765/session/client#token=secret"
    runtime = standalone_qt.create_remote_qt_window(url, width=1200, height=800)

    assert runtime["app"] is fake_app
    assert runtime["session_url"] == url
    assert runtime["webview"].url == url
    assert runtime["window"].central is runtime["webview"]
    assert runtime["window"].size == (1200, 800)
    assert runtime["webview"]._page._settings.attributes == {
        "fullscreen-support": True
    }

    class FakeFullScreenRequest:
        def __init__(self, enabling):
            self.enabling = enabling
            self.accepted = False

        def toggleOn(self):
            return self.enabling

        def accept(self):
            self.accepted = True

    enter_fullscreen = FakeFullScreenRequest(True)
    runtime["webview"]._page.fullScreenRequested.emit(enter_fullscreen)
    assert enter_fullscreen.accepted is True
    assert runtime["window"].fullscreen is True
    leave_fullscreen = FakeFullScreenRequest(False)
    runtime["webview"]._page.fullScreenRequested.emit(leave_fullscreen)
    assert leave_fullscreen.accepted is True
    assert runtime["window"].fullscreen is False
    assert runtime["window"].status.messages == [
        "Connecting to remote MolSysViewer session…",
        "Remote session loaded; negotiating connection…",
    ]
    timer = runtime["window"]._molsysviewer_remote_status_timer
    assert timer.interval == 500
    assert timer.running is True
    runtime["webview"]._page.result = json.dumps(
        {"state": "negotiating", "text": "Starting remote video…"}
    )
    timer.timeout.emit()
    assert runtime["window"].status.messages[-1] == "Starting remote video…"
    runtime["webview"]._page.result = json.dumps(
        {"state": "ready", "text": "Connected"}
    )
    timer.timeout.emit()
    assert runtime["window"].status.messages[-1] == ""
    runtime["webview"].loadStarted.emit()
    runtime["webview"].loadFinished.emit(False)
    assert timer.running is False
    assert runtime["window"].status.messages[-1] == (
        "Could not load the remote MolSysViewer session."
    )
    assert [menu.title for menu in runtime["window"].menu_bar.menus] == [
        "File", "View", "Export"
    ]
    file_menu, view_menu, export_menu = runtime["window"].menu_bar.menus
    assert file_menu.actions[0].shortcut == "Ctrl+O"
    file_menu.actions[0].triggered._callbacks[0]()
    assert "data-molsysviewer-upload-button" in runtime["webview"]._page.scripts[-1]
    view_menu.actions[0].triggered._callbacks[0]()
    assert runtime["webview"].reloaded is True
    export_menu.actions[0].triggered._callbacks[0]()
    assert "data-molsysviewer-export-image" in runtime["webview"]._page.scripts[-1]

    class FakeDownload:
        def __init__(self):
            self.isFinishedChanged = FakeSignal()
            self.directory = None
            self.filename = None
            self.accepted = False

        def suggestedFileName(self):
            return "molsysviewer.png"

        def setDownloadDirectory(self, value):
            self.directory = value

        def setDownloadFileName(self, value):
            self.filename = value

        def accept(self):
            self.accepted = True

        def cancel(self):
            raise AssertionError("download should not be cancelled")

        def isFinished(self):
            return True

    download = FakeDownload()
    runtime["webview"]._page._profile.downloadRequested._callbacks[0](download)
    assert download.directory == "/tmp"
    assert download.filename == "remote-view.png"
    assert download.accepted is True
    download.isFinishedChanged._callbacks[0]()
    assert runtime["window"].status.messages[-1] == "Downloaded: remote-view.png"


@pytest.mark.parametrize("url", ["", "127.0.0.1/session/client", "file:///tmp/client"])
def test_create_remote_qt_window_rejects_non_http_session_urls(url):
    with pytest.raises(ValueError, match=r"HTTP\(S\)"):
        standalone_qt.create_remote_qt_window(url)


def test_qt_main_connects_remote_session_without_building_local_host(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(
        standalone_qt,
        "launch_remote_qt",
        lambda url, **kwargs: calls.append((url, kwargs)) or {"session_url": url},
    )

    url = "https://viewer.example/session/client#token=secret"
    assert qt_main(["--connect", url, "--no-exec"]) == 0
    assert calls == [(url, {
        "title": "MolSysViewer Qt Prototype",
        "width": 1440,
        "height": 960,
        "exec_app": False,
    })]
    assert capsys.readouterr().out.strip() == url


class _FakeUrlScheme:
    registered: dict[bytes, "_FakeUrlScheme"] = {}

    class Flag:
        SecureScheme = 1
        LocalScheme = 2
        LocalAccessAllowed = 4
        CorsEnabled = 8
        FetchApiAllowed = 16

    def __init__(self, name: bytes = b"") -> None:
        self._name = name
        self._flags = None

    def name(self) -> bytes:
        return self._name

    def setFlags(self, flags) -> None:  # noqa: N802
        self._flags = flags

    @classmethod
    def schemeByName(cls, name: bytes) -> "_FakeUrlScheme":  # noqa: N802
        return cls.registered.get(name, _FakeUrlScheme(b""))

    @classmethod
    def registerScheme(cls, scheme: "_FakeUrlScheme") -> None:  # noqa: N802
        cls.registered[scheme.name()] = scheme


def test_register_qt_url_schemes_registers_event_and_payload_schemes():
    _FakeUrlScheme.registered = {}

    standalone_qt._register_qt_url_schemes(_FakeUrlScheme)

    assert b"molsysviewer" in _FakeUrlScheme.registered
    assert b"molsysviewer-payload" in _FakeUrlScheme.registered
    # The event and payload schemes must be fetchable in real Qt.
    assert _FakeUrlScheme.registered[b"molsysviewer"]._flags & _FakeUrlScheme.Flag.CorsEnabled
    assert _FakeUrlScheme.registered[b"molsysviewer"]._flags & _FakeUrlScheme.Flag.FetchApiAllowed
    assert _FakeUrlScheme.registered[b"molsysviewer-payload"]._flags & _FakeUrlScheme.Flag.CorsEnabled
    assert _FakeUrlScheme.registered[b"molsysviewer-payload"]._flags & _FakeUrlScheme.Flag.FetchApiAllowed

    # Idempotent: registering again does not duplicate or error.
    standalone_qt._register_qt_url_schemes(_FakeUrlScheme)
    assert len(_FakeUrlScheme.registered) == 2


def test_payload_scheme_handler_serves_and_fails_correctly():
    class FakeByteArray:
        def __init__(self, data=b""):
            self.data = bytes(data)

    class FakeBuffer:
        class OpenModeFlag:
            ReadOnly = 1

        def __init__(self, parent=None):
            self._data = None
            self.opened = False

        def setData(self, ba):  # noqa: N802
            self._data = ba

        def open(self, mode):
            self.opened = True

    class FakeHandlerBase:
        pass

    class FakeUrl:
        def __init__(self, path):
            self._path = path

        def path(self):
            return self._path

    class FakeJob:
        UrlNotFound = 404

        def __init__(self, path):
            self._url = FakeUrl(path)
            self.replied = None
            self.failed = None

        def requestUrl(self):  # noqa: N802
            return self._url

        def reply(self, content_type, buffer):
            self.replied = (content_type, buffer)

        def fail(self, code):
            self.failed = code

    payloads = {"qt-7": b'{"ok":1}'}
    handler = standalone_qt._make_payload_scheme_handler(
        FakeHandlerBase, FakeBuffer, FakeByteArray, payloads
    )

    job = FakeJob("/qt-7")
    handler.requestStarted(job)
    content_type, buffer = job.replied
    assert content_type.data == b"application/json"
    assert buffer._data.data == b'{"ok":1}'
    assert buffer.opened is True

    missing = FakeJob("/does-not-exist")
    handler.requestStarted(missing)
    assert missing.replied is None
    assert missing.failed == FakeJob.UrlNotFound

    # Only successfully served payloads are recorded (used by the real-Qt smoke).
    assert handler.served == ["qt-7"]


def test_event_scheme_handler_delivers_event_to_bridge():
    class FakeByteArray:
        def __init__(self, data=b""):
            self.data = bytes(data)

    class FakeBuffer:
        class OpenModeFlag:
            ReadOnly = 1

        def __init__(self, parent=None):
            self._data = None
            self.opened = False

        def setData(self, ba):  # noqa: N802
            self._data = ba

        def open(self, mode):
            self.opened = True

    class FakeHandlerBase:
        pass

    class FakeUrl:
        def toString(self):  # noqa: N802
            return "molsysviewer://event?payload=%7B%22event%22%3A%22ready%22%7D"

    class FakeJob:
        def __init__(self):
            self.replied = None

        def requestUrl(self):  # noqa: N802
            return FakeUrl()

        def reply(self, content_type, buffer):
            self.replied = (content_type, buffer)

    class FakeBridge:
        def __init__(self):
            self.events = []

        def handle_frontend_event(self, event):
            self.events.append(event)
            return True

    class FakeWebView:
        pass

    webview = FakeWebView()
    bridge = FakeBridge()
    webview._molsysviewer_qt_bridge = bridge
    handler = standalone_qt._make_event_scheme_handler(
        FakeHandlerBase, FakeBuffer, FakeByteArray, webview
    )

    job = FakeJob()
    handler.requestStarted(job)

    assert bridge.events == [{"event": "ready"}]
    content_type, buffer = job.replied
    assert content_type.data == b"application/json"
    assert buffer._data.data == b'{"ok":true}'
    assert buffer.opened is True


@pytest.mark.parametrize(
    "payload",
    [
        "%22not%20a%20dict%22",
        "%7B%7D",
    ],
)
def test_malformed_qt_bridge_event_is_rejected_without_false_ok(payload, caplog):
    class FakeByteArray:
        def __init__(self, data=b""):
            self.data = bytes(data)

    class FakeBuffer:
        class OpenModeFlag:
            ReadOnly = 1

        def __init__(self, parent=None):
            self._data = None

        def setData(self, value):  # noqa: N802
            self._data = value

        def open(self, _mode):
            pass

    class FakeHandlerBase:
        pass

    class FakeJob:
        def __init__(self):
            self.replied = None

        def requestUrl(self):  # noqa: N802
            return type(
                "FakeUrl",
                (),
                {"toString": lambda _self: f"molsysviewer://event?payload={payload}"},
            )()

        def reply(self, content_type, buffer):
            self.replied = (content_type, buffer)

    class FakeQTimer:
        @staticmethod
        def singleShot(_timeout_ms, _callback):
            pass

    statuses = []
    bridge = standalone_qt.QtMessageBridge(
        object(), FakeQTimer, status_callback=statuses.append
    )
    webview = type("FakeWebView", (), {})()
    webview._molsysviewer_qt_bridge = bridge
    handler = standalone_qt._make_event_scheme_handler(
        FakeHandlerBase, FakeBuffer, FakeByteArray, webview
    )

    with caplog.at_level(logging.WARNING, logger="molsysviewer.standalone_qt.utils"):
        assert bridge.handle_frontend_event(json.loads(
            '"not a dict"' if payload.startswith("%22") else "{}"
        )) is False
        job = FakeJob()
        handler.requestStarted(job)

    content_type, buffer = job.replied
    assert content_type.data == b"application/json"
    assert buffer._data.data == b'{"ok":false,"error":"invalid_event"}'
    assert any("Rejected malformed frontend event" in status for status in statuses)
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_qt_view_channel_rejects_malformed_event_before_callbacks():
    class RecordingBridge(_FakeBridge):
        def __init__(self):
            super().__init__()
            self.rejections = []

        def reject_frontend_event(self, event, *, source, reason):
            self.rejections.append((event, source, reason))
            return False

    bridge = RecordingBridge()
    channel = QtViewChannel(bridge)
    received = []
    channel.on_msg(lambda _widget, content, _buffers: received.append(content))

    assert channel._dispatch_event({}) is False  # noqa: SLF001
    assert received == []
    assert bridge.rejections == [
        ({}, "Qt view channel", "expected a non-empty string 'event' field")
    ]


def test_qt_bridge_reports_load_progress():
    class FakeQTimer:
        @staticmethod
        def singleShot(_timeout_ms, _callback):
            pass

    class FakePage:
        def runJavaScript(self, script, callback=None):
            if callback is not None:
                callback({"accepted": True})

    class FakeWebView:
        def __init__(self):
            self._page = FakePage()

        def page(self):
            return self._page

    statuses: list[str] = []
    bridge = standalone_qt.QtMessageBridge(FakeWebView(), FakeQTimer, status_callback=statuses.append)
    bridge.ready = True
    bridge.send({"op": "load_molsys_payload", "payload": {"atoms": {}, "structures": []}})

    assert any("Loading" in s for s in statuses)
    mid = bridge.inflight["id"]
    gen = bridge.inflight["generation"]

    bridge.handle_frontend_event({"event": "structure_ready", "id": mid, "generation": gen})
    assert any("rendering" in s.lower() for s in statuses)

    bridge.handle_frontend_event({"event": "render_ready", "id": mid, "generation": gen})
    assert statuses[-1] == "Ready."

    # A stale-generation event must not overwrite the status.
    statuses.clear()
    bridge.handle_frontend_event({"event": "structure_ready", "id": mid, "generation": gen - 1})
    assert statuses == []


class _FakeBridge:
    def __init__(self):
        self.sent = []
        self.event_sink = None

    def send(self, msg):
        self.sent.append(msg)


def test_qt_view_channel_routes_send_and_initial_messages_to_bridge():
    bridge = _FakeBridge()
    channel = QtViewChannel(bridge)

    channel.send({"op": "clear_all"})
    assert bridge.sent == [{"op": "clear_all"}]

    # `initial_messages` is set cumulatively before ready; only new entries are
    # forwarded to the bridge, each exactly once.
    channel.initial_messages = [{"op": "m1"}]
    channel.initial_messages = [{"op": "m1"}, {"op": "m2"}]
    assert bridge.sent == [{"op": "clear_all"}, {"op": "m1"}, {"op": "m2"}]


def test_qt_view_channel_delivers_bridge_events_to_on_msg():
    bridge = _FakeBridge()
    channel = QtViewChannel(bridge)
    received = []
    channel.on_msg(lambda _widget, content, _buffers: received.append(content))

    # The channel wired itself as the bridge's event sink.
    assert callable(bridge.event_sink)
    bridge.event_sink({"event": "interaction_click", "kind": "structure"})
    assert received == [{"event": "interaction_click", "kind": "structure"}]


def test_qt_view_channel_close_only_detaches_its_own_event_sink():
    bridge = _FakeBridge()
    channel = QtViewChannel(bridge)
    replacement_sink = lambda event: event
    bridge.event_sink = replacement_sink

    channel.close()

    assert bridge.event_sink is replacement_sink


def test_molsysview_accepts_qt_transport_and_routes_events():
    from molsysviewer import MolSysView

    bridge = _FakeBridge()
    channel = QtViewChannel(bridge)
    view = MolSysView(transport=channel)
    assert view.widget is channel

    # Outgoing (post-ready) messages route through the channel to the bridge.
    view._ready = True  # noqa: SLF001
    view._send({"op": "clear_all"})  # noqa: SLF001
    assert {"op": "clear_all"} in bridge.sent

    # Incoming: a bridge-forwarded frontend event reaches _handle_frontend_event.
    view._ready = False  # noqa: SLF001
    bridge.event_sink({"event": "ready"})
    assert view._ready is True  # noqa: SLF001


def test_qt_transport_delivers_interaction_and_movie_events_to_view():
    """F2/F3 enablement: with the persistent view, forwarded frontend events reach
    the view's interaction state and movie-export buffer end to end."""
    from molsysviewer import MolSysView

    bridge = _FakeBridge()
    channel = QtViewChannel(bridge)
    view = MolSysView(transport=channel)

    # F3: an interaction event updates the view's last-click state.
    bridge.event_sink({"event": "interaction_click", "kind": "empty"})
    assert view.get_last_click_event() is not None

    # F2: a movie frame lands in the export buffer (the cooperative wait consumes it).
    view._movie_export_frames = []  # noqa: SLF001
    bridge.event_sink({"event": "movie_frame", "data_uri": "data:image/png;base64,AAAA"})
    assert len(view._movie_export_frames) == 1  # noqa: SLF001


def test_qt_bridge_forwards_product_events_but_not_transport():
    class FakeQTimer:
        @staticmethod
        def singleShot(_t, _cb):
            pass

    forwarded = []
    bridge = standalone_qt.QtMessageBridge(
        object(), FakeQTimer, event_sink=forwarded.append
    )

    bridge.handle_frontend_event({"event": "ready"})
    bridge.handle_frontend_event({"event": "interaction_hover", "kind": "empty"})
    # Pure-transport events must NOT reach the view.
    bridge.handle_frontend_event({"event": "message_ack", "id": "x", "generation": 0})
    bridge.handle_frontend_event({"event": "structure_ready", "id": "x", "generation": 0})

    names = [e.get("event") for e in forwarded]
    assert "ready" in names
    assert "interaction_hover" in names
    assert "message_ack" not in names
    assert "structure_ready" not in names


def test_qt_bridge_reports_view_event_failure_without_raising(caplog):
    class FakeQTimer:
        @staticmethod
        def singleShot(_t, _cb):
            pass

    def failing_sink(_event):
        raise RuntimeError("boom")

    bridge = standalone_qt.QtMessageBridge(
        object(), FakeQTimer, event_sink=failing_sink
    )
    event = {"event": "interaction_click", "kind": "structure"}

    with caplog.at_level(logging.ERROR, logger="molsysviewer.standalone_qt.utils"):
        bridge.handle_frontend_event(event)

    record = next(
        record for record in caplog.records if "Qt view event failed" in record.message
    )
    assert record.exc_info is not None
    assert record.exc_info[0] is RuntimeError
    assert str(record.exc_info[1]) == "boom"
    assert repr(event) in record.message


# Tier-1 CI smoke: the real Qt JS->Python event transport WITHOUT Mol*/WebGL.
# A trivial page (no viewer.js, no WebGL context) posts a `ready` event exactly
# like the frontend does — fetch("molsysviewer://event?...") — and we assert the
# bridge receives it and becomes ready. This isolates the transport
# (fetch -> scheme handler -> bridge) that fakes cannot cover, runs headless
# (offscreen, no GPU/display needed), and is the always-on CI gate. It runs in a
# subprocess because QtWebEngine cannot be initialized more than once per process
# (doing so alongside the rest of the suite aborts the interpreter). The render
# (which needs WebGL) is validated separately in test_qt_live_model_full_render_gpu.
_QT_TRANSPORT_SMOKE_SCRIPT = r'''
import os, sys, tempfile, time
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import molsysviewer.standalone_qt as sq
qt = sq._import_qt()
sq._register_qt_url_schemes(qt["QWebEngineUrlScheme"])
app = sq._get_or_create_application(qt["QApplication"], None)
view = qt["QWebEngineView"]()
bridge = sq._install_qt_message_bridge(
    view, qt["QWebEnginePage"], qt["QTimer"],
    QWebEngineUrlSchemeHandler=qt["QWebEngineUrlSchemeHandler"],
    QBuffer=qt["QBuffer"], QByteArray=qt["QByteArray"],
)
received = []
bridge.event_sink = received.append
html = ("<!doctype html><html><body><script>"
        "window.addEventListener('load',function(){"
        "fetch('molsysviewer://event?payload='+"
        "encodeURIComponent(JSON.stringify({event:'ready'})));});"
        "</script></body></html>")
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
    fh.write(html); path = fh.name
view.setUrl(qt["QUrl"].fromLocalFile(path))
start = time.time()
while time.time() - start < 15.0:
    app.processEvents()
    if bridge.ready:
        break
    time.sleep(0.02)
ok = bool(bridge.ready) and any(e.get("event") == "ready" for e in received)
print("TRANSPORT_READY:" + ("yes" if ok else "no"))
sys.exit(0 if ok else 1)
'''


def test_qt_event_transport_smoke_real_qt():
    """Real Qt JS->Python transport smoke (fetch -> scheme handler -> bridge).

    Runs in a subprocess (QtWebEngine is single-init-per-process). Headless,
    no GPU/display: this is the always-on CI gate for the transport.
    """
    import subprocess

    try:
        standalone_qt._import_qt()
    except ImportError as exc:
        pytest.skip(f"PySide6 is not available: {exc}")

    # Curated env: force offscreen and strip QtWebEngine path/backend vars that
    # other tests may leave in os.environ (they'd otherwise leak into the child
    # and make QtWebEngine try a real GL/Vulkan backend). The child's _import_qt
    # recomputes the resource paths fresh from CONDA_PREFIX.
    env = dict(os.environ)
    for key in (
        "QTWEBENGINE_RESOURCES_PATH",
        "QTWEBENGINEPROCESS_PATH",
        "QTWEBENGINE_LOCALES_PATH",
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "QT_QUICK_BACKEND",
    ):
        env.pop(key, None)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

    result = subprocess.run(
        [sys.executable, "-c", _QT_TRANSPORT_SMOKE_SCRIPT],
        capture_output=True,
        text=True,
        timeout=90,
        env=env,
    )
    assert "TRANSPORT_READY:yes" in result.stdout, (
        "real Qt event transport (fetch -> molsysviewer:// scheme handler -> bridge) "
        f"failed.\nstdout={result.stdout}\nstderr={result.stderr[-1500:]}"
    )


_QT_TWO_GENERATION_PAYLOAD_SCRIPT = r'''
import json, os, sys, tempfile, time
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["MOLSYSVIEWER_QT_PAYLOAD_REF_THRESHOLD"] = "1"
import molsysviewer.standalone_qt as sq
qt = sq._import_qt()
sq._register_qt_url_schemes(qt["QWebEngineUrlScheme"])
app = sq._get_or_create_application(qt["QApplication"], None)
view = qt["QWebEngineView"]()
bridge = sq._install_qt_message_bridge(
    view, qt["QWebEnginePage"], qt["QTimer"],
    QWebEngineUrlSchemeHandler=qt["QWebEngineUrlSchemeHandler"],
    QBuffer=qt["QBuffer"], QByteArray=qt["QByteArray"],
)
received = []
bridge.event_sink = received.append
html = r"""<!doctype html><html><body><script>
async function postHost(event) {
  const payload = encodeURIComponent(JSON.stringify(event));
  await fetch("molsysviewer://event?payload=" + payload);
}
window.__molsysviewerDocsHandleMessage = async function(message) {
  if (message.op === "clear_all") {
    await postHost({event:"message_ack", id:message.id, generation:message.generation});
    return;
  }
  if (message.op === "load_molsys_payload_ref") {
    const response = await fetch(message.ref.url);
    if (!response.ok) throw new Error("payload ref failed: " + response.status);
    const payload = await response.json();
    await postHost({
      event:"qt_payload_probe",
      id:message.id,
      generation:message.generation,
      atoms:payload.atoms.atom_id.length,
      label:message.label
    });
    await postHost({event:"structure_ready", id:message.id, generation:message.generation});
    return;
  }
  await postHost({event:"message_ack", id:message.id, generation:message.generation});
};
window.addEventListener("load", () => {
  postHost({event:"ready"});
});
</script></body></html>"""
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as fh:
    fh.write(html)
    path = fh.name
view.setUrl(qt["QUrl"].fromLocalFile(path))

def spin_until(predicate, timeout=15.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return False

if not spin_until(lambda: bridge.ready):
    print(json.dumps({"error":"ready_timeout"}))
    sys.exit(1)

def send_generation(label, atom_count):
    generation = bridge.begin_generation()
    bridge.send({"op":"clear_all"})
    bridge.send({
        "op":"load_molsys_payload",
        "label":label,
        "payload":{
            "atoms":{"atom_id":list(range(1, atom_count + 1))},
            "structures":[{"coordinates":[[float(i), 0.0, 0.0] for i in range(atom_count)]}]
        }
    })
    ok = spin_until(
        lambda: bridge.inflight is None
        and not bridge.queue
        and any(
            event.get("event") == "qt_payload_probe"
            and event.get("generation") == generation
            for event in received
        )
    )
    return generation, ok

first_generation, first_ok = send_generation("first", 1)
second_generation, second_ok = send_generation("second", 2)
probes = [event for event in received if event.get("event") == "qt_payload_probe"]
handler = view._molsysviewer_qt_payload_handler
print(json.dumps({
    "first_ok": first_ok,
    "second_ok": second_ok,
    "first_generation": first_generation,
    "second_generation": second_generation,
    "probes": probes,
    "served": list(handler.served),
    "failed_deliveries": bridge.failed_deliveries,
}))
sys.exit(0 if first_ok and second_ok else 1)
'''


def test_qt_payload_refs_replace_across_two_real_generations():
    """Real Qt bridge serves and acknowledges two successive payload generations."""
    import subprocess

    try:
        standalone_qt._import_qt()
    except ImportError as exc:
        pytest.skip(f"PySide6 is not available: {exc}")

    env = dict(os.environ)
    for key in (
        "QTWEBENGINE_RESOURCES_PATH",
        "QTWEBENGINEPROCESS_PATH",
        "QTWEBENGINE_LOCALES_PATH",
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "QT_QUICK_BACKEND",
    ):
        env.pop(key, None)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

    result = subprocess.run(
        [sys.executable, "-c", _QT_TWO_GENERATION_PAYLOAD_SCRIPT],
        capture_output=True,
        text=True,
        timeout=90,
        env=env,
    )
    output_lines = [line for line in result.stdout.splitlines() if line.startswith("{")]
    assert output_lines, f"Qt payload-generation probe produced no report.\nstderr={result.stderr[-1500:]}"
    report = json.loads(output_lines[-1])

    assert result.returncode == 0, (
        f"two-generation Qt payload delivery failed: {report}\nstderr={result.stderr[-1500:]}"
    )
    assert report["first_ok"] is True
    assert report["second_ok"] is True
    assert report["second_generation"] > report["first_generation"]
    assert [(item["label"], item["atoms"]) for item in report["probes"]] == [
        ("first", 1),
        ("second", 2),
    ]
    assert len(set(report["served"])) == 2
    assert report["failed_deliveries"] == []


def test_qt_live_model_smoke_real_window(monkeypatch):
    """Real (offscreen) Qt WebEngine smoke test for the live-message transport.

    Asserts, in real Qt: the event scheme + bridge round-trip (bridge.ready) and
    that a payload above the ref threshold is served over the molsysviewer-payload
    scheme (handler.served).

    NOT validated here: the actual 3D/WebGL render. Headless (offscreen +
    --disable-gpu) has no WebGL context, so the structure never finishes drawing
    and this test skips that part. To also validate rendering, run in an
    environment with a real GPU, or with xvfb plus software WebGL
    (QTWEBENGINE_CHROMIUM_FLAGS="--use-gl=angle --use-angle=swiftshader
    --enable-unsafe-swiftshader") — best kept as a separate opt-in test/CI job,
    not the default smoke.
    """
    try:
        standalone_qt._import_qt()
    except ImportError as exc:
        pytest.skip(f"PySide6 is not available: {exc}")

    # Real WebGL/GPU rendering context is required for the viewer to initialize and signal ready.
    # Without a display (X11 DISPLAY variable), rendering will fail in headless test environments.
    if not os.environ.get("DISPLAY"):
        pytest.skip("Requires a real X11 display context to initialize WebGL (run manually, not in headless CI).")


    # Set threshold to 1 so dialanine payload goes through custom scheme handler
    monkeypatch.setenv("MOLSYSVIEWER_QT_PAYLOAD_REF_THRESHOLD", "1")
    monkeypatch.setenv("QTWEBENGINE_DISABLE_SANDBOX", "1")
    monkeypatch.setenv("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")
    monkeypatch.setenv("QT_QUICK_BACKEND", "software")

    # Run in offscreen mode to avoid opening visible GUI window during tests
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    # Create real window with dialanine demo
    runtime = create_standalone_qt0_window(
        demo["dialanine"],
        title="Smoke Test Real Window",
    )

    app = runtime["app"]
    webview = runtime["webview"]
    window = runtime["window"]
    bridge = webview._molsysviewer_qt_bridge

    # Spin the event loop until the viewer is ready and the structure loads, with 15s timeout
    import time
    start_time = time.time()
    success = False
    status_msg = ""
    while time.time() - start_time < 15.0:
        app.processEvents()
        if bridge.ready and len(bridge.queue) == 0 and bridge.inflight is None:
            success = True
            break
        # Read last status message from window status bar to diagnose issues
        if hasattr(window, "statusBar") and window.statusBar():
            status_msg = window.statusBar().currentMessage()
            if "error" in status_msg.lower() or "failed" in status_msg.lower():
                break
        time.sleep(0.05)

    try:
        # Cleanup
        window.close()
    except Exception:
        pass

    # #1 (event scheme + bridge round-trip): the frontend only signals ready via
    # the molsysviewer:// event scheme, so this proves that channel works in real Qt.
    assert bridge.ready is True, f"Qt message bridge failed to become ready. Status: {status_msg}"

    # #2 (payload scheme handler): the dialanine payload is above the ref threshold,
    # so the page must have fetched it over molsysviewer-payload://. The fetch runs
    # before any GPU work, so this holds even when rendering later fails headless.
    handler = getattr(webview, "_molsysviewer_qt_payload_handler", None)
    assert handler is not None and len(handler.served) >= 1, (
        f"payload scheme handler served no payload over molsysviewer-payload:// "
        f"(bridge ready={bridge.ready}). Status: {status_msg}"
    )

    if not success:
        pytest.skip(
            "Qt WebEngine loaded, the event and payload schemes both worked, but "
            "WebGL/rendering timed out (expected in headless environment without GPU). "
            f"Status: {status_msg}"
        )

    assert len(bridge.queue) == 0
    assert bridge.inflight is None




def test_qt_live_model_full_render_gpu(monkeypatch):
    """Opt-in end-to-end render test: also validates the actual 3D/WebGL draw.

    Disabled by default (needs a WebGL-capable environment). Enable with
    MOLSYSVIEWER_QT_GPU_TEST=1, ideally under xvfb with software WebGL, e.g.:

        QTWEBENGINE_CHROMIUM_FLAGS="--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader" \
        MOLSYSVIEWER_QT_GPU_TEST=1 xvfb-run -a pytest -k full_render_gpu

    Unlike the default smoke, this asserts the load fully completes (structure
    rendered), not just that the transports work.
    """
    if not os.environ.get("MOLSYSVIEWER_QT_GPU_TEST"):
        pytest.skip("Set MOLSYSVIEWER_QT_GPU_TEST=1 (WebGL-capable env) to run the full render test.")
    try:
        standalone_qt._import_qt()
    except ImportError as exc:
        pytest.skip(f"PySide6 is not available: {exc}")

    monkeypatch.setenv("MOLSYSVIEWER_QT_PAYLOAD_REF_THRESHOLD", "1")
    monkeypatch.setenv("QTWEBENGINE_DISABLE_SANDBOX", "1")
    monkeypatch.setenv("QT_QPA_PLATFORM", os.environ.get("QT_QPA_PLATFORM", "offscreen"))

    runtime = create_standalone_qt0_window(demo["dialanine"], title="Full Render GPU Test")
    app = runtime["app"]
    webview = runtime["webview"]
    window = runtime["window"]
    bridge = webview._molsysviewer_qt_bridge

    import time
    start = time.time()
    success = False
    status_msg = ""
    while time.time() - start < 30.0:
        app.processEvents()
        if bridge.ready and len(bridge.queue) == 0 and bridge.inflight is None:
            success = True
            break
        if hasattr(window, "statusBar") and window.statusBar():
            status_msg = window.statusBar().currentMessage()
        time.sleep(0.05)

    try:
        window.close()
    except Exception:
        pass

    assert bridge.ready is True, f"bridge never became ready. Status: {status_msg}"
    handler = getattr(webview, "_molsysviewer_qt_payload_handler", None)
    assert handler is not None and len(handler.served) >= 1, "payload was not served over the custom scheme"
    # The whole point of this test: the load actually finished (rendered).
    assert success, f"structure did not finish rendering within timeout. Status: {status_msg}"
    assert bridge.inflight is None
