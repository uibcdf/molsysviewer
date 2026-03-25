from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Sequence

from .demo import demo
from .standalone import _resolve_view, build_standalone0_html


QT_IMPORT_ERROR = (
    "PySide6 with Qt WebEngine is required for the standalone Qt prototype. "
    "Install `pyside6` and ensure `PySide6.QtWebEngineWidgets` is available. "
    "If the conda-forge build does not expose that module in your environment, "
    "install the matching PyPI addons package, for example "
    "`pip install PySide6-Addons==<your-pyside6-version>`."
)

QT_STATE_FILENAME = "standalone_qt0_state.json"


def _import_qt():
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QAction
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMainWindow, QMessageBox
    except Exception as exc:  # pragma: no cover - exercised by contract test
        raise ImportError(QT_IMPORT_ERROR) from exc

    return {
        "QAction": QAction,
        "QApplication": QApplication,
        "QFileDialog": QFileDialog,
        "QInputDialog": QInputDialog,
        "QMainWindow": QMainWindow,
        "QMessageBox": QMessageBox,
        "QUrl": QUrl,
        "QWebEngineView": QWebEngineView,
    }


def _get_or_create_application(QApplication, argv: Sequence[str] | None = None):
    app = QApplication.instance()
    if app is not None:
        return app
    return QApplication(list(argv or []))


def _qt_shell_state_path() -> Path:
    return Path.home() / ".molsysviewer" / QT_STATE_FILENAME


def _load_qt_shell_state() -> dict[str, Any]:
    path = _qt_shell_state_path()
    if not path.exists():
        return {"recent_sources": [], "last_source": None, "window_size": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"recent_sources": [], "last_source": None, "window_size": None}
    if not isinstance(data, dict):
        return {"recent_sources": [], "last_source": None, "window_size": None}
    recent_sources = data.get("recent_sources", [])
    if not isinstance(recent_sources, list):
        recent_sources = []
    last_source = data.get("last_source")
    if not isinstance(last_source, dict):
        last_source = None
    window_size = data.get("window_size")
    if (
        not isinstance(window_size, dict)
        or not isinstance(window_size.get("width"), int)
        or not isinstance(window_size.get("height"), int)
    ):
        window_size = None
    return {"recent_sources": recent_sources[:5], "last_source": last_source, "window_size": window_size}


def _save_qt_shell_state(current_state: dict[str, Any]) -> None:
    path = _qt_shell_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "recent_sources": current_state.get("recent_sources", [])[:5],
        "last_source": current_state.get("last_source"),
        "window_size": current_state.get("window_size"),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _capture_window_size(window) -> dict[str, int] | None:
    width = None
    height = None
    if hasattr(window, "width") and callable(window.width):
        try:
            width = int(window.width())
        except Exception:
            width = None
    if hasattr(window, "height") and callable(window.height):
        try:
            height = int(window.height())
        except Exception:
            height = None
    size = getattr(window, "size", None)
    if (width is None or height is None) and isinstance(size, tuple) and len(size) == 2:
        if width is None and isinstance(size[0], int):
            width = size[0]
        if height is None and isinstance(size[1], int):
            height = size[1]
    if not isinstance(width, int) or not isinstance(height, int):
        return None
    return {"width": width, "height": height}


def _show_status(window, message: str) -> None:
    if hasattr(window, "statusBar"):
        status_bar = window.statusBar()
        if status_bar is not None and hasattr(status_bar, "showMessage"):
            status_bar.showMessage(message)


def _reload_html_in_view(webview, QUrl, html_path: str) -> None:
    webview.setUrl(QUrl.fromLocalFile(html_path))


def _window_title(base_title: str, loaded_label: str | None = None) -> str:
    if not loaded_label:
        return base_title
    return f"{base_title} · {loaded_label}"


def _set_loaded_state(window, current_state: dict[str, Any], molecular_system: Any, loaded_label: str) -> None:
    current_state["molecular_system"] = molecular_system
    current_state["loaded_label"] = loaded_label
    if hasattr(window, "setWindowTitle"):
        window.setWindowTitle(_window_title(current_state["base_title"], loaded_label))


