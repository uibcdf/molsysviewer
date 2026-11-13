import { createSecureRuntimeId } from "../messages/popup-channel";

export type StudioImageOptions = { scale: number; transparent: boolean; preset: string };
export type StudioImageResult = {
    op: "studio_action_result"; action: "download_image"; domain: "export";
    request_id: string; target_endpoint_id: string; ok: boolean;
    image_data_uri?: string; error_message?: string;
};

export function isStudioImageRequest(message: any): boolean {
    return message?.op === "request_image_export" && typeof message.studio_image_request_id === "string";
}

export function isPngDataUri(value: unknown): value is string {
    return typeof value === "string" && value.startsWith("data:image/png;base64,iVBORw0KGgo");
}

type PendingImage = { owner: string; renderer: string; uiRequest: string; request: Record<string, unknown>;
    timer: ReturnType<typeof setTimeout> };

/** Widget-owned PNG routing. A panel can never choose its renderer or recipient. */
export class StudioImageExports {
    private readonly pending = new Map<string, PendingImage>();
    private closed = false;

    constructor(private readonly host: {
        ownerIsLive(owner: string): boolean;
        rendererIsLive(renderer: string): boolean;
        dispatch(renderer: string, request: Record<string, unknown>): boolean;
        deliver(owner: string, result: StudioImageResult): void;
    }, private readonly timeoutMs = 180_000) {}

    handle(owner: string, renderer: string | undefined, message: any): boolean {
        if (message?.event !== "interaction_context_action"
            || !["download_image", "cancel_image_download"].includes(message.action)) return false;
        const id = message.request_id;
        if (this.closed || typeof id !== "string" || !id || id.length > 160 || !this.host.ownerIsLive(owner)) return true;
        if (message.action === "cancel_image_download") {
            for (const [key, pending] of this.pending) if (pending.owner === owner && pending.uiRequest === id) {
                this.finish(key, "PNG export cancelled.", true);
                break;
            }
            return true;
        }
        const fail = (error: string) => this.deliver(owner, id, { ok: false, error_message: error });
        if ([...this.pending.values()].some(pending => pending.owner === owner)) {
            fail("A PNG export from this panel is already running."); return true;
        }
        if (!renderer || !this.host.rendererIsLive(renderer)) {
            fail("The originating canvas is unavailable. Open Studio from a live canvas and try again."); return true;
        }
        const scale = message.scale, preset = message.preset;
        if (typeof scale !== "number" || !Number.isFinite(scale) || scale <= 0
            || typeof message.transparent !== "boolean" || typeof preset !== "string") {
            fail("The requested PNG settings are invalid."); return true;
        }
        if (this.pending.size >= 32) { fail("Too many image exports are pending. Try again after one finishes."); return true; }
        const key = createSecureRuntimeId("studio-image");
        const request = { op: "request_image_export", request_id: key, capture_revision: createSecureRuntimeId("image-revision"),
            studio_image_request_id: key, scale, transparent: message.transparent, preset };
        const timer = setTimeout(() => this.finish(key, "PNG export timed out. Please try again.", true), this.timeoutMs);
        this.pending.set(key, { owner, renderer, uiRequest: id, request, timer });
        try {
            if (!this.host.dispatch(renderer, request)) this.finish(key, "The originating canvas is unavailable.", true);
        } catch { this.finish(key, "PNG export could not reach its originating canvas.", true); }
        return true;
    }

    receive(renderer: string, message: any): boolean {
        if (message?.event !== "image_export" || typeof message.studio_image_request_id !== "string") return false;
        const key = message.studio_image_request_id, pending = this.pending.get(key);
        // Private replies, including late or forged correlations, never become
        // unrelated Python image replies or downloads in another endpoint.
        if (!pending || pending.renderer !== renderer || message.request_id !== key
            || message.capture_revision !== pending.request.capture_revision) return true;
        clearTimeout(pending.timer); this.pending.delete(key);
        if (isPngDataUri(message.data_uri)) this.deliver(pending.owner, pending.uiRequest,
            { ok: true, image_data_uri: message.data_uri });
        else this.deliver(pending.owner, pending.uiRequest, { ok: false,
            error_message: typeof message.message === "string" ? message.message : "PNG rendering returned no valid image." });
        return true;
    }

    closeEndpoint(endpoint: string): void {
        for (const [key, pending] of this.pending) if (pending.owner === endpoint || pending.renderer === endpoint) {
            this.finish(key, "The PNG export window or its originating canvas closed.", true);
        }
    }

    dispose(): void {
        if (this.closed) return;
        this.closed = true;
        for (const key of this.pending.keys()) this.finish(key, "PNG export cancelled.", true);
    }

    private finish(key: string, error: string, cancel: boolean) {
        const pending = this.pending.get(key);
        if (!pending) return;
        clearTimeout(pending.timer); this.pending.delete(key);
        if (cancel) try {
            this.host.dispatch(pending.renderer, { ...pending.request, op: "cancel_visual_state" });
        } catch { /* Retired endpoints may already have released their captures. */ }
        this.deliver(pending.owner, pending.uiRequest, { ok: false, error_message: error });
    }

    private deliver(owner: string, request: string, result: Pick<StudioImageResult, "ok" | "image_data_uri" | "error_message">) {
        if (this.closed || !this.host.ownerIsLive(owner)) return;
        this.host.deliver(owner, { ...result, op: "studio_action_result", action: "download_image", domain: "export",
            request_id: request, target_endpoint_id: owner });
    }
}
