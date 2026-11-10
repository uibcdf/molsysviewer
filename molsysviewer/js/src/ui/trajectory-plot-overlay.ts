import { FloatingDataCard } from "./floating-data-card";

export interface TrajectoryPlotSeries {
    label: string;
    values: number[];
    color?: number;
    observation?: Record<string, unknown>;
    observation_rows?: number[];
    observation_count?: number;
}

export interface TrajectoryPlotEvent {
    frame: number;
    label?: string;
    color?: number;
}

export interface TrajectoryPlotOptions {
    cards?: TrajectoryPlotOptions[];
    tag?: string;
    visible?: boolean;
    series?: TrajectoryPlotSeries[];
    n_frames?: number;
    x?: number[];
    events?: TrajectoryPlotEvent[];
    x_label?: string;
    y_label?: string;
    title?: string;
    width?: number;
    height?: number;
}

const SVG_NS = "http://www.w3.org/2000/svg";
const DEFAULT_COLORS = [0x4477aa, 0xee6677, 0x228833, 0xccbb44, 0x66ccee, 0xaa3377];

function hex(color: number | undefined, fallback: string): string {
    if (color === undefined || color === null) return fallback;
    return "#" + ((color >>> 0) & 0xffffff).toString(16).padStart(6, "0");
}

function formatValue(value: number, precision = 6): string {
    if (value === 0) return "0";
    if (Math.abs(value) < 1e-3 || Math.abs(value) >= 1e6) {
        const [mantissa, exponent] = value.toExponential(precision - 1).split("e");
        return `${trimFraction(mantissa)}e${Number(exponent)}`;
    }
    const rounded = value.toPrecision(precision);
    return rounded.includes("e") ? String(Number(rounded)) : trimFraction(rounded);
}

function trimFraction(value: string): string {
    return value.includes(".") ? value.replace(/0+$/, "").replace(/\.$/, "") : value;
}

function axisPrecision(min: number, max: number): number {
    // Adjacent binary64 limits may need all 17 significant digits. Readouts on
    // that axis use the same precision; raw roundtrip values remain available
    // even when other samples in a broad range round to the same display text.
    for (let precision = 6; precision < 17; precision++) {
        const low = Number(formatValue(min, precision));
        const high = Number(formatValue(max, precision));
        if (min === max || (Number.isFinite(low) && Number.isFinite(high) && low !== high)) return precision;
    }
    return 17;
}

function rawValue(value: number): string {
    return Object.is(value, -0) ? "-0" : String(value);
}

function axisFraction(value: number, min: number, max: number): number {
    if (min === max) return 0.5;
    // Subtract nearby represented values before dividing: pre-scaling loses
    // the low bits that distinguish samples with a large common offset.
    const span = max - min;
    if (Number.isFinite(span)) return (value - min) / span;
    // Opposite finite extremes can overflow their span. Scaling is needed only
    // in that case, where subtraction does not suffer narrow-range cancellation.
    const scale = Math.max(Math.abs(min), Math.abs(max));
    return (value / scale - min / scale) / (max / scale - min / scale);
}

interface PlotCardEntry {
    tag: string;
    card: FloatingDataCard;
    options: TrajectoryPlotOptions;
    svg?: SVGSVGElement;
    playhead?: SVGLineElement;
    readoutText?: SVGTextElement;
    frameInput?: HTMLInputElement;
    frameOutput?: HTMLOutputElement;
    nFrames: number;
    width: number;
    height: number;
    xBounds?: [number, number];
    xPrecision?: number;
    yPrecision?: number;
    contextOpen?: boolean;
}

/**
 * Synchronized 2D trajectory plot manager attached to the 3D viewport.
 *
 * Renders one or more resizable, draggable FloatingDataCards hosting SVG plots.
 * Frame playheads remain synchronized across all active data cards, and live X/Y value
 * readouts update on every frame change or click.
 */
export class TrajectoryPlotOverlay {
    private readonly entries = new Map<string, PlotCardEntry>();
    private currentFrame = 0;

    constructor(
        private readonly host: HTMLElement,
        private readonly onSeek: (frame: number) => void,
        private readonly onPopout?: (tag: string) => void,
        private readonly onHide?: (tag: string) => void,
    ) {}

