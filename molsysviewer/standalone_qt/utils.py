from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Sequence

from ..demo import demo
from ..standalone import _resolve_view, build_standalone0_html

QT_IMPORT_ERROR = (
    "PySide6_uibcdf with Qt WebEngine is required for the standalone Qt prototype. "
    "Install the UIBCDF conda stack from the uibcdf channel:\n"
    "  conda install -c uibcdf -c conda-forge pyside6-addons-uibcdf"
)

QT_STATE_FILENAME = "standalone_qt0_state.json"


def _get_helper(name: str) -> Any:
    m = sys.modules.get("molsysviewer.standalone_qt")
    if m is not None and hasattr(m, name):
        return getattr(m, name)
    return globals()[name]


def _import_qt():
    try:
        from PySide6_uibcdf.QtCore import QUrl
        from PySide6_uibcdf.QtGui import QAction
        from PySide6_uibcdf.QtWebEngineWidgets import QWebEngineView
        from PySide6_uibcdf.QtWidgets import (
            QApplication, QFileDialog, QInputDialog, QMainWindow, QMessageBox,
        )
    except Exception as exc:  # pragma: no cover
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
    path = _get_helper("_qt_shell_state_path")()
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
    path = _get_helper("_qt_shell_state_path")()
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


def _show_host_error(window, QMessageBox, title: str, message: str) -> None:
    _get_helper("_show_status")(window, message)
    if hasattr(QMessageBox, "critical"):
        QMessageBox.critical(window, title, message)
    elif hasattr(QMessageBox, "warning"):
        QMessageBox.warning(window, title, message)


def _set_action_shortcut(action, shortcut: str) -> None:
    if hasattr(action, "setShortcut"):
        action.setShortcut(shortcut)
    else:
        setattr(action, "shortcut", shortcut)


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
        window.setWindowTitle(_get_helper("_window_title")(current_state["base_title"], loaded_label))


def _set_empty_state(window, current_state: dict[str, Any]) -> None:
    current_state["molecular_system"] = None
    current_state["loaded_label"] = None
    if hasattr(window, "setWindowTitle"):
        window.setWindowTitle(current_state["base_title"])


def _show_startup_status(window, current_state: dict[str, Any]) -> None:
    loaded_label = current_state.get("loaded_label")
    if isinstance(loaded_label, str) and loaded_label:
        _get_helper("_show_status")(window, f"Ready: {loaded_label}")
        return
    if current_state.get("molecular_system") is not None:
        _get_helper("_show_status")(window, "Ready. Molecular system loaded.")
        return
    _get_helper("_show_status")(
        window,
        "Ready. Use File to load a demo, file, PDB ID, or MolSysMT source.",
    )


def _current_source_summary(current_state: dict[str, Any]) -> str:
    loaded_label = current_state.get("loaded_label")
    if isinstance(loaded_label, str) and loaded_label:
        return loaded_label
    if current_state.get("molecular_system") is not None:
        return "Molecular system loaded"
    return "Empty host"


def _host_info_message(current_state: dict[str, Any], html_path: str) -> str:
    recent_sources = current_state.get("recent_sources", [])
    return (
        "MolSysViewer Qt Prototype\n\n"
        f"Current source: {_current_source_summary(current_state)}\n"
        f"Recent sources: {len(recent_sources)}\n"
        f"HTML path: {html_path}\n\n"
        "Primary shell shortcuts:\n"
        "  Ctrl+N  New Empty Host\n"
        "  Ctrl+O  Open File\n"
        "  Ctrl+R  Restore Last Source\n"
        "  Ctrl+1  Navigate\n"
        "  Ctrl+2  Workbench\n"
        "  Escape  Close Panel Mode\n"
        "  Ctrl+Shift+S  Export HTML\n"
        "  Ctrl+Shift+E  Export Figure"
    )


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


def _clear_recent_sources(current_state: dict[str, Any]) -> None:
    current_state["recent_sources"] = []
    current_state["last_source"] = None


def _persist_shell_state(current_state: dict[str, Any], window=None) -> None:
    if window is not None:
        window_size = _get_helper("_capture_window_size")(window)
        if window_size is not None:
            current_state["window_size"] = window_size
    try:
        _get_helper("_save_qt_shell_state")(current_state)
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
    local_runtime = Path(__file__).parent.with_name("viewer.js").resolve().as_uri()
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
        runtime_urls=_get_helper("_qt_runtime_urls")(),
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
    _get_helper("_rebuild_qt_html")(
        demo[demo_name],
        html_path=html_path,
        title=current_title,
    )
    _get_helper("_set_loaded_state")(window, current_state, demo[demo_name], demo_name)
    _get_helper("_record_recent_source")(
        current_state,
        kind="demo",
        value=demo_name,
        loaded_label=demo_name,
    )
    _get_helper("_persist_shell_state")(current_state, window=window)
    _get_helper("_reload_html_in_view")(webview, QUrl, html_path)
    _get_helper("_show_status")(window, f"Loaded demo: {demo_name}")


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
        _get_helper("_load_demo_into_qt_host")(
            str(value),
            window=window,
            webview=webview,
            QUrl=QUrl,
            html_path=html_path,
            current_title=current_title,
            current_state=current_state,
        )
        return
    _get_helper("_rebuild_qt_html")(
        value,
        html_path=html_path,
        title=current_title,
    )
    _get_helper("_set_loaded_state")(window, current_state, value, loaded_label)
    _get_helper("_record_recent_source")(
        current_state,
        kind=kind,
        value=value,
        loaded_label=loaded_label,
    )
    _get_helper("_persist_shell_state")(current_state, window=window)
    _get_helper("_reload_html_in_view")(webview, QUrl, html_path)
    if kind == "pdb_id":
        _get_helper("_show_status")(window, f"Loaded PDB ID: {loaded_label}")
    elif kind == "source":
        _get_helper("_show_status")(window, f"Loaded source: {loaded_label}")
    else:
        _get_helper("_show_status")(window, f"Loaded file: {loaded_label}")


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
        _get_helper("_show_status")(window, "No last source is available.")
        return
    _get_helper("_load_recent_source")(
        recent_entry,
        window=window,
        webview=webview,
        QUrl=QUrl,
        html_path=html_path,
        current_title=current_title,
        current_state=current_state,
    )
