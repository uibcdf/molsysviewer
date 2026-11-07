import math
from asyncio import get_running_loop
from hashlib import sha256
from numbers import Real
from pathlib import Path
from threading import RLock, get_ident
from time import monotonic

import anywidget
import traitlets as T
from smonitor import signal

from ._private.argdigest import digest
from .runtime_contract import wrap_outbound

_VIEWER_JS_PATH = Path(__file__).parent / "viewer.js"
_WIDGET_BOOTSTRAP_ESM = r"""const CACHE_KEY = "__molsysviewer_anywidget_runtime__";

async function importRuntimeFromSource(source) {
    const url = URL.createObjectURL(new Blob([source], { type: "text/javascript" }));
    try {
        return await import(url);
    } finally {
        URL.revokeObjectURL(url);
    }
}

function requestRuntimeModule(model) {
    const root = globalThis;
    const cached = root[CACHE_KEY];
    const digest = model.get("runtime_bundle_digest") || "";
    if (cached?.digest === digest && cached?.module) return Promise.resolve(cached);
    if (cached?.digest === digest && cached?.promise) return cached.promise;

    const promise = new Promise((resolve, reject) => {
        let done = false;
        const cleanup = () => {
            done = true;
            if (timer) clearTimeout(timer);
            model.off("msg:custom", onMessage);
        };
        const onMessage = async (msg) => {
            if (!msg || msg.op !== "widget_runtime_source") return;
            const source = typeof msg.source === "string" ? msg.source : "";
            if (!source) {
                cleanup();
                root[CACHE_KEY] = undefined;
                reject(new Error("MolSysViewer widget runtime response was empty"));
                return;
            }
            try {
                const module = await importRuntimeFromSource(source);
                const runtime = { module, source, digest };
                root[CACHE_KEY] = runtime;
                cleanup();
                resolve(runtime);
            } catch (error) {
                root[CACHE_KEY] = undefined;
                cleanup();
                reject(error);
            }
        };
        const timer = setTimeout(() => {
            if (done) return;
            root[CACHE_KEY] = undefined;
            cleanup();
            reject(new Error("Timed out waiting for MolSysViewer widget runtime source"));
        }, 15000);
        model.on("msg:custom", onMessage);
        model.send({ event: "request_widget_runtime_source" });
    });

    root[CACHE_KEY] = { promise, digest };
    return promise;
}

export default {
    async render(context) {
        const runtime = await requestRuntimeModule(context.model);
        const module = runtime.module;
        const entrypoint = context.model.get("runtime_entrypoint");
        const widget = entrypoint ? module[entrypoint] : module.default || module;
        if (!widget || typeof widget.render !== "function") {
            throw new Error("MolSysViewer runtime module does not export a render function");
        }
        // Bind the popup to the source that actually rendered this widget.
        return widget.render({ ...context, runtimeSource: runtime.source });
    },
};
"""


class _ScheduledCallback:
    """One host-loop callback, released before calling its consumer."""

    def __init__(self, pending, callback, lock):
        self._pending = pending
        self._lock = lock
        self._callback = callback
        self._cancel_timer = None
        self._active = True
        with lock:
            pending.add(self)

    def _set_cancel(self, cancel):
        with self._lock:
            if self._active:
                self._cancel_timer = cancel
                return
        # Cancellation may precede registration on a different host thread.
        cancel()

    def _is_active(self):
        with self._lock:
            return self._active

    def _timer_closed(self):
        with self._lock:
            self._cancel_timer = None
        self.cancel()

    def cancel(self):
        with self._lock:
            if not self._active:
                return
            self._active = False
            self._pending.discard(self)
            self._callback = None
            cancel, self._cancel_timer = self._cancel_timer, None
        if cancel is not None:
            cancel()

    def __call__(self):
        with self._lock:
            if not self._active:
                return
            callback = self._callback
            self._active = False
            self._pending.discard(self)
            self._callback = None
            cancel, self._cancel_timer = self._cancel_timer, None
        if cancel is not None:
            cancel()
        callback()


def _callback_delay(delay_seconds, callback):
    if (
        isinstance(delay_seconds, bool)
        or not isinstance(delay_seconds, Real)
        or not math.isfinite(delay_seconds)
        or delay_seconds < 0
    ):
        raise ValueError("Host callback delay must be finite and nonnegative.")
    if not callable(callback):
        raise TypeError("Host callback must be callable.")
    return float(delay_seconds)


def _kernel_callback_host():
    from IPython import get_ipython

    io_loop = getattr(getattr(get_ipython(), "kernel", None), "io_loop", None)
    if io_loop is not None:
        return "tornado", io_loop
    return None


def _callback_host_running(host):
    kind, loop = host
    if kind == "tornado":
        if not all(callable(getattr(loop, name, None)) for name in ("add_callback", "call_later", "remove_timeout")):
            return False
        loop = getattr(loop, "asyncio_loop", None)
    return loop is not None and loop.is_running() and not loop.is_closed()


