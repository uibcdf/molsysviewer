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


def _import_qt():
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QAction
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMainWindow
    except Exception as exc:  # pragma: no cover - exercised by contract test
        raise ImportError(QT_IMPORT_ERROR) from exc

    return {
        "QAction": QAction,
        "QApplication": QApplication,
        "QFileDialog": QFileDialog,
        "QInputDialog": QInputDialog,
        "QMainWindow": QMainWindow,
        "QUrl": QUrl,
        "QWebEngineView": QWebEngineView,
    }


def _get_or_create_application(QApplication, argv: Sequence[str] | None = None):
    app = QApplication.instance()
    if app is not None:
        return app
    return QApplication(list(argv or []))


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
    _reload_html_in_view(webview, QUrl, html_path)
    _show_status(window, f"Loaded demo: {demo_name}")


def _install_menu_bar(
    *,
    window,
    webview,
    QUrl,
    QAction,
    QFileDialog,
    QInputDialog,
    html_path: str,
    current_title: str,
    current_state: dict[str, Any],
) -> None:
    menu_bar = window.menuBar()

    file_menu = menu_bar.addMenu("File")
    view_menu = menu_bar.addMenu("View")
    export_menu = menu_bar.addMenu("Export")

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
        _reload_html_in_view(webview, QUrl, html_path)
        _show_status(window, f"Loaded file: {Path(selected).name}")

    open_file_action.triggered.connect(_open_file)
    file_menu.addAction(open_file_action)

    load_demo_action = QAction("Load Demo", window)

    def _load_demo():
        if not hasattr(QInputDialog, "getItem"):
            _show_status(window, "Load Demo is not available in the current Qt runtime.")
            return
        demo_names = sorted(demo.keys())
        selected, accepted = QInputDialog.getItem(
            window,
            "Load Demo",
            "Demo:",
            demo_names,
            0,
            False,
        )
        demo_name = str(selected).strip()
        if not accepted or not demo_name:
            return
        if demo_name not in demo:
            _show_status(window, f"Unknown demo: {demo_name}")
            return
        _load_demo_into_qt_host(
            demo_name,
            window=window,
            webview=webview,
            QUrl=QUrl,
            html_path=html_path,
            current_title=current_title,
            current_state=current_state,
        )

    load_demo_action.triggered.connect(_load_demo)
    file_menu.addAction(load_demo_action)

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
        _reload_html_in_view(webview, QUrl, html_path)
        _show_status(window, f"Loaded PDB ID: {pdb_id}")

    load_pdbid_action.triggered.connect(_load_pdbid)
    file_menu.addAction(load_pdbid_action)

    close_action = QAction("Close", window)
    close_action.triggered.connect(window.close)
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

    app = _get_or_create_application(QApplication, app_argv)
    window = QMainWindow()
    window.setWindowTitle(title)
    if hasattr(window, "resize"):
        window.resize(width, height)

    webview = QWebEngineView(window)
    webview.setUrl(QUrl.fromLocalFile(html_path))
    window.setCentralWidget(webview)
    current_state = {"molecular_system": molecular_system, "base_title": title, "loaded_label": None}
    _install_menu_bar(
        window=window,
        webview=webview,
        QUrl=QUrl,
        QAction=QAction,
        QFileDialog=QFileDialog,
        QInputDialog=QInputDialog,
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