    set(options: TrajectoryPlotOptions | undefined): void {
        if (options?.cards) {
            const retained = new Set(options.cards.map(card => card.tag || "default"));
            for (const tag of this.entries.keys()) if (!retained.has(tag)) this.clear(tag);
            for (const card of options.cards) this.set(card);
            return;
        }
        if (!options || !options.series || options.series.length === 0) {
            if (options?.visible === false) this.hide(options.tag); else this.clear(options?.tag);
            return;
        }
        const tag = options?.tag || "default";

        let entry = this.entries.get(tag);
        const firstSeries = options.series[0];
        const nFrames = options.n_frames ?? firstSeries.values.length;

        const resolvedTitle = options.title || options.y_label || "Trajectory Plot";

        if (!entry) {
            const width = options.width || 450;
            const height = options.height || 210;

            // Offset cascade for multiple open cards
            const offset = (this.entries.size % 4) * 24;
            const left = Math.max(10, (this.host.clientWidth || 800) / 2 - width / 2 + offset);
            const top = Math.max(10, (this.host.clientHeight || 600) - height - 30 - offset);

            const card = new FloatingDataCard(this.host, {
                tag,
                title: resolvedTitle,
                width,
                height,
                left,
                top,
                onClose: () => { this.hide(tag); this.onHide?.(tag); },
                onPopout: this.onPopout ? () => this.onPopout!(tag) : undefined,
                onResize: (w, h) => {
                    if (entry) {
                        entry.width = w;
                        entry.height = h;
                        this.renderEntry(entry);
                    }
                },
            });

            entry = {
                tag,
                card,
                options,
                nFrames,
                width,
                height,
            };
            this.entries.set(tag, entry);
        } else {
            entry.options = options;
            entry.nFrames = nFrames;
            entry.card.setTitle(resolvedTitle);
        }

        if (options.visible === false) entry.card.hide(); else entry.card.show();
        this.renderEntry(entry);
        this.setFrame(this.currentFrame);
    }

    hide(tag?: string): void {
        if (!tag) {
            for (const t of Array.from(this.entries.keys())) {
                this.hide(t);
            }
            return;
        }

        const entry = this.entries.get(tag);
        if (entry) {
            entry.options = { ...entry.options, visible: false };
            entry.card.hide();
        }
    }

    private clear(tag?: string): void {
        if (!tag) {
            for (const key of Array.from(this.entries.keys())) this.clear(key);
            return;
        }
        const entry = this.entries.get(tag);
        if (entry) {
            entry.card.dispose();
            this.entries.delete(tag);
        }
    }

    /** Move playhead marker and update live X/Y value readouts on all active cards. */
    setFrame(frame: number): void {
        this.currentFrame = frame;
        for (const entry of this.entries.values()) {
            if (!entry.playhead || entry.nFrames <= 0) continue;
            const clamped = Math.max(0, Math.min(entry.nFrames - 1, frame));
            if (entry.frameInput) entry.frameInput.value = String(clamped);
            if (entry.frameOutput) entry.frameOutput.textContent = `${clamped + 1} / ${entry.nFrames}`;
            const x = this.frameToX(clamped, entry);
            entry.playhead.setAttribute("x1", String(x));
            entry.playhead.setAttribute("x2", String(x));

            const opts = entry.options;
            // Narrow through `opts`, not `entry.options`: TypeScript does not carry
            // the check across the alias, so `opts.series` read as possibly undefined.
            if (entry.readoutText && opts.series) {
                const xValue = opts.x?.[clamped];
                const xValStr = xValue !== undefined ? formatValue(xValue, entry.xPrecision) : `frame: ${clamped}`;
                const xRaw = xValue !== undefined ? `x: ${rawValue(xValue)}` : `frame: ${clamped}`;
                let display: string;
                let raw: string;
                if (opts.series.length === 1) {
                    const val = opts.series[0].values[clamped];
                    const valStr = val !== undefined ? formatValue(val, entry.yPrecision) : "—";
                    display = opts.x ? `x: ${xValStr} · y: ${valStr}` : `${xValStr} · y: ${valStr}`;
                    raw = `${xRaw} · y: ${val !== undefined ? rawValue(val) : "—"}`;
                } else {
                    const seriesStr = opts.series
                        .map((s) => `${s.label}: ${s.values[clamped] !== undefined ? formatValue(s.values[clamped], entry.yPrecision) : "—"}`)
                        .join(" · ");
                    display = `${opts.x ? "x: " : ""}${xValStr} · ${seriesStr}`;
                    raw = `${xRaw} · ${opts.series.map(s => `${s.label}: ${s.values[clamped] !== undefined ? rawValue(s.values[clamped]) : "—"}`).join(" · ")}`;
                }
                this.setNumericText(entry.readoutText, display, raw);
                entry.frameInput?.setAttribute("aria-valuetext", `Structure ${clamped + 1} of ${entry.nFrames}; index ${clamped}; ${raw}${opts.y_label ? `; ${opts.y_label}` : ""}`);
            }
        }
    }

