from __future__ import annotations

import sys
import tempfile
import json
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit

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


def _run_remote_page_action(
    webview: Any, selector: str, callback=None, *, reveal_selector: str | None = None
) -> None:
    """Activate one stable control in the shared authenticated session page."""
    target = json.dumps(selector)
    reveal = json.dumps(reveal_selector) if reveal_selector else "null"
    script = f"""(() => {{
        const activate = () => {{
            const element = document.querySelector({target});
            if (!element) return false;
            element.click();
            return true;
        }};
        if (activate()) return true;
        const reveal = {reveal};
        if (!reveal) return false;
        const control = document.querySelector(reveal);
        if (!control) return false;
        control.click();
        window.setTimeout(activate, 100);
        return true;
    }})()"""
    webview.page().runJavaScript(script, callback)


def _install_remote_qt_chrome(
    *, window: Any, webview: Any, QAction: Any, QFileDialog: Any
) -> None:
    """Install native menus and download handling around the shared web client."""
    menu_bar = window.menuBar()
    file_menu = menu_bar.addMenu("File")
    view_menu = menu_bar.addMenu("View")
    export_menu = menu_bar.addMenu("Export")

    def add_action(menu, label: str, callback, shortcut: str | None = None):
        action = QAction(label, window)
        if shortcut and hasattr(action, "setShortcut"):
            action.setShortcut(shortcut)
        action.triggered.connect(callback)
        menu.addAction(action)
        return action

    def page_action(
        selector: str, missing_message: str, *, reveal_selector: str | None = None
    ):
        return lambda *_: _run_remote_page_action(
            webview,
            selector,
            lambda found: None
            if found
            else window.statusBar().showMessage(missing_message),
            reveal_selector=reveal_selector,
        )

    add_action(
        file_menu,
        "Open Molecular File…",
        page_action(
            '[data-molsysviewer-upload-button="true"]',
            "The remote session has no upload control.",
        ),
        "Ctrl+O",
    )
    add_action(file_menu, "Close", lambda *_: window.close(), "Ctrl+W")
    add_action(view_menu, "Reload Session", lambda *_: webview.reload(), "Ctrl+R")
    add_action(
        export_menu,
        "Download PNG Image",
        page_action(
            '[data-molsysviewer-export-image="true"]',
            "The remote session has no PNG export control.",
            reveal_selector='[data-molsysviewer-group-panel-tab="export"]',
        ),
        "Ctrl+Shift+E",
    )
    add_action(
        export_menu,
        "Download Standalone HTML View",
        page_action(
            '[data-molsysviewer-export-html="true"]',
            "The remote session has no HTML export control.",
            reveal_selector='[data-molsysviewer-group-panel-tab="export"]',
        ),
        "Ctrl+Shift+S",
    )

    page = webview.page()
    profile = page.profile()
    active_downloads: list[Any] = []
    window._molsysviewer_remote_downloads = active_downloads

    def handle_download(download: Any) -> None:
        suggested = Path(str(download.suggestedFileName() or "molsysviewer-download")).name
        selected, _filter = QFileDialog.getSaveFileName(
            window,
            "Save remote MolSysViewer download",
            suggested,
            "All files (*)",
        )
        if not selected:
            download.cancel()
            return
        destination = Path(selected).expanduser().resolve()
        download.setDownloadDirectory(str(destination.parent))
        download.setDownloadFileName(destination.name)
        active_downloads.append(download)

        def finished() -> None:
            if not download.isFinished():
                return
            if download in active_downloads:
                active_downloads.remove(download)
            window.statusBar().showMessage(f"Downloaded: {destination.name}")

        download.isFinishedChanged.connect(finished)
        download.accept()
        window.statusBar().showMessage(f"Downloading: {destination.name}")

    profile.downloadRequested.connect(handle_download)