def _record_recent_source(
    current_state: dict[str, Any],
    *,
    kind: str,
    value: Any,
    loaded_label: str,
) -> None:
    recent = current_state.setdefault("recent_sources", [])
    entry = {"kind": kind, "value": value, "loaded_label": loaded_label}
    recent[:] = [item for item in recent if not (item["kind"] == kind and item["loaded_label"] == loaded_label)]
    recent.insert(0, entry)
    del recent[5:]
    current_state["last_source"] = entry


def _recent_section_title(kind: str) -> str:
    return {
        "demo": "Demos",
        "file": "Files",
        "pdb_id": "PDB IDs",
        "source": "Sources",
    }.get(kind, "Other")


def _persist_shell_state(current_state: dict[str, Any], window=None) -> None:
    if window is not None:
        window_size = _capture_window_size(window)
        if window_size is not None:
            current_state["window_size"] = window_size
    try:
        _save_qt_shell_state(current_state)
    except Exception:
        return


def _send_viewer_message(webview, message: dict[str, Any]) -> None:
    page = webview.page() if hasattr(webview, "page") else None
    if page is None or not hasattr(page, "runJavaScript"):
        return
    payload = json.dumps(message, separators=(",", ":"))
    script = (
        "if (window.__molsysviewerDocsHandleMessage) { "
        f"window.__molsysviewerDocsHandleMessage({payload}); "
        "}"
    )
    page.runJavaScript(script)


def _qt_runtime_urls() -> list[str]:
    local_runtime = Path(__file__).with_name("viewer.js").resolve().as_uri()
    return [
        local_runtime,
        "https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer/dist/viewer.js",
    ]


def _rebuild_qt_html(
    molecular_system: Any,
    *,
    html_path: str,
    title: str,
) -> str:
    return build_standalone0_html(
        molecular_system,
        html_path,
        title=title,
        include_popout=False,
        prepare_addons=False,
        mode="lite",
        runtime_urls=_qt_runtime_urls(),
    )


def _export_qt_figure(
    molecular_system: Any,
    *,
    output_filename: str,
    title: str,
) -> str:
    view = _resolve_view(molecular_system)
    view.export.figure(
        output_filename,
        skip_digestion=True,
    )
    return output_filename


def _load_demo_into_qt_host(
    demo_name: str,
    *,
    window,
    webview,
    QUrl,
    html_path: str,
    current_title: str,
    current_state: dict[str, Any],
) -> None:
    _rebuild_qt_html(
        demo[demo_name],
        html_path=html_path,
        title=current_title,
    )
    _set_loaded_state(window, current_state, demo[demo_name], demo_name)
    _record_recent_source(
        current_state,
        kind="demo",
        value=demo_name,
        loaded_label=demo_name,
    )
    _persist_shell_state(current_state, window=window)
    _reload_html_in_view(webview, QUrl, html_path)
    _show_status(window, f"Loaded demo: {demo_name}")


def _load_recent_source(
    recent_entry: dict[str, Any],
    *,
    window,
    webview,
    QUrl,
    html_path: str,
    current_title: str,
    current_state: dict[str, Any],
) -> None:
    kind = recent_entry["kind"]
    value = recent_entry["value"]
    loaded_label = recent_entry["loaded_label"]
    if kind == "demo":
        _load_demo_into_qt_host(
            str(value),
            window=window,
            webview=webview,
            QUrl=QUrl,
            html_path=html_path,
            current_title=current_title,
            current_state=current_state,
        )
        return
    _rebuild_qt_html(
        value,
        html_path=html_path,
        title=current_title,
    )
    _set_loaded_state(window, current_state, value, loaded_label)
    _record_recent_source(
        current_state,
        kind=kind,
        value=value,
        loaded_label=loaded_label,
    )
    _persist_shell_state(current_state, window=window)
    _reload_html_in_view(webview, QUrl, html_path)
    if kind == "pdb_id":
        _show_status(window, f"Loaded PDB ID: {loaded_label}")
    elif kind == "source":
        _show_status(window, f"Loaded source: {loaded_label}")
    else:
        _show_status(window, f"Loaded file: {loaded_label}")


