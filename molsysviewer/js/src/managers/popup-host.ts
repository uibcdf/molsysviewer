import {
    createPopupChannelIdentity,
    createSecureRuntimeId,
    decodePopupEvent,
    encodePopupMessage,
    type PopupChannelIdentity,
    type PopupMode,
    type PopupWireMessage,
} from "../messages/popup-channel";
import {
    RUNTIME_PROTOCOL_VERSION,
    RuntimeMessageRouter,
    type RuntimeDirection,
    type RuntimeEnvelope,
} from "../messages/runtime-router";
import { popupActionAllows } from "../messages/runtime-actions";

type PopupSourceProvider = () => string | Promise<string>;

type PopupHostOptions = {
    source?: string;
    moduleUrl?: string;
    sourceProvider?: PopupSourceProvider;
    viewerId?: string;
    sessionId?: string;
    /** Fired when a popup endpoint goes away, so the host can cancel work it
     *  owns (pending requests, retained buffers) instead of leaking it. */
    onEndpointClosed?: (mode: PopupMode, endpointId: string) => void;
    /** Reports a manifest refusal through the host's observable diagnostic seam. */
    onContractRejection?: (rejection: {
        seam: "popup-host-inbound" | "popup-host-outbound";
        reason: string;
        detail: string;
    }) => void;
};

export class PopupHostManager {
    private popoutWin: Window | null = null;
    public panelWin: Window | null = null;
    public isReady = false;
    public isPanelReady = false;

    private viewerJsSource: string;
    private readonly viewerModuleUrl?: string;
    private readonly viewerSourceProvider?: PopupSourceProvider;
    private readonly viewerId: string;
    private readonly sessionId: string;
    private readonly authorityEndpointId: string;
    private readonly hostEndpointId: string;
    private readonly router: RuntimeMessageRouter;
    private messageCounter = 0;
    private readonly channels = new Map<PopupMode, PopupChannelIdentity>();
    private readonly onEndpointClosed?: (mode: PopupMode, endpointId: string) => void;
    private readonly onContractRejection?: PopupHostOptions["onContractRejection"];
    private readonly bootstrapping = new Set<PopupMode>();
    private readonly bootstrapQueues = new Map<PopupMode, Array<{ type: string; data: any }>>();

    /** Endpoint id of the live popup for `mode`, or null when none is open. */
    popupEndpointId(mode: PopupMode): string | null {
        return this.channels.get(mode)?.popupEndpointId ?? null;
    }

    beginBootstrap(mode: PopupMode): void {
        if (this.bootstrapping.has(mode)) return;
        this.bootstrapping.add(mode);
        this.bootstrapQueues.set(mode, []);
    }

    completeBootstrap(mode: PopupMode): void {
        this.bootstrapping.delete(mode);
        const queued = this.bootstrapQueues.get(mode) ?? [];
        this.bootstrapQueues.delete(mode);
        for (const { type, data } of queued) this.sendTo(mode, type, data);
    }

    constructor(viewer: string | PopupHostOptions) {
        if (typeof viewer === "string") {
            this.viewerJsSource = viewer;
            this.viewerId = createSecureRuntimeId("view");
            this.sessionId = createSecureRuntimeId("session");
            this.authorityEndpointId = `python:${this.viewerId}`;
            this.hostEndpointId = `widget-host:${this.sessionId}`;
            this.router = this.createRouter();
            return;
        }
        this.viewerJsSource = viewer.source ?? "";
        this.viewerModuleUrl = viewer.moduleUrl;
        this.viewerSourceProvider = viewer.sourceProvider;
        this.viewerId = viewer.viewerId || createSecureRuntimeId("view");
        this.sessionId = viewer.sessionId || createSecureRuntimeId("session");
        this.authorityEndpointId = `python:${this.viewerId}`;
        this.hostEndpointId = `widget-host:${this.sessionId}`;
        this.onEndpointClosed = viewer.onEndpointClosed;
        this.onContractRejection = viewer.onContractRejection;
        this.router = this.createRouter();
    }

    private async resolveViewerJsSource(): Promise<string> {
        if (this.viewerJsSource) return this.viewerJsSource;
        if (!this.viewerSourceProvider) return "";
        const source = await this.viewerSourceProvider();
        this.viewerJsSource = source || "";
        return this.viewerJsSource;
    }

    private controller?: any;

    setController(controller: any) {
        this.controller = controller;
    }

    get isCanvasOpen() {
        return this.popoutWin && !this.popoutWin.closed;
    }

    get isPanelOpen() {
        return this.panelWin && !this.panelWin.closed;
    }

