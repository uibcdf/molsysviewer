from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
from typing import Any, Sequence
from urllib.parse import parse_qs, urlparse

from ..demo import demo
from ..standalone import _resolve_view, build_standalone0_html

QT_IMPORT_ERROR = (
    "PySide6_uibcdf with Qt WebEngine is required for the standalone Qt prototype. "
    "Install the UIBCDF conda stack from the uibcdf channel:\n"
    "  conda install -c uibcdf -c conda-forge pyside6-addons-uibcdf"
)

QT_STATE_FILENAME = "standalone_qt0_state.json"

# Custom URL schemes for the Qt live-message transport. Both must be registered
# with QWebEngineUrlScheme.registerScheme(...) BEFORE the QApplication is
# created, or Chromium treats them as invalid.
#   - QT_EVENT_SCHEME: JS -> Python events, intercepted in acceptNavigationRequest.
#   - QT_PAYLOAD_SCHEME: Python -> JS large payloads, served by a scheme handler
#     (so the page fetches them without needing file:// access).
QT_EVENT_SCHEME = "molsysviewer"
QT_PAYLOAD_SCHEME = "molsysviewer-payload"


def _get_helper(name: str) -> Any:
    m = sys.modules.get("molsysviewer.standalone_qt")
    if m is not None and hasattr(m, name):
        return getattr(m, name)
    return globals()[name]


def _configure_qt_webengine_environment(prefix: str | os.PathLike[str] | None = None) -> None:
    base = Path(prefix or os.environ.get("CONDA_PREFIX") or sys.prefix)
    candidates = {
        "QTWEBENGINEPROCESS_PATH": base / "libexec" / "QtWebEngineProcess",
        "QTWEBENGINE_RESOURCES_PATH": base / "resources",
        "QTWEBENGINE_LOCALES_PATH": base / "translations" / "qtwebengine_locales",
    }
    for env_name, path in candidates.items():
        if env_name not in os.environ and path.exists():
            os.environ[env_name] = str(path)


