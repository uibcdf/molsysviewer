from hashlib import sha256
from pathlib import Path

import anywidget
import traitlets as T

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