    private frameToX(frame: number, entry: PlotCardEntry): number {
        const leftMargin = 40;
        const rightMargin = 14;
        const plotW = Math.max(200, entry.width) - leftMargin - rightMargin;
        const clamped = Math.max(0, Math.min(entry.nFrames - 1, frame));
        const [min, max] = this.xRange(entry);
        const value = entry.options.x?.[clamped] ?? clamped;
        return leftMargin + axisFraction(value, min, max) * plotW;
    }

    private xToFrame(px: number, entry: PlotCardEntry): number {
        // Samples may be nonconsecutive, reversed or repeated. Nearest pixel
        // position retains frame identity; ties keep the current frame if possible,
        // otherwise choose the earliest frame in the card.
        let chosen = 0;
        let distance = Infinity;
        for (let frame = 0; frame < entry.nFrames; frame++) {
            const candidate = Math.abs(this.frameToX(frame, entry) - px);
            if (candidate < distance - 1e-9 ||
                (Math.abs(candidate - distance) <= 1e-9 && frame === this.currentFrame)) {
                chosen = frame;
                distance = candidate;
            }
        }
        return chosen;
    }

    private xRange(entry: PlotCardEntry): [number, number] {
        if (entry.xBounds) return entry.xBounds;
        if (!entry.options.x?.length) return [0, Math.max(entry.nFrames - 1, 0)];
        let min = Infinity;
        let max = -Infinity;
        for (const x of entry.options.x) { min = Math.min(min, x); max = Math.max(max, x); }
        return [min, max];
    }

