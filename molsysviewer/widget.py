import anywidget
import traitlets as T
from pathlib import Path


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
    if (cached?.module) return Promise.resolve(cached.module);
    if (cached?.promise) return cached.promise;

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
                root[CACHE_KEY] = { module, source };
                cleanup();
                resolve(module);
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

    root[CACHE_KEY] = { promise };
    return promise;
}

export default {
    async render(context) {
        const module = await requestRuntimeModule(context.model);
        const widget = module.default || module;
        if (!widget || typeof widget.render !== "function") {
            throw new Error("MolSysViewer runtime module does not export a render function");
        }
        return widget.render(context);
    },
};
"""


class MolSysViewerWidget(anywidget.AnyWidget):
    _viewer_js_source = _VIEWER_JS_PATH.read_text(encoding="utf-8")
    _esm = _WIDGET_BOOTSTRAP_ESM

    initial_messages = T.List(default_value=[]).tag(sync=True)
    show_controls = T.Bool(default_value=True).tag(sync=True)
    enable_popout = T.Bool(default_value=True).tag(sync=True)
    autohide_controls = T.Bool(default_value=True).tag(sync=True)
    debug_js = T.Bool(default_value=False).tag(sync=True)
    controls_position = T.List(T.Unicode(), default_value=["top", "right"]).tag(sync=True)
    controls_position_fullscreen = T.List(T.Unicode(), default_value=["top", "right"]).tag(sync=True)
    controls_mode = T.Unicode(default_value="classic").tag(sync=True)
    panel_mode_style = T.Unicode(default_value="drawer").tag(sync=True)
    viewer_mode = T.Unicode(default_value="integrated").tag(sync=True)
    addon_states = T.Dict(default_value={}).tag(sync=True)
