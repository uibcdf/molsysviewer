import type { Canvas3D } from "molstar/lib/mol-canvas3d/canvas3d";

/** Request and await a fresh completed draw, ignoring the subject's replayed frame. */
export async function waitForCanvasDraw(canvas: Canvas3D, timeoutMs = 30000, signal?: AbortSignal): Promise<void> {
    await new Promise<void>((resolve, reject) => {
        let requested = false;
        let settled = false;
        let subscription: { unsubscribe(): void } | undefined;
        let timer: ReturnType<typeof setTimeout> | undefined;
        const finish = (error?: unknown) => {
            if (settled) return;
            settled = true;
            if (timer !== undefined) clearTimeout(timer);
            subscription?.unsubscribe();
            signal?.removeEventListener("abort", abort);
            if (error !== undefined) reject(error); else resolve();
        };
        const abort = () => finish(new DOMException("Canvas draw wait cancelled.", "AbortError"));
        if (signal?.aborted) { abort(); return; }
        signal?.addEventListener("abort", abort, { once: true });
        timer = setTimeout(() => finish(new Error("Canvas did not finish drawing.")), timeoutMs);
        try {
            subscription = canvas.didDraw.subscribe(() => {
                if (requested) finish();
            });
            if (settled) { subscription.unsubscribe(); return; }
            requested = true;
            canvas.requestDraw();
        } catch (error) {
            finish(error);
        }
    });
}