    private renderEntry(entry: PlotCardEntry): void {
        const opts = entry.options;
        entry.xBounds = undefined;
        entry.xBounds = this.xRange(entry);
        const body = entry.card.body;
        body.replaceChildren();
        Object.assign(body.style, { display: entry.card.minimized ? "none" : "flex", flexDirection: "column", overflow: "auto" });

        const controls = document.createElement("label");
        controls.setAttribute("data-molsysviewer-plot-navigation", entry.tag);
        Object.assign(controls.style, { display: "flex", alignItems: "center", gap: "6px", minWidth: "200px",
            height: "28px", flex: "0 0 28px", boxSizing: "border-box", padding: "2px 8px" });
        const caption = document.createElement("span");
        caption.textContent = "Structure";
        const input = document.createElement("input");
        input.type = "range"; input.min = "0"; input.max = String(Math.max(0, entry.nFrames - 1)); input.step = "1";
        input.disabled = entry.nFrames < 2;
        input.setAttribute("aria-label", `${opts.title || opts.y_label || "Trajectory plot"}: structure index`);
        Object.assign(input.style, { minWidth: "0", flex: "1 1 auto" });
        input.addEventListener("input", () => {
            const frame = Number(input.value);
            if (this.entries.get(entry.tag) === entry && Number.isInteger(frame) && frame >= 0 && frame < entry.nFrames) this.onSeek(frame);
        });
        const output = document.createElement("output");
        output.setAttribute("aria-label", "Selected structure");
        output.setAttribute("aria-live", "off");
        output.style.whiteSpace = "nowrap";
        controls.appendChild(caption); controls.appendChild(input); controls.appendChild(output);
        entry.frameInput = input; entry.frameOutput = output;

        const width = Math.max(200, entry.width || body.clientWidth || 440);
        const height = Math.max(120, (entry.height || body.clientHeight || 168) - 28);

        const M = { top: 24, right: 14, bottom: opts.x_label ? 28 : 20, left: 40 };
        const plotHeight = Math.max(10, height - M.top - M.bottom);

        const svg = document.createElementNS(SVG_NS, "svg");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        Object.assign(svg.style, { display: "block", cursor: "pointer", userSelect: "none" });
        Object.assign(svg.style, { width: `${width}px`, minWidth: "200px", minHeight: "120px", flex: "1 0 120px" });
        entry.svg = svg;

        // Min & Max range
        let min = Infinity;
        let max = -Infinity;
        for (const s of opts.series!) {
            for (const v of s.values) {
                if (v < min) min = v;
                if (v > max) max = v;
            }
        }
        if (!isFinite(min) || !isFinite(max)) { min = 0; max = 1; }
        const [xMin, xMax] = this.xRange(entry);
        entry.xPrecision = axisPrecision(xMin, xMax);
        entry.yPrecision = axisPrecision(min, max);
        const yOf = (v: number) => M.top + (1 - axisFraction(v, min, max)) * plotHeight;

        // Axes frame path
        const axis = document.createElementNS(SVG_NS, "path");
        axis.setAttribute("d", `M${M.left},${M.top} L${M.left},${height - M.bottom} L${width - M.right},${height - M.bottom}`);
        axis.setAttribute("fill", "none");
        axis.setAttribute("stroke", "rgba(242,242,242,0.4)");
        axis.setAttribute("stroke-width", "1");
        svg.appendChild(axis);

        // Live X/Y Readout text (top right of plot area)
        const readoutText = this.text(width - M.right, 14, "", "end", "rgba(244, 244, 245, 0.9)", 10);
        readoutText.setAttribute("font-weight", "600");
        readoutText.setAttribute("data-molsysviewer-plot-value", "readout");
        svg.appendChild(readoutText);
        entry.readoutText = readoutText;

        // Event markers (vertical lines)
        for (const ev of opts.events ?? []) {
            const x = this.frameToX(ev.frame, entry);
            const line = document.createElementNS(SVG_NS, "line");
            line.setAttribute("x1", String(x));
            line.setAttribute("x2", String(x));
            line.setAttribute("y1", String(M.top));
            line.setAttribute("y2", String(height - M.bottom));
            line.setAttribute("stroke", hex(ev.color, "#f59e0b"));
            line.setAttribute("stroke-width", "1");
            line.setAttribute("stroke-dasharray", "3,2");
            svg.appendChild(line);
        }

        // Series polylines
        opts.series!.forEach((s, i) => {
            const pts = s.values
                .map((v, idx) => `${this.frameToX(idx, entry)},${yOf(v)}`)
                .join(" ");
            const poly = document.createElementNS(SVG_NS, "polyline");
            poly.setAttribute("points", pts);
            poly.setAttribute("fill", "none");
            poly.setAttribute("stroke", hex(s.color, hex(DEFAULT_COLORS[i % DEFAULT_COLORS.length], "#4477aa")));
            poly.setAttribute("stroke-width", "1.5");
            svg.appendChild(poly);
        });

        // Playhead line
        const playhead = document.createElementNS(SVG_NS, "line");
        playhead.setAttribute("y1", String(M.top));
        playhead.setAttribute("y2", String(height - M.bottom));
        playhead.setAttribute("stroke", "#ffffff");
        playhead.setAttribute("stroke-width", "1.5");
        playhead.setAttribute("pointer-events", "none");
        svg.appendChild(playhead);
        entry.playhead = playhead;

        // Axis labels
        if (opts.x_label) {
            svg.appendChild(this.text(width / 2, height - 4, opts.x_label, "middle", "rgba(242,242,242,0.7)", 10));
        }
        if (opts.y_label) {
            const t = this.text(12, height / 2, opts.y_label, "middle", "rgba(242,242,242,0.7)", 10);
            t.setAttribute("transform", `rotate(-90 12 ${height / 2})`);
            svg.appendChild(t);
        }
        for (const [value, x, anchor, name] of [
            [xMin, M.left, "start", "x-min"],
            [xMax, width - M.right, "end", "x-max"],
        ] as const) {
            const label = this.text(x, height - M.bottom + 11, "", anchor, "rgba(242,242,242,0.5)", 9);
            label.setAttribute("data-molsysviewer-plot-value", name);
            this.setNumericText(label, formatValue(value, entry.xPrecision), rawValue(value));
            svg.appendChild(label);
        }

        // Legend (multi-series only)
        if (opts.series!.length > 1) {
            opts.series!.forEach((s, i) => {
                const ly = M.top + 2 + i * 13;
                const chip = document.createElementNS(SVG_NS, "rect");
                chip.setAttribute("x", String(M.left + 8));
                chip.setAttribute("y", String(ly));
                chip.setAttribute("width", "9");
                chip.setAttribute("height", "9");
                chip.setAttribute("fill", hex(s.color, hex(DEFAULT_COLORS[i % DEFAULT_COLORS.length], "#4477aa")));
                svg.appendChild(chip);
                svg.appendChild(this.text(M.left + 21, ly + 8, s.label, "start", "#e8e8e8", 10));
            });
        }

        // Seek on click
        svg.addEventListener("click", (e) => {
            const rect = svg.getBoundingClientRect();
            const px = (e.clientX - rect.left) * (width / rect.width);
            this.onSeek(this.xToFrame(px, entry));
        });

        body.appendChild(svg);
        body.appendChild(controls);
        if (opts.series?.some(series => series.observation)) {
            const details = document.createElement("details");
            details.setAttribute("data-molsysviewer-plot-context", entry.tag);
            details.open = !!entry.contextOpen;
            Object.assign(details.style, { flex: "0 0 auto", padding: "6px 8px", fontSize: "12px", userSelect: "text" });
            const summary = document.createElement("summary");
            summary.textContent = "Calculation details";
            summary.style.cursor = "pointer";
            details.appendChild(summary);
            let populated = false;
            const populate = () => {
                entry.contextOpen = details.open;
                if (!details.open || populated) return;
                populated = true;
                const notice = document.createElement("p");
                notice.textContent = "Stored historical context. Source correspondence is declared; these details do not verify that the current molecular system still matches. Preserve the source and reference inputs for reproduction.";
                details.appendChild(notice);
                opts.series?.forEach((series, index) => {
                    if (!series.observation) return;
                    const label = document.createElement("strong");
                    label.textContent = series.label;
                    details.appendChild(label);
                    const raw = document.createElement("pre");
                    raw.setAttribute("data-molsysviewer-series-observation", String(index));
                    raw.textContent = JSON.stringify({ context: series.observation,
                        original_observation_rows: series.observation_rows,
                        original_observation_count: series.observation_count }, null, 2);
                    Object.assign(raw.style, { maxHeight: "200px", overflow: "auto", whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontSize: "11px" });
                    details.appendChild(raw);
                });
            };
            details.addEventListener("toggle", populate);
            populate();
            body.appendChild(details);
        }
        this.setFrame(this.currentFrame);
    }

    private text(x: number, y: number, content: string, anchor: string, fill: string, size: number): SVGTextElement {
        const t = document.createElementNS(SVG_NS, "text");
        t.setAttribute("x", String(x));
        t.setAttribute("y", String(y));
        t.setAttribute("text-anchor", anchor);
        t.setAttribute("fill", fill);
        t.setAttribute("font-size", String(size));
        t.setAttribute("font-family", '"IBM Plex Sans", system-ui, sans-serif');
        t.textContent = content;
        return t;
    }

    private setNumericText(text: SVGTextElement, display: string, raw: string): void {
        const value = document.createElementNS(SVG_NS, "tspan");
        value.textContent = display;
        const title = document.createElementNS(SVG_NS, "title");
        title.textContent = raw;
        text.replaceChildren(value, title);
        text.setAttribute("aria-label", raw);
        text.setAttribute("tabindex", "0");
        text.style.userSelect = "text";
        text.style.cursor = "text";
        text.onclick = event => event.stopPropagation();
    }

    dispose(): void {
        this.clear();
    }
}