def _restore_last_source(
    *,
    window,
    webview,
    QUrl,
    html_path: str,
    current_title: str,
    current_state: dict[str, Any],
) -> None:
    recent_entry = current_state.get("last_source")
    if not isinstance(recent_entry, dict):
        recent_sources = current_state.get("recent_sources", [])
        recent_entry = recent_sources[0] if recent_sources else None
    if not isinstance(recent_entry, dict):
        _show_status(window, "No last source is available.")
        return
    _load_recent_source(
        recent_entry,
        window=window,
        webview=webview,
        QUrl=QUrl,
        html_path=html_path,
        current_title=current_title,
        current_state=current_state,
    )


def _install_menu_bar(
    *,
    window,
    webview,
    QUrl,
    QAction,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    html_path: str,
    current_title: str,
    current_state: dict[str, Any],
) -> None:
    menu_bar = window.menuBar()

    file_menu = menu_bar.addMenu("File")
    view_menu = menu_bar.addMenu("View")
    export_menu = menu_bar.addMenu("Export")
    help_menu = menu_bar.addMenu("Help")

    open_file_action = QAction("Open File", window)

    def _open_file():
        if not hasattr(QFileDialog, "getOpenFileName"):
            _show_status(window, "Open File is not available in the current Qt runtime.")
            return
        selected, _filter = QFileDialog.getOpenFileName(
            window,
            "Open molecular system",
            "",
            "Molecular systems (*);;All files (*)",
        )
        if not selected:
            return
        _rebuild_qt_html(
            selected,
            html_path=html_path,
            title=current_title,
        )
        _set_loaded_state(window, current_state, selected, Path(selected).name)
        _record_recent_source(
            current_state,
            kind="file",
            value=selected,
            loaded_label=Path(selected).name,
        )
        _persist_shell_state(current_state, window=window)
        _reload_html_in_view(webview, QUrl, html_path)
        _refresh_recent_menu()
        _show_status(window, f"Loaded file: {Path(selected).name}")

    open_file_action.triggered.connect(_open_file)
    file_menu.addAction(open_file_action)

    demo_menu = file_menu.addMenu("Load Demo")
    recent_menu = file_menu.addMenu("Recent")

    def _refresh_recent_menu() -> None:
        if hasattr(recent_menu, "clear"):
            recent_menu.clear()
        elif isinstance(getattr(recent_menu, "actions", None), list):
            recent_menu.actions.clear()
        recent_sources = current_state.get("recent_sources", [])
        if not recent_sources:
            empty_action = QAction("No recent sources", window)
            recent_menu.addAction(empty_action)
            return
        kind_order = ("demo", "file", "pdb_id", "source")
        grouped_sources: dict[str, list[dict[str, Any]]] = {kind: [] for kind in kind_order}
        for recent_entry in recent_sources:
            kind = str(recent_entry.get("kind", "other"))
            grouped_sources.setdefault(kind, []).append(recent_entry)
        for kind in kind_order:
            entries = grouped_sources.get(kind, [])
            if not entries:
                continue
            target_menu = recent_menu.addMenu(_recent_section_title(kind))
            for recent_entry in entries:
                recent_action = QAction(recent_entry["loaded_label"], window)
                recent_action.triggered.connect(
                    lambda _checked=False, entry=recent_entry: _load_recent_source(
                        entry,
                        window=window,
                        webview=webview,
                        QUrl=QUrl,
                        html_path=html_path,
                        current_title=current_title,
                        current_state=current_state,
                    )
                )
                target_menu.addAction(recent_action)
        extra_kinds = [kind for kind in grouped_sources.keys() if kind not in kind_order]
        for kind in sorted(extra_kinds):
            entries = grouped_sources[kind]
            if not entries:
                continue
            target_menu = recent_menu.addMenu(_recent_section_title(kind))
            for recent_entry in entries:
                recent_action = QAction(recent_entry["loaded_label"], window)
                recent_action.triggered.connect(
                    lambda _checked=False, entry=recent_entry: _load_recent_source(
                        entry,
                        window=window,
                        webview=webview,
                        QUrl=QUrl,
                        html_path=html_path,
                        current_title=current_title,
                        current_state=current_state,
                    )
                )
                target_menu.addAction(recent_action)
    for demo_name in sorted(demo.keys()):
        demo_action = QAction(demo_name, window)
        demo_action.triggered.connect(
            lambda _checked=False, name=demo_name: (
                _load_demo_into_qt_host(
                    name,
                    window=window,
                    webview=webview,
                    QUrl=QUrl,
                    html_path=html_path,
                    current_title=current_title,
                    current_state=current_state,
                ),
                _refresh_recent_menu(),
            )
        )
        demo_menu.addAction(demo_action)

    _refresh_recent_menu()

    load_pdbid_action = QAction("Load PDB ID", window)

    def _load_pdbid():
        if not hasattr(QInputDialog, "getText"):
            _show_status(window, "Load PDB ID is not available in the current Qt runtime.")
            return
        value, accepted = QInputDialog.getText(
            window,
            "Load PDB ID",
            "PDB ID:",
        )
        pdb_id = str(value).strip()
        if not accepted or not pdb_id:
            return
        _rebuild_qt_html(
            pdb_id,
            html_path=html_path,
            title=current_title,
        )
        _set_loaded_state(window, current_state, pdb_id, pdb_id)
        _record_recent_source(
            current_state,
            kind="pdb_id",
            value=pdb_id,
            loaded_label=pdb_id,
        )
        _reload_html_in_view(webview, QUrl, html_path)
        _refresh_recent_menu()
        _show_status(window, f"Loaded PDB ID: {pdb_id}")

    load_pdbid_action.triggered.connect(_load_pdbid)
    file_menu.addAction(load_pdbid_action)

    load_source_action = QAction("Load Source", window)

    def _load_source():
        if not hasattr(QInputDialog, "getText"):
            _show_status(window, "Load Source is not available in the current Qt runtime.")
            return
        value, accepted = QInputDialog.getText(
            window,
            "Load MolSysMT Source",
            "Source:",
        )
        source_value = str(value).strip()
        if not accepted or not source_value:
            return
        _rebuild_qt_html(
            source_value,
            html_path=html_path,
            title=current_title,
        )
        _set_loaded_state(window, current_state, source_value, source_value)
        _record_recent_source(
            current_state,
            kind="source",
            value=source_value,
            loaded_label=source_value,
        )
        _persist_shell_state(current_state, window=window)
        _reload_html_in_view(webview, QUrl, html_path)
        _refresh_recent_menu()
        _show_status(window, f"Loaded source: {source_value}")

    load_source_action.triggered.connect(_load_source)
    file_menu.addAction(load_source_action)

    restore_last_action = QAction("Restore Last Source", window)

    def _restore_last():
        _restore_last_source(
            window=window,
            webview=webview,
            QUrl=QUrl,
            html_path=html_path,
            current_title=current_title,
            current_state=current_state,
        )
        _refresh_recent_menu()

    restore_last_action.triggered.connect(_restore_last)
    file_menu.addAction(restore_last_action)

    close_action = QAction("Close", window)
    close_action.triggered.connect(lambda: (_persist_shell_state(current_state, window=window), window.close()))
    file_menu.addAction(close_action)

    open_navigate_action = QAction("Open Navigate", window)
    open_navigate_action.triggered.connect(
        lambda: _send_viewer_message(
            webview,
            {"op": "set_panel_mode", "panel": "navigate", "expanded": True},
        )
    )
    view_menu.addAction(open_navigate_action)

    open_workbench_action = QAction("Open Workbench", window)
    open_workbench_action.triggered.connect(
        lambda: _send_viewer_message(
            webview,
            {"op": "set_panel_mode", "panel": "workbench", "expanded": True},
        )
    )
    view_menu.addAction(open_workbench_action)

    close_panel_action = QAction("Close Panel Mode", window)
    close_panel_action.triggered.connect(
        lambda: _send_viewer_message(
            webview,
            {"op": "set_panel_mode", "panel": None, "expanded": False},
        )
    )
    view_menu.addAction(close_panel_action)

    export_html_action = QAction("Export HTML", window)

    def _export_html():
        if not hasattr(QFileDialog, "getSaveFileName"):
            _show_status(window, "Export HTML is not available in the current Qt runtime.")
            return
        selected, _filter = QFileDialog.getSaveFileName(
            window,
            "Export MolSysViewer HTML",
            str(Path(html_path).with_name("molsysviewer-export.html")),
            "HTML files (*.html);;All files (*)",
        )
        if not selected:
            return
        destination = Path(selected).expanduser().resolve()
        shutil.copyfile(html_path, destination)
        _show_status(window, f"Exported HTML: {destination.name}")

    export_html_action.triggered.connect(_export_html)
    export_menu.addAction(export_html_action)

    export_figure_action = QAction("Export Figure", window)

    def _export_figure():
        if current_state.get("molecular_system") is None:
            _show_status(window, "No molecular system is loaded for figure export.")
            return
        if not hasattr(QFileDialog, "getSaveFileName"):
            _show_status(window, "Export Figure is not available in the current Qt runtime.")
            return
        selected, _filter = QFileDialog.getSaveFileName(
            window,
            "Export MolSysViewer figure",
            str(Path(html_path).with_name("molsysviewer-figure.png")),
            "PNG files (*.png);;All files (*)",
        )
        if not selected:
            return
        destination = Path(selected).expanduser().resolve()
        _export_qt_figure(
            current_state["molecular_system"],
            output_filename=str(destination),
            title=current_title,
        )
        _show_status(window, f"Exported Figure: {destination.name}")

    export_figure_action.triggered.connect(_export_figure)
    export_menu.addAction(export_figure_action)

    about_action = QAction("About MolSysViewer Qt Prototype", window)

    def _show_about() -> None:
        message = (
            "MolSysViewer Qt Prototype\n\n"
            "Thin standalone host for the shared MolSysViewer runtime.\n"
            "Current goal: validate the dedicated app shell before final packaging."
        )
        if hasattr(QMessageBox, "information"):
            QMessageBox.information(window, "About MolSysViewer Qt Prototype", message)
        else:
            _show_status(window, "About: MolSysViewer Qt Prototype")

    about_action.triggered.connect(_show_about)
    help_menu.addAction(about_action)

    current_source_action = QAction("Show Current Source", window)

    def _show_current_source() -> None:
        loaded_label = current_state.get("loaded_label")
        if not loaded_label:
            _show_status(window, "No molecular system is currently loaded.")
            return
        _show_status(window, f"Current source: {loaded_label}")

    current_source_action.triggered.connect(_show_current_source)
    help_menu.addAction(current_source_action)

    reload_last_action = QAction("Reload Last Source", window)

    def _reload_last_source() -> None:
        _restore_last_source(
            window=window,
            webview=webview,
            QUrl=QUrl,
            html_path=html_path,
            current_title=current_title,
            current_state=current_state,
        )
        _refresh_recent_menu()

    reload_last_action.triggered.connect(_reload_last_source)
    help_menu.addAction(reload_last_action)


