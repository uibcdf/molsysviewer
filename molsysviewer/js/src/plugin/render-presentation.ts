import { Renderer } from "molstar/lib/mol-gl/renderer";
import { ImagePass } from "molstar/lib/mol-canvas3d/passes/image";
import type { ICamera } from "molstar/lib/mol-canvas3d/camera";
import type { Scene } from "molstar/lib/mol-gl/scene";
import type { WebGLContext } from "molstar/lib/mol-gl/webgl/context";

type Presentation = { camera: ICamera; present(camera: ICamera, scene: Scene): void };
const presentations = new WeakMap<WebGLContext, Set<Presentation>>();
const attached = new WeakSet<object>();

/** Synchronous presentation before Mol* consumes a camera/scene for any pass.
 * The owning bundle installs this once, before it creates native renderers.
 * Empty weak registries retain no viewer, scene, subscription or timing owner.
 */
export function attachRenderPresentation(renderer: Pick<Renderer, "update">, context: WebGLContext): void {
    if (attached.has(renderer)) return;
    attached.add(renderer);
    const update = renderer.update;
    renderer.update = (...args) => {
        const [camera, scene] = args;
        for (const entry of presentations.get(context) ?? []) entry.present(camera, scene);
        update.apply(renderer, args);
    };
}

export function registerRenderPresentation(context: WebGLContext, camera: ICamera,
    present: Presentation["present"]): () => void {
    let entries = presentations.get(context);
    if (!entries) { entries = new Set(); presentations.set(context, entries); }
    const entry = { camera, present };
    entries.add(entry);
    return () => {
        entries.delete(entry);
        if (!entries.size && presentations.get(context) === entries) presentations.delete(context);
    };
}

// Mol* 5.13.1 uses this boundary for normal drawing, picking, image passes and
// illumination. Forward its complete native tuple, including Frame. Per-draw
// asynchronous state updates cannot provide this ordering. The wrapper stays
// local to this runtime bundle.
const createRenderer = Renderer.create;
Renderer.create = (...args) => {
    const renderer = createRenderer(...args);
    attachRenderPresentation(renderer, args[0]);
    return renderer;
};

const renderImage = ImagePass.prototype.render;
ImagePass.prototype.render = async function (...args) {
    try { return await renderImage.apply(this, args); }
    finally {
        // An offscreen image may use another camera. Restore live loci and GPU
        // transforms before returning, including when image rendering fails.
        const pass = this as unknown as { webgl: WebGLContext; scene: Scene };
        for (const entry of presentations.get(pass.webgl) ?? []) entry.present(entry.camera, pass.scene);
    }
};
