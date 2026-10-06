import type { Canvas3D } from "molstar/lib/mol-canvas3d/canvas3d";

/** Request and await a fresh completed draw, ignoring the subject's replayed frame. */
export async function waitForCanvasDraw(canvas: Canvas3D, timeoutMs = 30000): Promise<void> {
    await new Promise<void>((resolve, reject) => {
        let requested = false;
        const timer = setTimeout(() => {
            subscription.unsubscribe();
            reject(new Error("Canvas did not finish drawing."));
        }, timeoutMs);
        const subscription = canvas.didDraw.subscribe(() => {
            if (!requested) return;
            clearTimeout(timer);
            subscription.unsubscribe();
            resolve();
        });
        requested = true;
        canvas.requestDraw();
    });
}
