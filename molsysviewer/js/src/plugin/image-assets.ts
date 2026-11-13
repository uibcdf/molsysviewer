import type { ImagePass } from "molstar/lib/mol-canvas3d/passes/image";

type Texture = { getWidth(): number; getHeight(): number };
type Smaa = { supported: boolean; weightsRenderable?: { values: {
    tArea: { ref: { value: Texture } }; tSearch: { ref: { value: Texture } };
} } };

/** #382: a read-only private seam, qualified against exact native source bytes
 * by the build plugin. Mol* exposes no readiness promise for these uploads.
 * Wait for the real GPU textures; never render a warm-up or reduce quality.
 */
export async function waitForImageAssets(pass: ImagePass, signals: readonly AbortSignal[] = [], timeoutMs = 5000): Promise<void> {
    const aborted = () => signals.some(signal => signal.aborted);
    const abortError = () => new DOMException("Image asset loading cancelled.", "AbortError");
    if (aborted()) throw abortError();
    if (pass.props.postprocessing.antialiasing.name !== "smaa") return;
    const smaa = (pass as unknown as { drawPass?: { antialiasing?: { smaa?: Smaa } } }).drawPass?.antialiasing?.smaa;
    if (!smaa || typeof smaa.supported !== "boolean") throw new Error("Unqualified native SMAA image-asset boundary (#382).");
    if (!smaa.supported) return; // Preserve the native unsupported-renderer behavior.
    const values = smaa.weightsRenderable?.values;
    const textures = [values?.tArea?.ref.value, values?.tSearch?.ref.value];
    if (textures.some(texture => !texture || typeof texture.getWidth !== "function" || typeof texture.getHeight !== "function")) {
        throw new Error("Unqualified native SMAA texture boundary (#382).");
    }
    // Native textures start with 1x1 placeholders, not a zero-sized sentinel.
    // These are the qualified 5.13.1 area/search images, observed after upload.
    const dimensions = [[160, 560], [66, 33]];
    const ready = () => textures.every((texture, index) => texture!.getWidth() === dimensions[index][0]
        && texture!.getHeight() === dimensions[index][1]);
    if (ready()) return;
    await new Promise<void>((resolve, reject) => {
        let poll: ReturnType<typeof setTimeout> | undefined, deadline: ReturnType<typeof setTimeout> | undefined;
        let settled = false;
        const finish = (error?: Error) => {
            if (settled) return; settled = true;
            clearTimeout(poll); clearTimeout(deadline);
            for (const signal of signals) signal.removeEventListener("abort", cancel);
            if (error) reject(error); else resolve();
        };
        const cancel = () => finish(abortError());
        const check = () => {
            try {
                if (aborted()) { cancel(); return; }
                if (ready()) { finish(); return; }
                poll = setTimeout(check, 16);
            } catch (error) { finish(error instanceof Error ? error : new Error("Image assets could not be inspected.")); }
        };
        for (const signal of signals) signal.addEventListener("abort", cancel, { once: true });
        deadline = setTimeout(() => finish(new Error("SMAA image assets did not finish loading; PNG was not rendered.")), timeoutMs);
        check();
    });
}
