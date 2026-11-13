import { FontAtlas } from "molstar/lib/mol-geo/geometry/text/font-atlas";

/** Observe original native allocations; do not replace glyphs or renderer data. */
export function inspectFontAtlas(props?: ConstructorParameters<typeof FontAtlas>[0]) {
    const atlas = new FontAtlas(props);
    for (const char of "H₂O Å αβ") atlas.get(char);
    return {
        props: atlas.props, width: atlas.texture.width, height: atlas.texture.height,
        array_bytes: atlas.texture.array.byteLength,
        glyphs: Object.keys(atlas.mapped),
    };
}
