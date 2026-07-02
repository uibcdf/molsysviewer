from __future__ import annotations

import sys
import tempfile
from typing import Any, Sequence

from ..standalone import build_standalone0_html
from .utils import (
    _import_qt,
    _get_or_create_application,
    _load_qt_shell_state,
    _show_startup_status,
    _qt_runtime_urls,
    _install_qt_message_bridge,
    _load_molecular_system_into_qt_host,
)
from .menus import _install_menu_bar


def _get_helper(name: str) -> Any:
    m = sys.modules.get("molsysviewer.standalone_qt")
    if m is not None and hasattr(m, name):
        return getattr(m, name)
    return globals()[name]


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
    qt = _get_helper("_import_qt")()
    QApplication = qt["QApplication"]
    QMainWindow = qt["QMainWindow"]
    QWebEngineView = qt["QWebEngineView"]
    QUrl = qt["QUrl"]
    QAction = qt["QAction"]
    QFileDialog = qt["QFileDialog"]
    QInputDialog = qt["QInputDialog"]
    QMessageBox = qt["QMessageBox"]
    QTimer = qt["QTimer"]
    QWebEnginePage = qt["QWebEnginePage"]
    QWebEngineUrlScheme = qt["QWebEngineUrlScheme"]
    QWebEngineUrlSchemeHandler = qt["QWebEngineUrlSchemeHandler"]
    QBuffer = qt["QBuffer"]
    QByteArray = qt["QByteArray"]

    # Must run before the QApplication is created, or Chromium rejects the schemes.
    _get_helper("_register_qt_url_schemes")(QWebEngineUrlScheme)

    if output_filename is None:
        with tempfile.NamedTemporaryFile(prefix="molsysviewer-qt0-", suffix=".html", delete=False) as handle:
            output_filename = handle.name

    html_path = build_standalone0_html(
        None,
        output_filename,
        title=title,
        include_controls=include_controls,
        include_popout=include_popout,
        discover_addons=discover_addons,
        addon_modules=addon_modules,
        apply_project_config=apply_project_config,
        debug_js=debug_js,
        mode="lite",
        runtime_urls=_get_helper("_qt_runtime_urls")(),
        host_event_transport="url-scheme",
        show_empty_host_overlay=False,
    )

    current_state = {"molecular_system": molecular_system, "base_title": title, "loaded_label": None}
    current_state.update(_get_helper("_load_qt_shell_state")())

    app = _get_helper("_get_or_create_application")(QApplication, app_argv)
    window = QMainWindow()
    window.setWindowTitle(title)
    saved_window_size = current_state.get("window_size") if isinstance(current_state.get("window_size"), dict) else None
    initial_width = saved_window_size.get("width", width) if saved_window_size else width
    initial_height = saved_window_size.get("height", height) if saved_window_size else height
    if hasattr(window, "resize"):
        window.resize(initial_width, initial_height)

    webview = QWebEngineView(window)
    _get_helper("_install_qt_message_bridge")(
        webview,
        QWebEnginePage,
        QTimer,
        status_callback=lambda message: window.statusBar().showMessage(message),
        QWebEngineUrlSchemeHandler=QWebEngineUrlSchemeHandler,
        QBuffer=QBuffer,
        QByteArray=QByteArray,
    )
    webview.setUrl(QUrl.fromLocalFile(html_path))
    window.setCentralWidget(webview)
    _get_helper("_install_menu_bar")(
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
    if molecular_system is None:
        _get_helper("_show_startup_status")(window, current_state)
    else:
        _get_helper("_load_molecular_system_into_qt_host")(
            molecular_system,
            window=window,
            webview=webview,
            current_state=current_state,
            loaded_label=None,
            status_message="Loading molecular system...",
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            load_mode=load_mode,
            debug_js=debug_js,
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
    m = sys.modules.get("molsysviewer.standalone_qt")
    create_func = getattr(m, "create_standalone_qt0_window", create_standalone_qt0_window) if m else create_standalone_qt0_window
    runtime = create_func(
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
