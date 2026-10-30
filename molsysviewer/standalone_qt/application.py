from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit

from smonitor import signal

from .._private.argdigest import digest
from ..standalone import build_standalone0_html
from .actions import _install_host_actions
from .chrome import _install_window_chrome
from .geometry import _restore_geometry

# `_get_helper` resolves these **by name** -- `getattr(module, name)` first, then
# `globals()[name]`. Ruff cannot see a string lookup, so it reports every one of them
# as unused: they are load-bearing, and deleting them breaks the Qt host at runtime
# with a KeyError no test would attribute to the import.
from .utils import (  # noqa: F401
    _get_or_create_application,
    _import_qt,
    _install_qt_message_bridge,
    _load_molecular_system_into_qt_host,
    _load_qt_shell_state,
    _qt_runtime_urls,
    _show_startup_status,
    _show_status,
)

logger = logging.getLogger(__name__)


def _run_remote_page_action(webview: Any, selector: str, callback=None, *, reveal_selector: str | None = None) -> None:
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


def _install_remote_qt_chrome(*, window: Any, webview: Any, QAction: Any, QFileDialog: Any) -> None:
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

    def page_action(selector: str, missing_message: str, *, reveal_selector: str | None = None):
        return lambda *_: _run_remote_page_action(
            webview,
            selector,
            lambda found: None if found else window.statusBar().showMessage(missing_message),
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

    _install_qt_downloads(window=window, webview=webview, QFileDialog=QFileDialog)


def _install_qt_downloads(*, window: Any, webview: Any, QFileDialog: Any) -> None:
    """Let each native host own the destinations of its browser downloads."""
    page = webview.page()
    profile = page.profile()
    active_downloads: list[Any] = []
    window._molsysviewer_downloads = active_downloads
    window._molsysviewer_remote_downloads = active_downloads

    def handle_download(download: Any) -> None:
        suggested = Path(str(download.suggestedFileName() or "molsysviewer-download")).name
        selected, _filter = QFileDialog.getSaveFileName(
            window,
            "Save MolSysViewer download",
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
            state = download.state()
            if state == type(download).DownloadState.DownloadCompleted:
                _show_status(window, f"Downloaded: {destination.name}", kind="info")
            elif state == type(download).DownloadState.DownloadCancelled:
                _show_status(window, f"Download cancelled: {destination.name}", kind="info")
            else:
                _show_status(
                    window,
                    f"Download interrupted: {destination.name}: {download.interruptReasonString()}",
                    kind="error",
                )

        download.isFinishedChanged.connect(finished)
        download.accept()
        _show_status(window, f"Downloading: {destination.name}", kind="progress")

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


def _install_qt_fullscreen(*, window: Any, webview: Any) -> None:
    """Bridge the page Fullscreen API to the enclosing native Qt window."""
    page = webview.page()
    settings = page.settings()
    settings.setAttribute(
        type(settings).WebAttribute.FullScreenSupportEnabled,
        True,
    )
    restore = {"maximized": False}

    def handle_request(request: Any) -> None:
        enabling = bool(request.toggleOn())
        if enabling:
            restore["maximized"] = bool(window.isMaximized() if hasattr(window, "isMaximized") else False)
            window._molsysviewer_fullscreen_maximized = restore["maximized"]
            window.showFullScreen()
        elif restore["maximized"] and hasattr(window, "showMaximized"):
            window.showMaximized()
        else:
            window.showNormal()
        request.accept()

    page.fullScreenRequested.connect(handle_request)
    window._molsysviewer_remote_fullscreen_handler = handle_request


def _get_helper(name: str) -> Any:
    m = sys.modules.get("molsysviewer.standalone_qt")
    if m is not None and hasattr(m, name):
        return getattr(m, name)
    return globals()[name]


@signal()
@digest()
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
    width: int | None = None,
    height: int | None = None,
    skip_digestion: bool = False,
) -> dict[str, Any]:
    qt = _get_helper("_import_qt")()
    QApplication = qt["QApplication"]
    QMainWindow = qt["QMainWindow"]
    QWebEngineView = qt["QWebEngineView"]
    QUrl = qt["QUrl"]
    QFileDialog = qt["QFileDialog"]
    QTimer = qt["QTimer"]
    QWebEnginePage = qt["QWebEnginePage"]
    QWebEngineProfile = qt["QWebEngineProfile"]
    QWebEngineUrlScheme = qt["QWebEngineUrlScheme"]
    QWebEngineUrlSchemeHandler = qt["QWebEngineUrlSchemeHandler"]
    QBuffer = qt["QBuffer"]
    QByteArray = qt["QByteArray"]

    # Must run before the QApplication is created, or Chromium rejects the schemes.
    _get_helper("_register_qt_url_schemes")(QWebEngineUrlScheme)

    html_owner = None
    if output_filename is None:
        html_owner = tempfile.TemporaryDirectory(prefix="molsysviewer-qt0-")
        output_filename = str(Path(html_owner.name) / "shell.html")
    try:
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
    except BaseException:
        if html_owner is not None:
            html_owner.cleanup()
        raise

    current_state = {"molecular_system": molecular_system, "base_title": title, "loaded_label": None}
    current_state.update(_get_helper("_load_qt_shell_state")())

    app = _get_helper("_get_or_create_application")(QApplication, app_argv)

    class StandaloneWindow(QMainWindow):
        _molsysviewer_cleanup = None

        def closeEvent(self, event):  # noqa: N802
            cleanup = self._molsysviewer_cleanup
            if cleanup is not None:
                try:
                    cleanup()
                except Exception:
                    logger.exception("Could not close the local Qt host cleanly")
                    event.ignore()
                    return
                self._molsysviewer_cleanup = None
            super().closeEvent(event)

    window = StandaloneWindow()
    window.setWindowTitle(title)

    webview = QWebEngineView(window)
    profile = QWebEngineProfile(window)
    bridge = _get_helper("_install_qt_message_bridge")(
        webview,
        QWebEnginePage,
        QTimer,
        status_callback=lambda message: _show_status(window, message),
        QWebEngineUrlSchemeHandler=QWebEngineUrlSchemeHandler,
        QBuffer=QBuffer,
        QByteArray=QByteArray,
        profile=profile,
        synchronize_draws=True,
    )

    # Persistent MolSysView driven through the Qt bridge: the same view backend
    # as Jupyter, so loads, rebuilds, interactions and movie export all work over
    # live messages. `view.widget` is a QtViewChannel wrapping the bridge; the
    # bridge forwards frontend product events to it, reaching _handle_frontend_event.
    from ..viewer.core import MolSysView
    from .view_channel import QtViewChannel

    channel = QtViewChannel(bridge)
    view = MolSysView(transport=channel, debug_js=debug_js)
    channel.show_controls = include_controls
    channel.enable_popout = include_popout
    view._qt_process_events = getattr(app, "processEvents", None)  # noqa: SLF001
    webview._molsysviewer_view = view

    _install_qt_fullscreen(window=window, webview=webview)
    _install_qt_downloads(window=window, webview=webview, QFileDialog=QFileDialog)

    page = webview.page()
    if html_owner is not None:
        # Chromium may still read the shell until the page has been disposed.
        page.destroyed.connect(lambda *_: html_owner.cleanup())

    def close_host() -> None:
        from .utils import _persist_shell_state

        _persist_shell_state(current_state, window=window)
        for download in list(window._molsysviewer_downloads):
            if not download.isFinished():
                download.cancel()
        view.close()
        bridge._close()
        webview.stop()
        page.deleteLater()
        profile.deleteLater()  # Queued after its page, as Qt requires.

    window._molsysviewer_cleanup = close_host

    webview.setUrl(QUrl.fromLocalFile(html_path))
    _install_host_actions(
        window=window, webview=webview, qt=qt, html_path=html_path, current_title=title, current_state=current_state
    )
    _install_window_chrome(window=window, webview=webview, qt=qt)
    _restore_geometry(window, app, qt, current_state, width=width, height=height)
    try:
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
    except BaseException:
        window.close()
        raise

    return {
        "app": app,
        "window": window,
        "webview": webview,
        "html_path": html_path,
        "title": title,
    }


@signal()
@digest()
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
    width: int | None = None,
    height: int | None = None,
    exec_app: bool = True,
    skip_digestion: bool = False,
) -> dict[str, Any]:
    m = sys.modules.get("molsysviewer.standalone_qt")
    create_func = (
        getattr(m, "create_standalone_qt0_window", create_standalone_qt0_window) if m else create_standalone_qt0_window
    )
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

    Experimental in MolSysViewer 1.0; the remote API may change later.
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
    _install_qt_fullscreen(
        window=window,
        webview=webview,
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
    """Show the experimental native client for a remote MolSysViewer session."""
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