def create_standalone_qt0_window(
    molecular_system: Any,
    output_filename: str | None = None,
    *,
    title: str = "MolSysViewer Qt Prototype",
    selection: str | Sequence[int] = "all",
    structure_indices: str | Sequence[int] = "all",
    syntax: str = "MolSysMT",
    load_mode: str = "selection",
    include_controls: bool = True,
    include_popout: bool = False,
    discover_addons: bool = False,
    addon_modules: Sequence[str] | None = None,
    apply_project_config: bool = True,
    debug_js: bool | None = None,
    app_argv: Sequence[str] | None = None,
    width: int = 1440,
    height: int = 960,
) -> dict[str, Any]:
    qt = _import_qt()
    QApplication = qt["QApplication"]
    QMainWindow = qt["QMainWindow"]
    QWebEngineView = qt["QWebEngineView"]
    QUrl = qt["QUrl"]
    QAction = qt["QAction"]
    QFileDialog = qt["QFileDialog"]
    QInputDialog = qt["QInputDialog"]
    QMessageBox = qt["QMessageBox"]

    if output_filename is None:
        with tempfile.NamedTemporaryFile(prefix="molsysviewer-qt0-", suffix=".html", delete=False) as handle:
            output_filename = handle.name

    html_path = build_standalone0_html(
        molecular_system,
        output_filename,
        title=title,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        load_mode=load_mode,
        include_controls=include_controls,
        include_popout=include_popout,
        discover_addons=discover_addons,
        addon_modules=addon_modules,
        apply_project_config=apply_project_config,
        debug_js=debug_js,
        mode="lite",
        runtime_urls=_qt_runtime_urls(),
    )

    current_state = {"molecular_system": molecular_system, "base_title": title, "loaded_label": None}
    current_state.update(_load_qt_shell_state())

    app = _get_or_create_application(QApplication, app_argv)
    window = QMainWindow()
    window.setWindowTitle(title)
    saved_window_size = current_state.get("window_size") if isinstance(current_state.get("window_size"), dict) else None
    initial_width = saved_window_size.get("width", width) if saved_window_size else width
    initial_height = saved_window_size.get("height", height) if saved_window_size else height
    if hasattr(window, "resize"):
        window.resize(initial_width, initial_height)

    webview = QWebEngineView(window)
    webview.setUrl(QUrl.fromLocalFile(html_path))
    window.setCentralWidget(webview)
    _install_menu_bar(
        window=window,
        webview=webview,
        QUrl=QUrl,
        QAction=QAction,
        QFileDialog=QFileDialog,
        QInputDialog=QInputDialog,
        QMessageBox=QMessageBox,
        html_path=html_path,
        current_title=title,
        current_state=current_state,
    )

    return {
        "app": app,
        "window": window,
        "webview": webview,
        "html_path": html_path,
        "title": title,
    }