class MolSysViewerWidget(anywidget.AnyWidget):
    supports_array_native_buffers = True
    _viewer_js_source = _VIEWER_JS_PATH.read_text(encoding="utf-8")
    _viewer_js_digest = sha256(_viewer_js_source.encode("utf-8")).hexdigest()
    _esm = _WIDGET_BOOTSTRAP_ESM

    initial_messages = T.List(default_value=[]).tag(sync=True)
    # Initial molecular data may arrive only after the frontend's ready event.
    # This small hint distinguishes that prepared load from an empty widget.
    has_molecular_system = T.Bool(default_value=False).tag(sync=True)
    show_controls = T.Bool(default_value=True).tag(sync=True)
    enable_popout = T.Bool(default_value=True).tag(sync=True)
    runtime_viewer_id = T.Unicode(default_value="").tag(sync=True)
    runtime_session_id = T.Unicode(default_value="").tag(sync=True)
    presentation_host_id = T.Unicode(default_value="").tag(sync=True)
    runtime_bundle_digest = T.Unicode(default_value=_viewer_js_digest).tag(sync=True)
    autohide_controls = T.Bool(default_value=True).tag(sync=True)
    autohide_scope = T.Enum(["controls", "canvas"], default_value="controls").tag(sync=True)
    debug_js = T.Bool(default_value=False).tag(sync=True)
    controls_position = T.List(T.Unicode(), default_value=["top", "right"]).tag(sync=True)
    controls_position_fullscreen = T.List(T.Unicode(), default_value=["top", "right"]).tag(sync=True)
    controls_mode = T.Unicode(default_value="compact").tag(sync=True)
    panel_mode_style = T.Unicode(default_value="drawer").tag(sync=True)
    viewer_mode = T.Unicode(default_value="standard").tag(sync=True)
    addon_states = T.Dict(default_value={}).tag(sync=True)

    def __init__(self, *args, **kwargs):
        self._callbacks_lock = RLock()
        self._scheduled_callbacks = set()
        self._callbacks_closed = False
        self._callback_thread_ident = get_ident()
        self._callback_host = _kernel_callback_host()
        if self._callback_host is None:
            try:
                self._callback_host = "asyncio", get_running_loop()
            except RuntimeError:
                pass
        super().__init__(*args, **kwargs)

    def _schedule_callback(self, delay_seconds, callback):
        """Schedule on this connector's live host loop; never start a thread.

        A kernel may dispatch comms on another registered thread. Arming and
        cancellation are sent to its bound host loop, never the caller's private
        loop. An unbound plain-Python widget may bind a running creator loop;
        unrelated worker threads cannot appoint a host for it.
        """
        delay = _callback_delay(delay_seconds, callback)
        with self._callbacks_lock:
            if self._callbacks_closed:
                raise RuntimeError("The widget is closed.")
            host = self._callback_host
            if host is None:
                host = _kernel_callback_host()
                if host is None and get_ident() == self._callback_thread_ident:
                    try:
                        host = "asyncio", get_running_loop()
                    except RuntimeError:
                        pass
            if host is None or not _callback_host_running(host):
                raise RuntimeError("The widget has no running notebook or asyncio event loop.") from None
            self._callback_host = host
            handle = _ScheduledCallback(self._scheduled_callbacks, callback, self._callbacks_lock)
        kind, loop = host
        deadline = monotonic() + delay
        submit = loop.add_callback if kind == "tornado" else loop.call_soon_threadsafe

        def arm():
            if not handle._is_active():
                return
            timer = loop.call_later(max(0.0, deadline - monotonic()), handle)

            def cancel_timer():
                cancel = (lambda: loop.remove_timeout(timer)) if kind == "tornado" else timer.cancel
                try:
                    submit(cancel)
                except RuntimeError:
                    # A closed asyncio host cannot dispatch this timer again.
                    timer.cancel()

            handle._set_cancel(cancel_timer)

        try:
            submit(arm)
        except BaseException:
            handle.cancel()
            raise
        return handle

    @signal()
    @digest()
    def close(self, *, skip_digestion: bool = False):
        """Cancel connector-owned callbacks before closing its comm."""
        self._close_connector()

    def __del__(self):
        # ipywidgets' inherited finalizer calls the public close(). At Python
        # shutdown its diagnostic/digestion imports may already be unavailable.
        # Internal resource release keeps the same behavior without that API
        # wrapper; explicit user close still has the full public contract.
        self._close_connector()

    def _close_connector(self):
        with self._callbacks_lock:
            self._callbacks_closed = True
            for handle in tuple(self._scheduled_callbacks):
                handle.cancel()
        super().close()

    def send(self, content, buffers=None):
        """Apply the R1 runtime envelope to control-plane messages on the wire.

        The AnyWidget connector owns its wire format: this wraps domain
        projection/request messages into a RuntimeEnvelope, while raw/data-plane
        and already-enveloped messages (e.g. a duplicate-command ack) pass through
        unchanged. Tests that replace ``view.widget.send`` therefore observe the
        domain message, and only the real connector envelopes the wire.
        """
        if isinstance(content, dict):
            content = wrap_outbound(content, self.runtime_viewer_id, self.runtime_session_id)
        super().send(content, buffers=buffers)
