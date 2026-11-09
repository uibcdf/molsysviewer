import { FontAtlas } from "molstar/lib/mol-geo/geometry/text/font-atlas";
import type { WebGLContext } from "molstar/lib/mol-gl/webgl/context";

// Mol* 5.4.1 appends atlas pixels through this public writer, but its Text
// geometry advances tFont even when only glyph positions change. Keep a weak
// content token at the writer, not a copy/hash of its multi-megabyte image.
// This seam is local to the owning bundle, before any controller creates fonts.
const fontContent = new WeakMap<object, object>();
const getGlyph = FontAtlas.prototype.get;
FontAtlas.prototype.get = function (this: FontAtlas, char: string) {
    const previous = this.mapped[char];
    try {
        const glyph = getGlyph.call(this, char);
        if (this.mapped[char] && this.mapped[char] !== previous) fontContent.set(this.texture, {});
        return glyph;
    } catch (error) {
        // A failed native writer is never evidence that its pixels stayed put.
        fontContent.delete(this.texture);
        throw error;
    }
};

/** Consume the native atlas writer while retaining native GPU resource ownership.
 * Unknown images, sub-image writes and retired/lost resources always use Mol*.
 * #344 owns this 5.4.1 compatibility seam; #115 owns its eventual retirement.
 */
export function installFontAtlasUploads(context: WebGLContext): () => void {
    const resources = context.resources, create = resources.texture, reset = resources.reset;
    let epoch = 0, disposed = false;
    const invalidate = () => { epoch++; };
    const restored = context.contextRestored.subscribe(invalidate);
    const resetResources: typeof reset = () => { invalidate(); return reset.call(resources); };
    const createTexture: typeof create = (...args) => {
        const texture = create.apply(resources, args);
        if (args[0] !== "image-uint8" || args[1] !== "alpha" || args[2] !== "ubyte") return texture;
        let retired = false;
        let uploaded: { image: object; array: object; content: object; epoch: number;
            width: number; height: number; filter: unknown; flipY: unknown } | undefined;
        return {
            ...texture,
            load(image, sub = false) {
                const content = fontContent.get(image);
                const array = "array" in image ? image.array : undefined;
                if (!disposed && !retired && !context.isContextLost && !sub && content && array
                    && uploaded?.image === image && uploaded.array === array && uploaded.content === content
                    && uploaded.epoch === epoch && uploaded.width === image.width && uploaded.height === image.height
                    && uploaded.filter === ("filter" in image ? image.filter : undefined)
                    && uploaded.flipY === ("flipY" in image ? image.flipY : undefined)
                    && texture.getWidth() === image.width && texture.getHeight() === image.height) return;
                uploaded = undefined;
                texture.load(image, sub);
                if (!disposed && !retired && !context.isContextLost && !sub && content && array) uploaded = {
                    image, array, content, epoch, width: image.width, height: image.height,
                    filter: "filter" in image ? image.filter : undefined,
                    flipY: "flipY" in image ? image.flipY : undefined,
                };
            },
            define(...dimensions) { uploaded = undefined; texture.define(...dimensions); },
            reset() { uploaded = undefined; texture.reset(); },
            destroy() { uploaded = undefined; retired = true; texture.destroy(); },
        };
    };
    resources.texture = createTexture;
    resources.reset = resetResources;
    return () => {
        if (disposed) return;
        disposed = true;
        restored.unsubscribe();
        if (resources.texture === createTexture) resources.texture = create;
        if (resources.reset === resetResources) resources.reset = reset;
    };
}