def _import_qt():
    _get_helper("_configure_qt_webengine_environment")()
    try:
        from PySide6_uibcdf.QtCore import QBuffer, QByteArray, QTimer, QUrl
        from PySide6_uibcdf.QtGui import QAction
        from PySide6_uibcdf.QtWebEngineCore import (
            QWebEnginePage, QWebEngineUrlScheme, QWebEngineUrlSchemeHandler,
        )
        from PySide6_uibcdf.QtWebEngineWidgets import QWebEngineView
        from PySide6_uibcdf.QtWidgets import (
            QApplication, QFileDialog, QInputDialog, QMainWindow, QMessageBox,
        )
    except Exception as exc:  # pragma: no cover
        raise ImportError(QT_IMPORT_ERROR) from exc

    return {
        "QAction": QAction,
        "QApplication": QApplication,
        "QBuffer": QBuffer,
        "QByteArray": QByteArray,
        "QFileDialog": QFileDialog,
        "QInputDialog": QInputDialog,
        "QMainWindow": QMainWindow,
        "QMessageBox": QMessageBox,
        "QTimer": QTimer,
        "QUrl": QUrl,
        "QWebEnginePage": QWebEnginePage,
        "QWebEngineUrlScheme": QWebEngineUrlScheme,
        "QWebEngineUrlSchemeHandler": QWebEngineUrlSchemeHandler,
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
    bridge = getattr(webview, "_molsysviewer_qt_bridge", None)
    if bridge is not None and hasattr(bridge, "on_load_started"):
        bridge.on_load_started()
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


class QtMessageBridge:
    """Runtime-only queue for Qt -> JS viewer messages."""

    def __init__(self, webview, QTimer, *, status_callback=None, event_sink=None) -> None:
        self.webview = webview
        self.QTimer = QTimer
        self.status_callback = status_callback
        # Optional callback(event: dict) that receives the frontend "product"
        # events (interaction, movie, scene acks, ready, ...) so a persistent
        # MolSysView can consume them. The pure-transport events (ack/error/
        # structure_ready/render_ready) are handled by the bridge and not forwarded.
        self.event_sink = event_sink
        self.ready = False
        self.queue: list[dict[str, Any]] = []
        self.inflight: dict[str, Any] | None = None
        self.next_id = 0
        self.generation = 0
        self.payload_ref_threshold_bytes = int(os.environ.get("MOLSYSVIEWER_QT_PAYLOAD_REF_THRESHOLD", "1000000"))
        # Large payloads are served in-memory over a custom URL scheme (see
        # MolSysViewerPayloadSchemeHandler) instead of a temp file + fetch(file://),
        # which Chromium blocks from a file:// page. Keyed by message id.
        self.payloads: dict[str, bytes] = {}

    def on_load_started(self) -> None:
        self.ready = False
        if self.inflight is not None:
            self._cleanup_entry(self.inflight)
        self._cleanup_queue()
        self.inflight = None
        self.generation += 1

    def begin_generation(self, *, clear_queue: bool = True) -> int:
        self.generation += 1
        if self.inflight is not None:
            self._cleanup_entry(self.inflight)
        self.inflight = None
        if clear_queue:
            self._cleanup_queue()
            self.queue.clear()
        return self.generation

    def send(self, message: dict[str, Any]) -> None:
        entry = self._make_entry(message)
        coalesce_key = entry.get("coalesce_key")
        if coalesce_key:
            self.queue = [item for item in self.queue if item.get("coalesce_key") != coalesce_key]
        self.queue.append(entry)
        self._flush()

    def handle_frontend_event(self, event: dict[str, Any]) -> None:
        name = event.get("event")
        if name == "ready":
            self.ready = True
            self._flush()
            self._forward_to_view(event)  # the view also needs "ready"
            return
        if name in {"message_ack", "message_error", "structure_ready", "render_ready"}:
            # Pure-transport events: handled here, not forwarded to the view.
            # Progress feedback for the current generation, so the user is never
            # left in front of a blank window during a long load.
            if event.get("generation") == self.generation:
                if name == "structure_ready":
                    self._show_status("Structure ready, rendering…")
                elif name == "render_ready":
                    self._show_status("Ready.")
            self._handle_message_event(event)
            return
        if name == "frontend_error":
            self._show_status(f"Frontend error: {event.get('error', 'unknown error')}")
            return
        # Any other frontend event (interaction_*, movie_*, region_ack, ...) is a
        # product event for the persistent MolSysView.
        self._forward_to_view(event)

    def _forward_to_view(self, event: dict[str, Any]) -> None:
        if callable(self.event_sink):
            try:
                self.event_sink(event)
            except Exception:
                pass

    def _make_entry(self, message: dict[str, Any]) -> dict[str, Any]:
        self.next_id += 1
        msg = dict(message)
        msg.setdefault("id", f"qt-{self.next_id}")
        msg.setdefault("generation", self.generation)
        payload_id = self._materialize_payload_ref(msg)
        op = str(msg.get("op", ""))
        wait_event = "structure_ready" if op in {"load_molsys_payload", "load_molsys_payload_ref"} else "message_ack"
        timeout_s = 30.0 if wait_event == "structure_ready" else 5.0
        return {
            "id": msg["id"],
            "generation": msg["generation"],
            "message": msg,
            "payload_id": payload_id,
            "wait_event": wait_event,
            "timeout_s": timeout_s,
            "coalesce_key": self._coalesce_key(msg),
        }

    def _materialize_payload_ref(self, message: dict[str, Any]) -> str | None:
        if message.get("op") != "load_molsys_payload":
            return None
        payload = message.get("payload")
        if not isinstance(payload, dict):
            return None
        payload_text = json.dumps(payload, separators=(",", ":"))
        if len(payload_text.encode("utf-8")) < self.payload_ref_threshold_bytes:
            return None
        payload_id = str(message["id"])
        self.payloads[payload_id] = payload_text.encode("utf-8")
        n_structures = len(payload.get("structures") or []) if isinstance(payload.get("structures"), list) else None
        message.pop("payload", None)
        message["op"] = "load_molsys_payload_ref"
        # Served by MolSysViewerPayloadSchemeHandler; the page fetches this URL.
        message["ref"] = {"kind": "scheme", "url": f"{QT_PAYLOAD_SCHEME}://payload/{payload_id}"}
        if n_structures is not None:
            message["n_structures"] = n_structures
        return payload_id

    def _coalesce_key(self, message: dict[str, Any]) -> str | None:
        op = message.get("op")
        if op == "set_panel_mode":
            return "set_panel_mode"
        if op == "set_trajectory_frame":
            return "set_trajectory_frame"
        return None

    def _flush(self) -> None:
        if not self.ready or self.inflight is not None or not self.queue:
            return
        entry = self.queue.pop(0)
        self.inflight = entry
        entry["deadline"] = time.monotonic() + float(entry["timeout_s"])
        if str(entry["message"].get("op", "")) in {"load_molsys_payload", "load_molsys_payload_ref"}:
            self._show_status("Loading molecular system…")
        self._arm_timeout(entry)
        self._run_javascript(entry)

    def _run_javascript(self, entry: dict[str, Any]) -> None:
        page = self.webview.page() if hasattr(self.webview, "page") else None
        if page is None or not hasattr(page, "runJavaScript"):
            self.inflight = None
            self.queue.insert(0, entry)
            return
        payload = json.dumps(entry["message"], separators=(",", ":"))
        script = (
            "(() => { "
            "const handler = window.__molsysviewerDocsHandleMessage; "
            "if (typeof handler !== 'function') return {accepted:false}; "
            f"const message = {payload}; "
            "Promise.resolve(handler(message)).catch((error) => { "
            "console.error('[MolSysViewer Qt bridge] message failed', error); "
            "}); "
            "return {accepted:true}; "
            "})()"
        )

        def _callback(result=None):
            accepted = isinstance(result, dict) and result.get("accepted") is True
            if accepted:
                return
            if self.inflight is entry:
                self.inflight = None
                self.ready = False
                self.queue.insert(0, entry)
                self._retry_later()

        try:
            page.runJavaScript(script, _callback)
        except TypeError:
            page.runJavaScript(script)
        except Exception as exc:
            self.inflight = None
            self.queue.insert(0, entry)
            self._show_status(f"Could not send viewer message: {exc}")
            self._retry_later()

    def _handle_message_event(self, event: dict[str, Any]) -> None:
        entry = self.inflight
        if entry is None:
            return
        if event.get("id") != entry.get("id"):
            return
        if event.get("generation") != entry.get("generation"):
            return
        if event.get("event") == "message_error":
            self.inflight = None
            self._cleanup_entry(entry)
            self._show_status(f"Viewer message failed: {event.get('error', 'unknown error')}")
            self._flush()
            return
        if event.get("event") != entry.get("wait_event"):
            return
        self.inflight = None
        self._cleanup_entry(entry)
        self._flush()

    def _arm_timeout(self, entry: dict[str, Any]) -> None:
        timeout_ms = max(1, int(float(entry["timeout_s"]) * 1000))

        def _check_timeout():
            if self.inflight is not entry:
                return
            if time.monotonic() <= float(entry.get("deadline", 0.0)):
                return
            self.inflight = None
            self._cleanup_entry(entry)
            self._show_status(f"Viewer message timed out: {entry['message'].get('op', 'unknown')}")
            self._flush()

        self.QTimer.singleShot(timeout_ms, _check_timeout)

    def _retry_later(self) -> None:
        self.QTimer.singleShot(50, self._flush)

    def _show_status(self, message: str) -> None:
        if callable(self.status_callback):
            self.status_callback(message)

    def _cleanup_entry(self, entry: dict[str, Any]) -> None:
        payload_id = entry.get("payload_id")
        if isinstance(payload_id, str):
            self.payloads.pop(payload_id, None)

    def _cleanup_queue(self) -> None:
        for entry in self.queue:
            self._cleanup_entry(entry)


def _register_qt_url_schemes(QWebEngineUrlScheme) -> None:
    """Register the custom transport schemes. Idempotent; must run before QApplication."""
    flag = QWebEngineUrlScheme.Flag
    specs = {
        # Event scheme: navigations intercepted in acceptNavigationRequest. No
        # handler; it only needs to be a known scheme so the navigation is valid.
        QT_EVENT_SCHEME: flag.SecureScheme | flag.LocalScheme | flag.LocalAccessAllowed,
        # Payload scheme: served by a QWebEngineUrlSchemeHandler and fetched by the
        # page, so it must allow CORS-enabled fetches.
        QT_PAYLOAD_SCHEME: flag.SecureScheme | flag.CorsEnabled,
    }
    for name, flags in specs.items():
        name_bytes = name.encode("ascii")
        if QWebEngineUrlScheme.schemeByName(name_bytes).name():
            continue  # already registered
        scheme = QWebEngineUrlScheme(name_bytes)
        scheme.setFlags(flags)
        QWebEngineUrlScheme.registerScheme(scheme)


def _make_payload_scheme_handler(QWebEngineUrlSchemeHandler, QBuffer, QByteArray, payloads: dict[str, bytes]):
    """Build a scheme handler that serves in-memory payloads over QT_PAYLOAD_SCHEME.

    The returned handler exposes a `served` list (payload ids actually served) so
    the round-trip can be asserted, e.g. by the real-Qt smoke test.
    """
    served: list[str] = []

    class MolSysViewerPayloadSchemeHandler(QWebEngineUrlSchemeHandler):
        def requestStarted(self, job):  # noqa: N802
            url = job.requestUrl()
            payload_id = (url.path() if hasattr(url, "path") else "").lstrip("/")
            data = payloads.get(payload_id)
            if data is None:
                if hasattr(job, "fail"):
                    job.fail(getattr(job, "UrlNotFound", 0))
                return
            buffer = QBuffer(job)
            buffer.setData(QByteArray(data))
            buffer.open(QBuffer.OpenModeFlag.ReadOnly if hasattr(QBuffer, "OpenModeFlag") else QBuffer.ReadOnly)
            job.reply(QByteArray(b"application/json"), buffer)
            served.append(payload_id)

    handler = MolSysViewerPayloadSchemeHandler()
    handler.served = served
    return handler


def _decode_qt_bridge_event(url: str) -> dict[str, Any] | None:
    parsed = urlparse(url)
    if parsed.scheme != QT_EVENT_SCHEME or parsed.netloc != "event":
        return None
    payload_values = parse_qs(parsed.query).get("payload")
    if not payload_values:
        return None
    try:
        event = json.loads(payload_values[0])
    except Exception:
        return None
    if not isinstance(event, dict) or not isinstance(event.get("event"), str):
        return None
    return event


def _install_qt_message_bridge(
    webview,
    QWebEnginePage,
    QTimer,
    *,
    status_callback=None,
    QWebEngineUrlSchemeHandler=None,
    QBuffer=None,
    QByteArray=None,
):
    class MolSysViewerQtPage(QWebEnginePage):
        def acceptNavigationRequest(self, url, nav_type, is_main_frame):  # noqa: N802
            event = _decode_qt_bridge_event(url.toString() if hasattr(url, "toString") else str(url))
            if event is not None:
                bridge = getattr(webview, "_molsysviewer_qt_bridge", None)
                if bridge is not None:
                    bridge.handle_frontend_event(event)
                return False
            return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    page = MolSysViewerQtPage(webview)
    webview.setPage(page)
    bridge = QtMessageBridge(webview, QTimer, status_callback=status_callback)
    setattr(webview, "_molsysviewer_qt_bridge", bridge)

    # Serve large payloads over the custom scheme, so the page fetches them
    # without needing (insecure) file:// access.
    if QWebEngineUrlSchemeHandler is not None and QBuffer is not None and QByteArray is not None:
        handler = _get_helper("_make_payload_scheme_handler")(
            QWebEngineUrlSchemeHandler, QBuffer, QByteArray, bridge.payloads
        )
        profile = page.profile() if hasattr(page, "profile") else None
        if profile is not None and hasattr(profile, "installUrlSchemeHandler"):
            profile.installUrlSchemeHandler(QT_PAYLOAD_SCHEME.encode("ascii"), handler)
        setattr(webview, "_molsysviewer_qt_payload_handler", handler)

    return bridge


def _send_viewer_message(webview, message: dict[str, Any]) -> None:
    bridge = getattr(webview, "_molsysviewer_qt_bridge", None)
    if bridge is not None:
        bridge.send(message)
        return
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


def _send_viewer_messages(webview, messages: Sequence[dict[str, Any]], *, new_generation: bool = False) -> None:
    bridge = getattr(webview, "_molsysviewer_qt_bridge", None)
    if bridge is not None and new_generation:
        bridge.begin_generation()
    for message in messages:
        _get_helper("_send_viewer_message")(webview, message)


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
        host_event_transport="url-scheme",
    )


