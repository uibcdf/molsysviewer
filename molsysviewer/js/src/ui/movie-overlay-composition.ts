/** Detached vector overlays. No arbitrary HTML, external resources or UI chrome. */
export type OverlayId = { kind: "trajectory_plot" | "colour_legend"; tag: string };
export type OverlayRect = { x: number; y: number; width: number; height: number };
export type MovieSvgOverlay = OverlayId & { bounds: OverlayRect; svg: string;
    rendering: { opacity: number; view_box: { width: number; height: number } } };
export type MovieOverlaySnapshot = {
    schema: "molsysviewer.movie_composition@1";
    viewport: { width: number; height: number; unit: "css-px" };
    layers: Array<MovieSvgOverlay & { output: OverlayRect }>;
};
const ns = "http://www.w3.org/2000/svg";
export class MovieOverlayError extends Error {
    constructor(name: "MovieOverlayUnavailable" | "MovieOverlayChanged" | "MovieOverlayLimit", message: string) {
        super(message); this.name = name;
    }
}
export const svgNode = (name: string, attributes: Record<string, string | number> = {}, text?: string): SVGElement => {
    const node = document.createElementNS(ns, name);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
    if (text !== undefined) node.textContent = text;
    return node;
};
export function svgDocument(width: number, height: number) {
    return svgNode("svg", { xmlns: ns, width, height, viewBox: `0 0 ${width} ${height}` });
}
export function overlayBounds(element: Element, host: Element): OverlayRect {
    const rect = element.getBoundingClientRect(), viewport = host.getBoundingClientRect();
    if (element.ownerDocument !== host.ownerDocument || !element.isConnected || rect.width <= 0 || rect.height <= 0
        || getComputedStyle(element).visibility === "hidden") {
        throw new MovieOverlayError("MovieOverlayUnavailable", "A visible Movie plot/legend must be expanded in its canvas; return detached cards before exporting.");
    }
    return { x: rect.left - viewport.left, y: rect.top - viewport.top, width: rect.width, height: rect.height };
}
export function positionOverlay(bounds: OverlayRect, viewport: { width: number; height: number }, width: number, height: number): OverlayRect {
    if (![...Object.values(bounds), viewport.width, viewport.height, width, height].every(Number.isFinite)
        || bounds.width <= 0 || bounds.height <= 0 || viewport.width <= 0 || viewport.height <= 0 || width <= 0 || height <= 0
        || bounds.x < -1 || bounds.y < -1 || bounds.x + bounds.width > viewport.width + 1 || bounds.y + bounds.height > viewport.height + 1) {
        throw new MovieOverlayError("MovieOverlayUnavailable", "A Movie overlay is outside its viewer or has invalid dimensions.");
    }
    const scale = Math.min(width / viewport.width, height / viewport.height);
    return { x: (bounds.x + bounds.width / 2) / viewport.width * width - bounds.width * scale / 2,
        y: (bounds.y + bounds.height / 2) / viewport.height * height - bounds.height * scale / 2,
        width: bounds.width * scale, height: bounds.height * scale };
}
const allowedElements = new Set(["svg", "g", "path", "polyline", "line", "rect", "text", "tspan", "title"]);
const allowedAttributes = new Set(["x", "y", "x1", "x2", "y1", "y2", "width", "height", "viewBox", "preserveAspectRatio",
    "d", "points", "fill", "stroke", "stroke-width", "stroke-dasharray", "opacity", "font-size", "font-weight", "text-anchor", "transform"]);
/** Copy only the primitives produced by our plot renderer, retaining raw-value titles. */
export function plotSvgForMovie(source: Element): SVGElement {
    if (!allowedElements.has(source.localName)) throw new Error("Unsupported primitive in Movie plot SVG.");
    const clone = svgNode(source.localName);
    for (const attr of Array.from(source.attributes)) {
        if (!allowedAttributes.has(attr.name)) continue;
        if ((attr.name === "fill" || attr.name === "stroke") && !/^(#[0-9a-f]{3,8}|none|transparent|rgba?\([\d.,% ]+\))$/i.test(attr.value)) {
            throw new Error("Unsupported Movie plot colour.");
        }
        clone.setAttribute(attr.name, attr.value);
    }
    if (source.localName === "text") clone.setAttribute("font-family", "sans-serif");
    for (const child of Array.from(source.childNodes)) {
        if (child.nodeType === 3) clone.appendChild(document.createTextNode(child.textContent ?? ""));
        else if (child.nodeType === 1) clone.appendChild(plotSvgForMovie(child as Element));
    }
    return clone;
}
export function overlaySnapshot(viewport: { width: number; height: number }, overlays: MovieSvgOverlay[], width: number, height: number): MovieOverlaySnapshot {
    if (overlays.length > 32 || overlays.reduce((n, row) => n + new TextEncoder().encode(row.svg).byteLength, 0) > 8 * 1024 * 1024) {
        throw new MovieOverlayError("MovieOverlayLimit", "Movie composition exceeds 32 overlays or 8 MiB of vector content.");
    }
    return { schema: "molsysviewer.movie_composition@1", viewport: { ...viewport, unit: "css-px" },
        layers: overlays.map(row => ({ ...row, output: positionOverlay(row.bounds, viewport, width, height) })) };
}
export function overlayDescriptor(snapshot: MovieOverlaySnapshot) {
    return { schema: snapshot.schema, viewport: snapshot.viewport, placement: "normalized-centres-uniform-scale@1", unit: "px",
        layers: snapshot.layers.map(({ kind, tag, bounds, output, rendering }) => ({ kind, tag, bounds, output, rendering })) };
}
export async function drawMovieOverlays(context: CanvasRenderingContext2D, snapshot: MovieOverlaySnapshot, signal: AbortSignal) {
    for (const layer of snapshot.layers) {
        if (signal.aborted) throw new DOMException("Movie composition cancelled.", "AbortError");
        const parsed = new DOMParser().parseFromString(layer.svg, "image/svg+xml");
        if (parsed.querySelector("parsererror")) throw new Error("Movie overlay SVG is invalid.");
        // Rasterize vectors at the requested output resolution, not the screen's DPI.
        parsed.documentElement.setAttribute("width", String(Math.max(1, Math.ceil(layer.output.width))));
        parsed.documentElement.setAttribute("height", String(Math.max(1, Math.ceil(layer.output.height))));
        const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(parsed.documentElement)], { type: "image/svg+xml" }));
        const image = new Image();
        let abort: (() => void) | undefined;
        try {
            await new Promise<void>((resolve, reject) => {
                abort = () => { image.src = ""; reject(new DOMException("Movie composition cancelled.", "AbortError")); };
                signal.addEventListener("abort", abort, { once: true });
                image.onload = () => resolve(); image.onerror = () => reject(new Error("Movie overlay could not be rasterized."));
                image.src = url;
                if (signal.aborted) abort();
            });
            if (signal.aborted) throw new DOMException("Movie composition cancelled.", "AbortError");
            context.drawImage(image, layer.output.x, layer.output.y, layer.output.width, layer.output.height);
        } finally {
            if (abort) signal.removeEventListener("abort", abort);
            image.onload = image.onerror = null; URL.revokeObjectURL(url);
        }
    }
}
