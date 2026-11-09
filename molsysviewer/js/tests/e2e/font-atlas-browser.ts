import { FontAtlas } from "molstar/lib/mol-geo/geometry/text/font-atlas";
import { createContext } from "molstar/lib/mol-gl/webgl/context";
import { readAlphaTexture } from "molstar/lib/mol-gl/compute/util";
import { installFontAtlasUploads } from "../../src/plugin/font-atlas-uploads";

/** Real native writer, textures and GPU read-back; no fabricated image/GL result. */
export async function checkFontAtlasResourceLifecycle(adapt = true) {
    const assert = (condition: unknown, message: string) => { if (!condition) throw new Error(message); };
    const canvas = document.createElement("canvas"); canvas.width = canvas.height = 32;
    document.body.append(canvas);
    const gl = canvas.getContext("webgl2");
    if (!gl) throw new Error("Font atlas receiving requires WebGL2.");
    const context = createContext(gl), factory = context.resources.texture, reset = context.resources.reset;
    const release = adapt ? installFontAtlasUploads(context) : () => {};
    const tracked = new Set<object>(); let uploads = 0;
    const image = gl.texImage2D, sub = gl.texSubImage2D;
    (gl as any).texImage2D = (...args: any[]) => { if (tracked.has(args[8])) uploads++; return (image as any).apply(gl, args); };
    (gl as any).texSubImage2D = (...args: any[]) => { if (tracked.has(args[8])) uploads++; return (sub as any).apply(gl, args); };
    const changes: string[] = [];
    try {
        const atlas = new FontAtlas({ fontQuality: 0 });
        for (const char of "12.34 Å") atlas.get(char);
        tracked.add(atlas.texture.array);
        const first = context.resources.texture("image-uint8", "alpha", "ubyte", "linear");
        const second = context.resources.texture("image-uint8", "alpha", "ubyte", "linear");
        const pixelsMatch = (texture: typeof first, expected: Uint8Array) => {
            const pixels = readAlphaTexture(context, texture).array;
            for (let i = 0; i < expected.length; i++) if (pixels[4 * i + 3] !== expected[i]) {
                throw new Error(`Native GPU atlas differs at pixel ${i}.`);
            }
            assert(gl.getError() === gl.NO_ERROR, "Native GPU read-back must have no GL error.");
        };
        first.load(atlas.texture);
        const initial = uploads;
        first.load(atlas.texture);
        assert(uploads === initial, "An unchanged native atlas must not be uploaded again.");
        changes.push("unchanged image reused");
        const mapped = Object.keys(atlas.mapped).length;
        atlas.get("Ж");
        assert(Object.keys(atlas.mapped).length === mapped + 1, "The new native glyph must really be written.");
        first.load(atlas.texture);
        assert(uploads === initial + 1, "A newly written glyph must reach the GPU.");
        pixelsMatch(first, atlas.texture.array);
        changes.push("new glyph and every GPU pixel received");
        second.load(atlas.texture);
        const shared = uploads;
        second.load(atlas.texture); first.load(atlas.texture);
        assert(uploads === shared, "Both native textures must retain their own uploaded revision.");
        atlas.get("Ω"); first.load(atlas.texture); second.load(atlas.texture);
        assert(uploads === shared + 2, "Both consumers must receive another shared-atlas glyph.");
        pixelsMatch(second, atlas.texture.array);
        changes.push("shared image consumers remain coherent");
        const other = new FontAtlas({ fontQuality: 1, fontWeight: "bold" });
        for (const char of "Changed font") other.get(char);
        tracked.add(other.texture.array);
        const beforeStyle = uploads;
        first.load(other.texture);
        assert(uploads === beforeStyle + 1, "A new font/quality/size must be uploaded.");
        pixelsMatch(first, other.texture.array);
        changes.push("font style and quality changes received");
        first.define(other.texture.width + 1, other.texture.height);
        const resized = uploads; first.load(other.texture);
        assert(uploads === resized + 1, "An explicit allocation must invalidate the reused contents.");
        first.reset(); const restarted = uploads; first.load(other.texture);
        assert(uploads === restarted + 1, "An individual native reset must invalidate the uploaded revision.");
        context.handleContextRestored(); const allReset = uploads; first.load(other.texture);
        assert(uploads === allReset + 1, "The native resource reset must invalidate all uploaded revisions.");
        pixelsMatch(first, other.texture.array);
        changes.push("resize and native context reset received");
        const explicitSub = uploads; first.load(other.texture, true);
        assert(uploads === explicitSub + 1, "Explicit sub-image writes must always reach Mol*.");
        const unknown = { width: 2, height: 2, array: new Uint8Array([1, 2, 3, 4]) };
        tracked.add(unknown.array); const fallback = uploads;
        first.load(unknown); first.load(unknown);
        assert(uploads === fallback + 2, "Unregistered images must keep native loading semantics.");
        first.load(other.texture);
        changes.push("unknown and explicit writes retain native fallback");
        const extension = gl.getExtension("WEBGL_lose_context");
        assert(extension, "Physical context restoration requires WEBGL_lose_context.");
        const lost = new Promise<void>(resolve => canvas.addEventListener("webglcontextlost", event => {
            event.preventDefault(); context.setContextLost(); resolve();
        }, { once: true }));
        extension!.loseContext(); await lost;
        await new Promise<void>((resolve, reject) => {
            const deadline = setTimeout(() => reject(new Error("Native context did not restore.")), 5000);
            canvas.addEventListener("webglcontextrestored", () => {
                try { context.handleContextRestored(); clearTimeout(deadline); resolve(); }
                catch (error) { clearTimeout(deadline); reject(error); }
            }, { once: true });
            setTimeout(() => extension!.restoreContext(), 0);
        });
        const restored = uploads; first.load(other.texture);
        assert(uploads === restored + 1, "A physical context restore must not reuse an old GPU generation.");
        pixelsMatch(first, other.texture.array);
        changes.push("physical context loss/restoration received");
        const beforeDestroy = context.stats.resourceCounts.texture;
        first.destroy(); second.destroy();
        assert(context.stats.resourceCounts.texture === beforeDestroy - 2, "The native owner must release both GPU textures.");
        release(); release();
        assert(context.resources.texture === factory && context.resources.reset === reset, "Disposal must restore native factory/reset exactly.");
        changes.push("native resource ownership and idempotent disposal received");
        return { changes, atlasDimensions: [atlas.texture.width, atlas.texture.height] };
    } finally {
        release(); context.destroy(); canvas.remove();
    }
}
