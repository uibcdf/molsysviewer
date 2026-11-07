import type { Canvas3D } from "molstar/lib/mol-canvas3d/canvas3d";

/** Read synchronously inside a fresh completed draw, before later state advances.
 * The reader must not change the scene or return an asynchronous operation.
 */
export async function readCanvasDraw<T>(canvas: Canvas3D, read: () => T, timeoutMs = 30000,
    signal?: AbortSignal): Promise<T> {
    return new Promise<T>((resolve, reject) => {
        let requested = false;
        let settled = false;
        let subscription: { unsubscribe(): void } | undefined;
        let timer: ReturnType<typeof setTimeout> | undefined;
        const finish = (outcome: { value: T } | { error: unknown }) => {
            if (settled) return;
            settled = true;
            if (timer !== undefined) clearTimeout(timer);
            subscription?.unsubscribe();
            signal?.removeEventListener("abort", abort);
            if ("error" in outcome) reject(outcome.error); else resolve(outcome.value);
        };
        const abort = () => finish({ error: new DOMException("Canvas draw wait cancelled.", "AbortError") });
        if (signal?.aborted) { abort(); return; }
        signal?.addEventListener("abort", abort, { once: true });
        timer = setTimeout(() => finish({ error: new Error("Canvas did not finish drawing.") }), timeoutMs);
        try {
            subscription = canvas.didDraw.subscribe(() => {
                if (!requested || settled) return;
                try { finish({ value: read() }); } catch (error) { finish({ error }); }
            });
            if (settled) { subscription.unsubscribe(); return; }
            requested = true;
            canvas.requestDraw();
        } catch (error) {
            finish({ error });
        }
    });
}

/** Request and await a fresh completed draw, ignoring the subject's replayed frame. */
export async function waitForCanvasDraw(canvas: Canvas3D, timeoutMs = 30000, signal?: AbortSignal): Promise<void> {
    await readCanvasDraw(canvas, () => undefined, timeoutMs, signal);
}
