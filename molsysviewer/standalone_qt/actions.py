"""Native keyboard affordances; scene tools stay in the shared canvas UI."""

from __future__ import annotations

from pathlib import Path

from .utils import (
    _get_helper,
    _load_molecular_system_into_qt_host,
    _persist_shell_state,
    _record_recent_source,
    _restore_last_source,
    _show_host_error,
    _show_status,
)


def _install_host_actions(*, window, webview, qt, current_state, html_path, current_title):
    """Register window shortcuts without constructing a second scene menu."""
    actions = {}

    def bind(key, label, shortcut, callback):
        action = qt["QAction"](label, window)
        action.setObjectName("molsysviewerHostAction_" + key)
        action.setShortcut(shortcut)
        action.triggered.connect(callback)
        window.addAction(action)
        actions[key] = action

    def load(source, label=None):
        _load_molecular_system_into_qt_host(
            source,
            window=window,
            webview=webview,
            current_state=current_state,
            loaded_label=label,
            status_message="Loading molecular system…" if source is not None else "Ready.",
        )

    def new_view():
        try:
            load(None)
        except Exception as exc:
            _show_host_error(window, qt["QMessageBox"], "New View Failed", f"Could not clear the view: {exc}")

    def open_file():
        path, _ = qt["QFileDialog"].getOpenFileName(window, "Open molecular system", "", "All files (*)")
        if not path:
            return
        try:
            label = Path(path).name
            load(path, label)
            _record_recent_source(current_state, kind="file", value=path, loaded_label=label)
            _persist_shell_state(current_state, window=window)
        except Exception as exc:
            _show_host_error(window, qt["QMessageBox"], "Open File Failed", f"Could not load file: {exc}")

    def restore_last():
        try:
            _restore_last_source(
                window=window,
                webview=webview,
                QUrl=qt["QUrl"],
                html_path=html_path,
                current_title=current_title,
                current_state=current_state,
            )
        except Exception as exc:
            _show_host_error(window, qt["QMessageBox"], "Restore Failed", f"Could not restore last source: {exc}")

    def export(kind):
        default = "molsysviewer-export.html" if kind == "html" else "molsysviewer-figure.png"
        file_filter = "HTML files (*.html)" if kind == "html" else "PNG files (*.png)"
        path, _ = qt["QFileDialog"].getSaveFileName(window, "Export MolSysViewer " + kind.upper(), default, file_filter)
        if not path:
            return
        try:
            view = webview._molsysviewer_view
            destination = Path(path).expanduser().resolve()
            if kind == "html":
                view.export.html(destination, title=current_title)
            else:
                view.export.figure(destination)
            _show_status(window, f"Exported: {destination.name}", kind="info")
        except Exception as exc:
            _show_host_error(window, qt["QMessageBox"], "Export Failed", f"Could not export {kind}: {exc}")

    def panel(mode):
        _get_helper("_send_viewer_message")(webview, {"op": "set_panel_mode", "panel": mode, "expanded": True})

    bind("new_view", "New view", "Ctrl+N", new_view)
    bind("open_file", "Open file", "Ctrl+O", open_file)
    bind("restore_last", "Restore last source", "Ctrl+Shift+R", restore_last)
    bind("close", "Close window", "Ctrl+W", window.close)
    bind("studio", "Open Studio", "Ctrl+1", lambda: panel("navigate"))
    bind("addons", "Open Add-ons", "Ctrl+2", lambda: panel("addons"))
    bind("export_html", "Export HTML", "Ctrl+Shift+S", lambda: export("html"))
    bind("export_figure", "Export figure", "Ctrl+Shift+E", lambda: export("figure"))
    bind("status_details", "Read status details", "Ctrl+Shift+D", lambda: window._molsysviewer_chrome.show_details())
    window._molsysviewer_host_actions = actions
    return actions