def _install_remote_qt_status_bridge(*, window: Any, webview: Any, QTimer: Any) -> Any:
    """Mirror the shared remote page status in the native Qt status bar."""
    status_bar = window.statusBar()
    timer = QTimer(window)
    timer.setInterval(500)

    script = """(() => {
        const element = document.querySelector('[data-molsysviewer-remote-status]');
        if (!element) return null;
        return JSON.stringify({
            state: element.getAttribute('data-molsysviewer-remote-status'),
            text: element.textContent || ''
        });
    })()"""

    def update_status(value: Any) -> None:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return
        if not isinstance(value, dict):
            return
        state = value.get("state")
        if state == "ready":
            status_bar.clearMessage()
            return
        text = value.get("text")
        if isinstance(text, str) and text.strip():
            status_bar.showMessage(text.strip())

    def poll_status() -> None:
        webview.page().runJavaScript(script, update_status)

    def load_started() -> None:
        timer.stop()
        status_bar.showMessage("Connecting to remote MolSysViewer session…")

    def load_finished(success: bool) -> None:
        if not success:
            timer.stop()
            status_bar.showMessage("Could not load the remote MolSysViewer session.")
            return
        status_bar.showMessage("Remote session loaded; negotiating connection…")
        poll_status()
        timer.start()

    timer.timeout.connect(poll_status)
    webview.loadStarted.connect(load_started)
    webview.loadFinished.connect(load_finished)
    window._molsysviewer_remote_status_timer = timer
    return timer


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
    QMenu = qt["QMenu"]
    QCursor = qt["QCursor"]

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
    bridge = _get_helper("_install_qt_message_bridge")(
        webview,
        QWebEnginePage,
        QTimer,
        status_callback=lambda message: window.statusBar().showMessage(message),
        QWebEngineUrlSchemeHandler=QWebEngineUrlSchemeHandler,
        QBuffer=QBuffer,
        QByteArray=QByteArray,
    )

    # Persistent MolSysView driven through the Qt bridge: the same view backend
    # as Jupyter, so loads, rebuilds, interactions and movie export all work over
    # live messages. `view.widget` is a QtViewChannel wrapping the bridge; the
    # bridge forwards frontend product events to it, reaching _handle_frontend_event.
    from ..viewer.core import MolSysView
    from .view_channel import QtViewChannel

    channel = QtViewChannel(bridge)
    view = MolSysView(transport=channel, debug_js=debug_js)
    view._qt_process_events = getattr(app, "processEvents", None)  # noqa: SLF001
    webview._molsysviewer_view = view

    # Native Qt context menu on right-click: the frontend emits
    # interaction_context_menu, the bridge forwards it to the view, and this
    # callback (registered on the persistent view) shows a QMenu at the cursor.
    def _qt_context_menu(_event: Any) -> None:
        try:
            menu = QMenu(window)
            reset_action = menu.addAction("Reset view")
            reset_action.triggered.connect(lambda *_: view.camera.reset())
            menu.exec(QCursor.pos())
        except Exception:
            # The optional native menu must not break interaction dispatch; Q5 tracks diagnostics.
            pass

    view.on_context(_qt_context_menu)

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


def create_remote_qt_window(
    session_url: str,
    *,
    title: str = "MolSysViewer Remote",
    app_argv: Sequence[str] | None = None,
    width: int = 1440,
    height: int = 960,
) -> dict[str, Any]:
    """Create the native Qt shell for one authenticated remote session.

    The page is the same session client used by a normal browser. Qt therefore
    contributes window management and WebEngine presentation without owning a
    second remote protocol or a second :class:`MolSysView`.
    """
    if not isinstance(session_url, str) or not session_url:
        raise ValueError("session_url must be a non-empty HTTP(S) URL")
    parsed = urlsplit(session_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("session_url must be an absolute HTTP(S) URL")

    qt = _get_helper("_import_qt")()
    app = _get_helper("_get_or_create_application")(qt["QApplication"], app_argv)
    window = qt["QMainWindow"]()
    window.setWindowTitle(title)
    if hasattr(window, "resize"):
        window.resize(width, height)
    webview = qt["QWebEngineView"](window)
    window.setCentralWidget(webview)
    _install_remote_qt_chrome(
        window=window,
        webview=webview,
        QAction=qt["QAction"],
        QFileDialog=qt["QFileDialog"],
    )
    _install_remote_qt_status_bridge(
        window=window,
        webview=webview,
        QTimer=qt["QTimer"],
    )
    webview.setUrl(qt["QUrl"](session_url))
    return {
        "app": app,
        "window": window,
        "webview": webview,
        "session_url": session_url,
        "title": title,
    }


def launch_remote_qt(
    session_url: str,
    *,
    title: str = "MolSysViewer Remote",
    app_argv: Sequence[str] | None = None,
    width: int = 1440,
    height: int = 960,
    exec_app: bool = True,
) -> dict[str, Any]:
    """Show the native client for a remotely hosted MolSysViewer session."""
    runtime = create_remote_qt_window(
        session_url,
        title=title,
        app_argv=app_argv,
        width=width,
        height=height,
    )
    runtime["window"].show()
    runtime["exit_code"] = runtime["app"].exec() if exec_app else None
    return runtime