    async open(mode: "canvas" | "panel" = "canvas") {
        const isOpen = mode === "canvas" ? this.isCanvasOpen : this.isPanelOpen;
        if (isOpen) {
            this.close(mode);
            return;
        }

        let resolvedModuleUrl: string | null = null;
        if (this.viewerModuleUrl) {
            try {
                resolvedModuleUrl = new URL(this.viewerModuleUrl, window.location.href).href;
                fetch(resolvedModuleUrl, { cache: "force-cache" }).catch(() => {});
            } catch (e) {
                resolvedModuleUrl = null;
            }
        }

        // The panel window opens at the size of the panel it came out of, rather
        // than a fixed 450x800 that was about half its width. See
        // `MolSysViewerController.getPanelPopupSize`.
        let features = "width=960,height=720";
        if (mode === "panel") {
            const size = this.controller?.getPanelPopupSize?.() ?? { width: 950, height: 800 };
            features = `width=${size.width},height=${size.height}`;
        }
        const win = window.open("", "_blank", features);
        if (!win) return;

        if (mode === "canvas") {
            this.popoutWin = win;
            this.isReady = false;
        } else {
            this.panelWin = win;
            this.isPanelReady = false;
        }

        const channel = createPopupChannelIdentity(
            this.viewerId,
            this.sessionId,
            mode,
            this.authorityEndpointId,
            this.hostEndpointId,
        );
        this.channels.set(mode, channel);
        this.router.registerEndpoint({
            endpointId: channel.popupEndpointId,
            role: mode === "canvas" ? "canvas-popup" : "panel-popup",
        });
        (win as Window & { molsysviewer_popup_channel?: PopupChannelIdentity })
            .molsysviewer_popup_channel = channel;

        if (this.controller) {
            (win as any).molsysviewer_init_options = {
                viewerMode: this.controller.getViewerMode(),
                controlsMode: this.controller.getControlsMode(),
                panelModeStyle: mode === "panel" ? "split" : this.controller.getPanelModeStyle(),
                isAmbient: this.controller.sharedShell?.isAmbient,
                isSplit: this.controller.sharedShell?.isSplit,
                isPanelOnly: mode === "panel",
                activePanel: this.controller.getActivePanel() || "navigate",
            };
        }
        
        const doc = win.document;
        
        doc.open();
        doc.write(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${mode === "canvas" ? "MolSysViewer Popout" : "MolSysViewer Panel"}</title>
  <style>
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #121216; }
    #molsysviewer-pop { position: relative; width: 100%; height: 100%; min-height: 300px; }
    #molsysviewer-loading { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: #fff; font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; font-size: 14px; letter-spacing: 0.2px; background: #121216; z-index: 1000; transition: opacity 240ms ease; }
    #molsysviewer-loading .spinner { width: 28px; height: 28px; border-radius: 999px; border: 3px solid rgba(255,255,255,0.12); border-top-color: rgba(255,255,255,0.45); animation: molsysviewer-spin 0.9s linear infinite; }
    @keyframes molsysviewer-spin { to { transform: rotate(360deg); } }
    .molsysviewer-controls { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "DejaVu Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; }
    .molsysviewer-controls button,
    .molsysviewer-controls input,
    .molsysviewer-controls select,
    .molsysviewer-controls textarea,
    .molsysviewer-controls span { font-family: inherit; }
    .molsysviewer-controls, .molsysviewer-controls * { user-select: none; -webkit-user-select: none; -moz-user-select: none; }
    .molsysviewer-traj-input::-webkit-inner-spin-button,
    .molsysviewer-traj-input::-webkit-outer-spin-button { -webkit-appearance: none !important; margin: 0 !important; }
    .molsysviewer-traj-input { -moz-appearance: textfield !important; appearance: none !important; color: rgba(255,255,255,0.9); background: rgba(40,40,40,0.6); }
    .molsysviewer-slider { background: transparent; height: 16px; border-radius: 999px; overflow: visible; }
    .molsysviewer-slider::-webkit-slider-runnable-track { background: rgba(200,200,200,0.35) !important; height: 16px; border-radius: 999px; }
    .molsysviewer-slider::-webkit-slider-thumb { -webkit-appearance: none !important; width: 16px; height: 16px; border-radius: 50% !important; background: rgba(0,0,0,0.5) !important; margin-top: 0px; }
  </style>
  ${resolvedModuleUrl ? `<link rel="modulepreload" href="${resolvedModuleUrl}">` : ""}
</head>
<body>
  <div id="molsysviewer-loading"><div class="spinner"></div><div>Loading...</div></div>
  <div id="molsysviewer-pop"></div>
</body>
</html>
        `);
        doc.close();

        try {
            const scriptEl = doc.createElement("script");
            scriptEl.type = "module";
            if (this.viewerModuleUrl) {
                scriptEl.textContent = `
                    (async () => {
                        try {
                            const module = await import("${resolvedModuleUrl ?? ""}");
                            const boot = module.bootPopup || (module.default && module.default.bootPopup);
                            if (boot) {
                                boot(module);
                            } else {
                                console.error("MolSysViewer Popout: bootPopup not found in module");
                            }
                        } catch (e) {
                            console.error("MolSysViewer Popout: Boot failed", e);
                        }
                    })();
                `;
            } else {
                const viewerJsSource = await this.resolveViewerJsSource();
                if (!viewerJsSource) {
                    throw new Error("No viewer source code provided to PopupHostManager");
                }
                const popWin = win as Window & typeof globalThis;
                const popBlob = new popWin.Blob([viewerJsSource], { type: "text/javascript" });
                const popBlobUrl = popWin.URL.createObjectURL(popBlob);

                console.log("[MolSysViewer Host] Injected viewer source to popup as:", popBlobUrl);

                scriptEl.textContent = `
                    (async () => {
                        try {
                            const module = await import("${popBlobUrl}");
                            const boot = module.bootPopup || (module.default && module.default.bootPopup);
                            if (boot) {
                                boot(module);
                            } else {
                                console.error("MolSysViewer Popout: bootPopup not found in module");
                            }
                        } catch (e) {
                            console.error("MolSysViewer Popout: Boot failed", e);
                        } finally {
                            URL.revokeObjectURL("${popBlobUrl}");
                        }
                    })();
                `;
            }
            doc.body.appendChild(scriptEl);

        } catch (err) {
            console.error("[MolSysViewer Host] Failed to inject viewer to popup:", err);
        }

        // Monitor closure
        const interval = window.setInterval(() => {
            if (mode === "canvas") {
                if (!this.popoutWin || this.popoutWin.closed) {
                    const current = this.channels.get("canvas");
                    this.popoutWin = null;
                    this.isReady = false;
                    this.channels.delete("canvas");
                    this.router.unregisterEndpoint(channel.popupEndpointId);
                    window.clearInterval(interval);
                    this.bootstrapping.delete("canvas");
                    this.bootstrapQueues.delete("canvas");
                    if (current?.popupEndpointId === channel.popupEndpointId) {
                        this.onEndpointClosed?.("canvas", channel.popupEndpointId);
                    }
                }
            } else {
                if (!this.panelWin || this.panelWin.closed) {
                    const current = this.channels.get("panel");
                    this.panelWin = null;
                    this.isPanelReady = false;
                    this.channels.delete("panel");
                    this.router.unregisterEndpoint(channel.popupEndpointId);
                    window.clearInterval(interval);
                    this.bootstrapping.delete("panel");
                    this.bootstrapQueues.delete("panel");
                    if (current?.popupEndpointId === channel.popupEndpointId) {
                        this.onEndpointClosed?.("panel", channel.popupEndpointId);
                    }
                    // Automatically restore host card when panel window is closed
                    if (this.controller) {
                        this.controller.restoreHostPanelState();
                    }
                }
            }
        }, 1000);
    }

    close(mode: "canvas" | "panel" = "canvas") {
        if (mode === "canvas") {
            if (this.popoutWin) {
                const channel = this.channels.get("canvas");
                this.popoutWin.close();
                this.popoutWin = null;
                this.isReady = false;
                this.channels.delete("canvas");
                if (channel) this.router.unregisterEndpoint(channel.popupEndpointId);
                this.bootstrapping.delete("canvas");
                this.bootstrapQueues.delete("canvas");
                if (channel) this.onEndpointClosed?.("canvas", channel.popupEndpointId);
            }
        } else {
            if (this.panelWin) {
                const channel = this.channels.get("panel");
                this.panelWin.close();
                this.panelWin = null;
                this.isPanelReady = false;
                this.channels.delete("panel");
                if (channel) this.router.unregisterEndpoint(channel.popupEndpointId);
                this.bootstrapping.delete("panel");
                this.bootstrapQueues.delete("panel");
                if (channel) this.onEndpointClosed?.("panel", channel.popupEndpointId);
            }
        }
    }

    dispose(): void {
        this.close("canvas");
        this.close("panel");
        this.channels.clear();
    }

    /**
     * Deliver to exactly one popup endpoint.
     *
     * `send` fans out to every open popup, which is right for shared scene
     * projections but wrong for anything endpoint-specific: a canvas bootstrap
     * carries molecular data, and a panel popup must never receive it. Returns
     * false when that endpoint is not open.
     */
    sendTo(mode: PopupMode, type: string, data: any): boolean {
        const direction: RuntimeDirection =
            type === "molsysviewer-sync-camera" ? "event" : "projection";
        const target = mode === "canvas" ? this.popoutWin : this.panelWin;
        const ready = mode === "canvas" ? this.isReady : this.isPanelReady;
        const channel = this.channels.get(mode);
        if (!ready || !target || target.closed || !channel) return false;
        if (
            this.bootstrapping.has(mode)
            && type !== "molsysviewer-initial-sync"
            && type !== "molsysviewer-structure-data"
        ) {
            this.bootstrapQueues.get(mode)?.push({ type, data });
            return true;
        }
        try {
            this.postToPopup(target, channel, type, data, direction);
            return true;
        } catch (e) {
            console.warn(`[MolSysViewer Host] ${mode} popup message failed`, e);
            return false;
        }
    }

    send(type: string, data: any) {
        this.sendTo("canvas", type, data);
        this.sendTo("panel", type, data);
    }

    receive(event: MessageEvent): {
        type: string;
        data: unknown;
        envelope: RuntimeEnvelope;
        channel: PopupChannelIdentity;
    } | null {
        const mode =
            event.source === this.popoutWin ? "canvas"
            : event.source === this.panelWin ? "panel"
            : null;
        if (!mode) return null;
        const channel = this.channels.get(mode);
        const expectedSource = mode === "canvas" ? this.popoutWin : this.panelWin;
        if (!channel || !expectedSource) return null;
        const wire = decodePopupEvent(
            event,
            expectedSource,
            channel,
            new Set([channel.popupEndpointId]),
        );
        if (!wire) return null;
        const routed = this.router.route(wire.envelope);
        if (routed.status !== "accepted") return null;
        // Same guard inbound: a popup cannot invent an action, nor send one in a
        // direction the manifest does not grant it.
        if (!popupActionAllows(wire.envelope.action, wire.envelope.direction)) {
            this.onContractRejection?.({
                seam: "popup-host-inbound",
                reason: "undeclared-popup-action",
                detail: `${wire.envelope.action}:${wire.envelope.direction}`,
            });
            console.warn(
                `[MolSysViewer Host] refused popup action ${wire.envelope.action} `
                + `as ${wire.envelope.direction}: not declared in runtime_actions.json`,
            );
            return null;
        }
        return {
            type: routed.envelope.action,
            data: routed.envelope.payload,
            envelope: routed.envelope,
            channel,
        };
    }

    private targetOrigin(): string {
        const origin = window.location?.origin;
        return origin && origin !== "null" ? origin : "*";
    }

    private createRouter(): RuntimeMessageRouter {
        const router = new RuntimeMessageRouter(this.viewerId, this.sessionId);
        router.registerEndpoint({ endpointId: this.authorityEndpointId, role: "python" });
        router.registerEndpoint({ endpointId: this.hostEndpointId, role: "widget-host" });
        return router;
    }

    private postToPopup(
        target: Window,
        channel: PopupChannelIdentity,
        action: string,
        payload: unknown,
        direction: RuntimeDirection = "projection",
    ): void {
        const envelope: RuntimeEnvelope = {
            protocolVersion: RUNTIME_PROTOCOL_VERSION,
            viewerId: this.viewerId,
            sessionId: this.sessionId,
            endpointId:
                direction === "projection"
                    ? this.authorityEndpointId
                    : this.hostEndpointId,
            targetEndpointId: channel.popupEndpointId,
            messageId: `${this.hostEndpointId}:${++this.messageCounter}`,
            direction,
            action,
            payload,
        };
        // The popup channel now has the guard the widget seam already had: an
        // action nobody declared, or one travelling in a direction it may not,
        // is refused instead of being relayed on trust.
        if (!popupActionAllows(action, direction)) {
            this.onContractRejection?.({
                seam: "popup-host-outbound",
                reason: "undeclared-popup-action",
                detail: `${action}:${direction}`,
            });
            throw new Error(
                `Popup action ${action} may not travel as ${direction} `
                + "(not declared in runtime_actions.json)",
            );
        }
        const routed = this.router.route(envelope);
        if (routed.status !== "accepted") {
            const detail =
                routed.status === "rejected"
                    ? routed.detail
                    : `duplicate message ${routed.envelope.messageId}`;
            throw new Error(`Popup projection rejected: ${detail}`);
        }
        target.postMessage(encodePopupMessage(channel, envelope), this.targetOrigin());
    }
}