def launch_standalone_qt0(
    molecular_system: Any,
    output_filename: str | None = None,
    *,
    title: str = "MolSysViewer Qt Prototype",
    selection: str | Sequence[int] = "all",
    structure_indices: str | Sequence[int] = "all",
    syntax: str = "MolSysMT",
    load_mode: str = "selection",
    include_controls: bool = True,
    include_popout: bool = False,
    discover_addons: bool = False,
    addon_modules: Sequence[str] | None = None,
    apply_project_config: bool = True,
    debug_js: bool | None = None,
    app_argv: Sequence[str] | None = None,
    width: int = 1440,
    height: int = 960,
    exec_app: bool = True,
) -> dict[str, Any]:
    runtime = create_standalone_qt0_window(
        molecular_system,
        output_filename=output_filename,
        title=title,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        load_mode=load_mode,
        include_controls=include_controls,
        include_popout=include_popout,
        discover_addons=discover_addons,
        addon_modules=addon_modules,
        apply_project_config=apply_project_config,
        debug_js=debug_js,
        app_argv=app_argv,
        width=width,
        height=height,
    )
    runtime["window"].show()
    runtime["exit_code"] = runtime["app"].exec() if exec_app else None
    return runtime


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the first MolSysViewer Qt standalone prototype.")
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to a molecular system or a demo key when using --demo. If omitted, launch an empty host.",
    )
    parser.add_argument("--demo", action="store_true", help="Interpret source as a MolSysViewer demo key.")
    parser.add_argument("--output", default=None, help="Output HTML file. Defaults to a temporary file.")
    parser.add_argument("--title", default="MolSysViewer Qt Prototype", help="Window title.")
    parser.add_argument("--selection", default="all", help="Selection passed to new_view(...).")
    parser.add_argument("--structure-indices", default="all", help="Structure indices passed to new_view(...).")
    parser.add_argument("--syntax", default="MolSysMT", help="Selection syntax.")
    parser.add_argument("--load-mode", default="selection", choices=("selection", "all"), help="Load mode.")
    parser.add_argument("--discover-addons", action="store_true", help="Discover known add-ons before launch.")
    parser.add_argument(
        "--addon-module",
        action="append",
        default=[],
        help="Explicit add-on module(s) to register, e.g. molsysviewer_topomt.",
    )
    parser.add_argument("--width", type=int, default=1440, help="Initial window width.")
    parser.add_argument("--height", type=int, default=960, help="Initial window height.")
    parser.add_argument(
        "--no-exec",
        action="store_true",
        help="Build the Qt window and HTML without entering the Qt event loop.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    source: Any
    if args.source is None:
        source = None
    else:
        source = demo[args.source] if args.demo else args.source

    runtime = launch_standalone_qt0(
        source,
        output_filename=args.output,
        title=args.title,
        selection=args.selection,
        structure_indices=args.structure_indices,
        syntax=args.syntax,
        load_mode=args.load_mode,
        discover_addons=args.discover_addons,
        addon_modules=args.addon_module,
        width=args.width,
        height=args.height,
        exec_app=not args.no_exec,
    )
    print(runtime["html_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
