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
    visible?: boolean;
    series?: TrajectoryPlotSeries[];
    n_frames?: number;
    x?: number[];
    events?: TrajectoryPlotEvent[];
    x_label?: string;
    y_label?: string;
    title?: string;
}

const SVG_NS = "http://www.w3.org/2000/svg";
const WIDTH = 440;
const HEIGHT = 168;
const M = { top: 22, right: 12, bottom: 26, left: 40 };
const DEFAULT_COLORS = [0x4477aa, 0xee6677, 0x228833, 0xccbb44, 0x66ccee, 0xaa3377];

function hex(color: number | undefined, fallback: string): string {
    if (color === undefined || color === null) return fallback;
    return "#" + ((color >>> 0) & 0xffffff).toString(16).padStart(6, "0");
}

/**
 * A synchronized 2D trajectory plot pinned to the bottom of the viewport. Any
 * per-frame scalar series (RMSD, radius of gyration, a channel bottleneck
 * radius, an energy term, ...) is drawn against the frame axis; a playhead
 * marker follows the current frame, and clicking the plot seeks the 3D view to
 * the corresponding frame. Fully generic — the data is supplied by
 * `trajectory_plot.show(...)` on the Python side.
 */
export class TrajectoryPlotOverlay {
    private readonly root: HTMLElement;
    private svg?: SVGSVGElement;
    private playhead?: SVGLineElement;
    private options?: TrajectoryPlotOptions;
    private nFrames = 0;
    private currentFrame = 0;

    constructor(private readonly host: HTMLElement, private readonly onSeek: (frame: number) => void) {
        this.root = document.createElement("div");
        this.root.setAttribute("data-molsysviewer-trajectory-plot", "true");
        Object.assign(this.root.style, {
            position: "absolute",
            bottom: "12px",
            left: "50%",
            transform: "translateX(-50%)",
            display: "none",
            background: "rgba(20, 20, 20, 0.78)",
            borderRadius: "8px",
            padding: "6px",
            zIndex: "10",
            cursor: "pointer",
            userSelect: "none",
        });
        this.host.appendChild(this.root);
    }

    set(options: TrajectoryPlotOptions | undefined): void {
        if (!options || options.visible === false || !options.series || options.series.length === 0) {
            this.hide();
            return;
        }
        this.options = options;
        const first = options.series[0];
        this.nFrames = options.n_frames ?? first.values.length;
        this.render();
        this.root.style.display = "block";
        this.setFrame(this.currentFrame);
    }

    hide(): void {
        this.options = undefined;
        this.root.style.display = "none";
        this.root.replaceChildren();
        this.svg = undefined;
        this.playhead = undefined;
    }

    /** Move the playhead marker to `frame`; called on every trajectory frame change. */
    setFrame(frame: number): void {
        this.currentFrame = frame;
        if (!this.playhead || this.nFrames <= 1) return;
        const x = this.frameToX(frame);
        this.playhead.setAttribute("x1", String(x));
        this.playhead.setAttribute("x2", String(x));
    }

    private plotWidth(): number {
        return WIDTH - M.left - M.right;
    }

    private frameToX(frame: number): number {
        const denom = Math.max(this.nFrames - 1, 1);
        const clamped = Math.max(0, Math.min(this.nFrames - 1, frame));
        return M.left + (clamped / denom) * this.plotWidth();
    }

    private xToFrame(px: number): number {
        const denom = Math.max(this.nFrames - 1, 1);
        const ratio = (px - M.left) / this.plotWidth();
        return Math.max(0, Math.min(this.nFrames - 1, Math.round(ratio * denom)));
    }