def _build_qt_live_messages(
    molecular_system: Any,
    *,
    selection: str | Sequence[int] = "all",
    structure_indices: str | Sequence[int] = "all",
    syntax: str = "MolSysMT",
    load_mode: str = "selection",
    debug_js: bool | None = None,
) -> list[dict[str, Any]]:
    if molecular_system is None:
        return [{"op": "clear_all"}]
    view = _resolve_view(
        molecular_system,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        load_mode=load_mode,
        debug_js=debug_js,
    )
    messages = view._build_export_messages()  # noqa: SLF001
    return [{"op": "clear_all"}, *messages]


def _load_molecular_system_into_qt_host(
    molecular_system: Any,
    *,
    window,
    webview,
    current_state: dict[str, Any],
    loaded_label: str | None,
    status_message: str,
    selection: str | Sequence[int] = "all",
    structure_indices: str | Sequence[int] = "all",
    syntax: str = "MolSysMT",
    load_mode: str = "selection",
    debug_js: bool | None = None,
) -> None:
    messages = _get_helper("_build_qt_live_messages")(
        molecular_system,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        load_mode=load_mode,
        debug_js=debug_js,
    )
    _get_helper("_send_viewer_messages")(webview, messages, new_generation=True)
    if molecular_system is None:
        _get_helper("_set_empty_state")(window, current_state)
    else:
        if loaded_label is None:
            current_state["molecular_system"] = molecular_system
            current_state["loaded_label"] = None
            if hasattr(window, "setWindowTitle"):
                window.setWindowTitle(current_state["base_title"])
        else:
            _get_helper("_set_loaded_state")(window, current_state, molecular_system, loaded_label)
    _get_helper("_persist_shell_state")(current_state, window=window)
    _get_helper("_show_status")(window, status_message)


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
    _get_helper("_load_molecular_system_into_qt_host")(
        demo[demo_name],
        window=window,
        webview=webview,
        current_state=current_state,
        loaded_label=demo_name,
        status_message=f"Loaded demo: {demo_name}",
    )
    _get_helper("_record_recent_source")(
        current_state,
        kind="demo",
        value=demo_name,
        loaded_label=demo_name,
    )


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
    _get_helper("_load_molecular_system_into_qt_host")(
        value,
        window=window,
        webview=webview,
        current_state=current_state,
        loaded_label=loaded_label,
        status_message=(
            f"Loaded PDB ID: {loaded_label}"
            if kind == "pdb_id"
            else f"Loaded source: {loaded_label}"
            if kind == "source"
            else f"Loaded file: {loaded_label}"
        ),
    )
    _get_helper("_record_recent_source")(
        current_state,
        kind=kind,
        value=value,
        loaded_label=loaded_label,
    )


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
