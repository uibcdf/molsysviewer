import { FloatingDataCard } from "./floating-data-card";

export interface TrajectoryPlotSeries {
    label: string;
    values: number[];
    color?: number;
}

export interface TrajectoryPlotEvent {
    frame: number;
    label?: string;
    color?: number;
}

export interface TrajectoryPlotOptions {
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

function formatValue(v: number): string {
    if (Number.isInteger(v)) return String(v);
    return v.toFixed(2);
}

interface PlotCardEntry {
    tag: string;
    card: FloatingDataCard;
    options: TrajectoryPlotOptions;
    svg?: SVGSVGElement;
    playhead?: SVGLineElement;
    readoutText?: SVGTextElement;
    nFrames: number;
    width: number;
    height: number;
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
    ) {}

    set(options: TrajectoryPlotOptions | undefined): void {
        const tag = options?.tag || "default";

        if (!options || options.visible === false || !options.series || options.series.length === 0) {
            this.hide(tag);
            return;
        }

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
                onClose: () => this.hide(tag),
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
            entry.card.titleElement.textContent = resolvedTitle;
        }

        entry.card.show();
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
            const x = this.frameToX(clamped, entry);
            entry.playhead.setAttribute("x1", String(x));
            entry.playhead.setAttribute("x2", String(x));

            const opts = entry.options;
            // Narrow through `opts`, not `entry.options`: TypeScript does not carry
            // the check across the alias, so `opts.series` read as possibly undefined.
            if (entry.readoutText && opts.series) {
                const xValStr = opts.x && opts.x.length > clamped ? formatValue(opts.x[clamped]) : `frame: ${clamped}`;
                
                if (opts.series.length === 1) {
                    const val = opts.series[0].values[clamped];
                    const valStr = val !== undefined ? formatValue(val) : "—";
                    entry.readoutText.textContent = opts.x ? `x: ${xValStr} · y: ${valStr}` : `${xValStr} · y: ${valStr}`;
                } else {
                    const seriesStr = opts.series
                        .map((s) => `${s.label}: ${s.values[clamped] !== undefined ? formatValue(s.values[clamped]) : "—"}`)
                        .join(" · ");
                    entry.readoutText.textContent = `${xValStr} · ${seriesStr}`;
                }
            }
        }
    }

    private frameToX(frame: number, entry: PlotCardEntry): number {
        const leftMargin = 40;
        const rightMargin = 12;
        const plotW = Math.max(10, entry.width - leftMargin - rightMargin);
        const denom = Math.max(entry.nFrames - 1, 1);
        const clamped = Math.max(0, Math.min(entry.nFrames - 1, frame));
        return leftMargin + (clamped / denom) * plotW;
    }

    private xToFrame(px: number, entry: PlotCardEntry): number {
        const leftMargin = 40;
        const rightMargin = 12;
        const plotW = Math.max(10, entry.width - leftMargin - rightMargin);
        const denom = Math.max(entry.nFrames - 1, 1);
        const ratio = (px - leftMargin) / plotW;
        return Math.max(0, Math.min(entry.nFrames - 1, Math.round(ratio * denom)));
    }

    private renderEntry(entry: PlotCardEntry): void {
        const opts = entry.options;
        const body = entry.card.body;
        body.replaceChildren();

        const width = Math.max(200, entry.width || body.clientWidth || 440);
        const height = Math.max(120, entry.height || body.clientHeight || 168);

        const M = { top: 24, right: 14, bottom: opts.x_label ? 28 : 20, left: 40 };
        const plotWidth = Math.max(10, width - M.left - M.right);
        const plotHeight = Math.max(10, height - M.top - M.bottom);

        const svg = document.createElementNS(SVG_NS, "svg");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "100%");
        svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
        Object.assign(svg.style, { display: "block", cursor: "pointer", userSelect: "none" });
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
        if (min === max) { min -= 1; max += 1; }

        const yOf = (v: number) => M.top + (1 - (v - min) / (max - min)) * plotHeight;

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
        svg.appendChild(readoutText);
        entry.readoutText = readoutText;

        // Event markers (vertical lines)
        for (const ev of opts.events ?? []) {
            const x = M.left + (Math.max(0, Math.min(entry.nFrames - 1, ev.frame)) / Math.max(entry.nFrames - 1, 1)) * plotWidth;
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
            const denom = Math.max(s.values.length - 1, 1);
            const pts = s.values
                .map((v, idx) => `${M.left + (idx / denom) * plotWidth},${yOf(v)}`)
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
        svg.appendChild(this.text(M.left, height - M.bottom + 11, "0", "middle", "rgba(242,242,242,0.5)", 9));
        svg.appendChild(this.text(width - M.right, height - M.bottom + 11, String(Math.max(entry.nFrames - 1, 0)), "middle", "rgba(242,242,242,0.5)", 9));

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

    dispose(): void {
        this.hide();
    }
}