    private render(): void {
        const opts = this.options!;
        this.root.replaceChildren();

        const svg = document.createElementNS(SVG_NS, "svg");
        svg.setAttribute("width", String(WIDTH));
        svg.setAttribute("height", String(HEIGHT));
        svg.setAttribute("viewBox", `0 0 ${WIDTH} ${HEIGHT}`);
        this.svg = svg;

        // Value range across all series.
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
        const yOf = (v: number) => M.top + (1 - (v - min) / (max - min)) * (HEIGHT - M.top - M.bottom);

        // Axes frame.
        const axis = document.createElementNS(SVG_NS, "path");
        axis.setAttribute("d",
            `M${M.left},${M.top} L${M.left},${HEIGHT - M.bottom} L${WIDTH - M.right},${HEIGHT - M.bottom}`);
        axis.setAttribute("fill", "none");
        axis.setAttribute("stroke", "rgba(242,242,242,0.5)");
        axis.setAttribute("stroke-width", "1");
        svg.appendChild(axis);

        // Event markers (vertical lines).
        for (const ev of opts.events ?? []) {
            const x = this.frameToX(ev.frame);
            const line = document.createElementNS(SVG_NS, "line");
            line.setAttribute("x1", String(x));
            line.setAttribute("x2", String(x));
            line.setAttribute("y1", String(M.top));
            line.setAttribute("y2", String(HEIGHT - M.bottom));
            line.setAttribute("stroke", hex(ev.color, "#f59e0b"));
            line.setAttribute("stroke-width", "1");
            line.setAttribute("stroke-dasharray", "3,2");
            svg.appendChild(line);
        }

        // Series polylines.
        opts.series!.forEach((s, i) => {
            const denom = Math.max(s.values.length - 1, 1);
            const pts = s.values
                .map((v, idx) => `${M.left + (idx / denom) * this.plotWidth()},${yOf(v)}`)
                .join(" ");
            const poly = document.createElementNS(SVG_NS, "polyline");
            poly.setAttribute("points", pts);
            poly.setAttribute("fill", "none");
            poly.setAttribute("stroke", hex(s.color, hex(DEFAULT_COLORS[i % DEFAULT_COLORS.length], "#4477aa")));
            poly.setAttribute("stroke-width", "1.5");
            svg.appendChild(poly);
        });

        // Playhead (created last so it renders on top).
        const playhead = document.createElementNS(SVG_NS, "line");
        playhead.setAttribute("y1", String(M.top));
        playhead.setAttribute("y2", String(HEIGHT - M.bottom));
        playhead.setAttribute("stroke", "#ffffff");
        playhead.setAttribute("stroke-width", "1.5");
        playhead.setAttribute("pointer-events", "none");
        svg.appendChild(playhead);
        this.playhead = playhead;

        // Labels.
        if (opts.title) svg.appendChild(this.text(WIDTH / 2, 14, opts.title, "middle", "#f2f2f2", 12));
        if (opts.x_label) svg.appendChild(this.text(WIDTH / 2, HEIGHT - 6, opts.x_label, "middle", "rgba(242,242,242,0.7)", 10));
        if (opts.y_label) {
            const t = this.text(12, HEIGHT / 2, opts.y_label, "middle", "rgba(242,242,242,0.7)", 10);
            t.setAttribute("transform", `rotate(-90 12 ${HEIGHT / 2})`);
            svg.appendChild(t);
        }
        svg.appendChild(this.text(M.left, HEIGHT - M.bottom + 12, "0", "middle", "rgba(242,242,242,0.6)", 9));
        svg.appendChild(this.text(WIDTH - M.right, HEIGHT - M.bottom + 12, String(Math.max(this.nFrames - 1, 0)), "middle", "rgba(242,242,242,0.6)", 9));

        // Legend (multi-series only).
        if (opts.series!.length > 1) {
            opts.series!.forEach((s, i) => {
                const ly = M.top + 2 + i * 13;
                const chip = document.createElementNS(SVG_NS, "rect");
                chip.setAttribute("x", String(WIDTH - M.right - 90));
                chip.setAttribute("y", String(ly));
                chip.setAttribute("width", "9");
                chip.setAttribute("height", "9");
                chip.setAttribute("fill", hex(s.color, hex(DEFAULT_COLORS[i % DEFAULT_COLORS.length], "#4477aa")));
                svg.appendChild(chip);
                svg.appendChild(this.text(WIDTH - M.right - 77, ly + 8, s.label, "start", "#e8e8e8", 10));
            });
        }

        // Seek on click.
        svg.addEventListener("click", (e) => {
            const rect = svg.getBoundingClientRect();
            const px = (e.clientX - rect.left) * (WIDTH / rect.width);
            this.onSeek(this.xToFrame(px));
        });

        this.root.appendChild(svg);
    }

    private text(x: number, y: number, content: string, anchor: string, fill: string, size: number): SVGTextElement {
        const t = document.createElementNS(SVG_NS, "text");
        t.setAttribute("x", String(x));
        t.setAttribute("y", String(y));
        t.setAttribute("text-anchor", anchor);
        t.setAttribute("fill", fill);
        t.setAttribute("font-size", String(size));
        t.setAttribute("font-family", "\"IBM Plex Sans\", system-ui, sans-serif");
        t.textContent = content;
        return t;
    }

    dispose(): void {
        this.root.remove();
    }
}
