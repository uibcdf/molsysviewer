import type { MolSysViewerController } from "./viewer-controller";
import { compileMovieTimeline } from "./movie-timeline";
import { readCanvasDraw } from "./canvas-draw";

type Sample = ReturnType<ReturnType<typeof compileMovieTimeline>["evaluate"]>;
const collection: Record<string, string> = { region: "regions", shape: "shapes", annotation: "annotations",
    interaction: "interactions", measurement: "measurements", layer: "layers" };
const key = (domain: string, tag: string | null) => JSON.stringify([domain, tag]);

/** Compose layer gates from the recorded scene, never from a previous sample. */
export function movieWebVisibility(scene: any, sample: Sample) {
    const desired = new Map(sample.visibility.map(row => [key(row.domain, row.tag), { ...row }]));
    for (const { domain, tag } of sample.appearance ?? []) {
        if (domain === "scene" || desired.has(key(domain, tag))) continue;
        const row = domain === "whole" ? scene.whole : scene[collection[domain]].find((row: any) => row.tag === tag);
        desired.set(key(domain, tag), { domain: domain as any, tag, visible: domain === "whole" ? row.visible : !row.hidden });
    }
    for (const gate of sample.visibility.filter(row => row.domain === "layer")) {
        const baselineGate = scene.layers.find((row: any) => row.tag === gate.tag);
        for (const [domain, name] of Object.entries(collection)) {
            if (domain === "layer") continue;
            for (const row of scene[name] ?? []) {
                if ((row.layer_tag ?? row.options?.layer_tag ?? row.layer) !== gate.tag) continue;
                const id = key(domain, row.tag);
                const own = desired.get(id)?.visible ?? (baselineGate.hidden ? true : !row.hidden);
                desired.set(id, { domain: domain as any, tag: row.tag, visible: gate.visible && own });
            }
        }
        desired.delete(key("layer", gate.tag));
    }
    return Array.from(desired.values());
}

/** One serialized writer and one draw-paced clock for an embedded presentation. */
export class MovieWebPlayer {
    private timeline;
    private recipe: any;
    private scene: any;
    private previous = new Map<string, string>();
    private frame = -1;
    private queue: Promise<unknown> = Promise.resolve();
    private generation = 0;
    private closed = false;
    private drawing = new AbortController();
    private raf: number | undefined;
    private playing = false;
    private time = 0;
    private origin = 0;
    private playButton: HTMLButtonElement;
    private range: HTMLInputElement;
    private status: HTMLOutputElement;
    private surface: HTMLElement;
    private interact: () => void;
    private layoutObserver?: ResizeObserver;

    constructor(private controller: MolSysViewerController, private host: HTMLElement, presentation: any) {
        if (presentation?.schema !== "molsysviewer.movie_web@1" || presentation?.assets?.policy !== "embedded-offline") {
            throw new Error("Unsupported Movie web presentation.");
        }
        this.recipe = structuredClone(presentation.recipe);
        this.timeline = compileMovieTimeline(this.recipe, { trackedVisibility: true });
        this.scene = this.recipe.baseline.scene;
        const bar = document.createElement("div"); this.surface = bar;
        bar.dataset.molsysviewerMoviePlayer = "true"; bar.setAttribute("role", "group"); bar.setAttribute("aria-label", "Movie playback");
        Object.assign(bar.style, { position: "absolute", bottom: "12px", left: "50%", transform: "translateX(-50%)",
            display: "flex", alignItems: "center", gap: "8px", width: "min(540px, calc(100% - 32px))",
            padding: "9px", borderRadius: "12px", background: "rgba(24,28,34,.94)", color: "#fff", zIndex: "900",
            boxSizing: "border-box", font: "13px system-ui, sans-serif" });
        const button = (text: string, action: () => void) => {
            const value = document.createElement("button"); value.type = "button"; value.textContent = text;
            Object.assign(value.style, { cursor: "pointer", color: "#fff", background: "#363d48", border: "1px solid #707782", borderRadius: "6px", padding: "5px 8px" });
            value.addEventListener("click", action); bar.appendChild(value); return value;
        };
        this.playButton = button("Play", () => { if (this.playing) this.pause(); else this.play(); });
        button("Restart", () => { void this.seek(0).catch(error => this.fail(error)); });
        this.range = document.createElement("input"); this.range.type = "range";
        this.range.min = "0"; this.range.max = String(this.timeline.duration_ms); this.range.step = "any";
        this.range.value = "0"; this.range.setAttribute("aria-label", "Movie time in milliseconds");
        Object.assign(this.range.style, { flex: "1", minWidth: "40px" });
        this.range.addEventListener("input", () => { void this.seek(Number(this.range.value)).catch(error => this.fail(error)); });
        bar.appendChild(this.range);
        this.status = document.createElement("output"); this.status.setAttribute("aria-live", "off"); bar.appendChild(this.status);
        for (const event of ["pointerdown", "click", "wheel", "keydown"]) bar.addEventListener(event, e => e.stopPropagation());
        host.appendChild(bar);
        const reserveControls = () => this.controller.setOverlayBottomInset(
            Math.max(0, host.getBoundingClientRect().bottom - bar.getBoundingClientRect().top + 8));
        reserveControls();
        this.layoutObserver = new ResizeObserver(reserveControls);
        this.layoutObserver.observe(host); this.layoutObserver.observe(bar);
        this.interact = () => this.pause();
        host.addEventListener("pointerdown", this.interact); host.addEventListener("wheel", this.interact, { passive: true });
        this.update();
    }

    async initialize() { await this.seek(0); this.host.dataset.molsysviewerMovieReady = "true"; }
    get state() { return { time_ms: this.time, playing: this.playing, closed: this.closed }; }

    pause(): Promise<unknown> {
        this.playing = false; this.generation++;
        if (this.raf !== undefined) cancelAnimationFrame(this.raf);
        this.raf = undefined; this.update();
        // Freeze the last submitted complete sample; never leave queued writes
        // that advance after this promise resolves.
        return this.queue;
    }

    async seek(time: number) {
        const sample = this.timeline.evaluate(time); // Validate before stopping a valid preview.
        this.pause();
        const generation = this.generation;
        const work = this.queue.then(async () => {
            if (this.closed || generation !== this.generation) return;
            this.previous.clear();
            await this.apply(sample);
        });
        this.queue = work.catch(() => {});
        return work;
    }

    play() {
        if (this.closed || this.playing) return;
        const generation = ++this.generation;
        this.playing = true; this.update();
        const start = this.time >= this.timeline.duration_ms ? 0 : this.time;
        const work = this.queue.then(async () => {
            if (this.closed || generation !== this.generation) return;
            this.previous.clear();
            this.origin = performance.now() - start;
            await this.tick(generation);
        });
        this.queue = work.catch(error => this.fail(error));
    }

    private async tick(generation: number) {
        if (this.closed || !this.playing || generation !== this.generation) return;
        const at = Math.min(this.timeline.duration_ms, Math.max(0, performance.now() - this.origin));
        await this.apply(this.timeline.evaluate(at));
        if (this.closed || !this.playing || generation !== this.generation) return;
        if (at >= this.timeline.duration_ms) { this.playing = false; this.update(); return; }
        this.raf = requestAnimationFrame(() => {
            this.raf = undefined;
            const work = this.queue.then(() => this.tick(generation));
            this.queue = work.catch(error => this.fail(error));
        });
    }

    private async send(message: any) {
        if (this.closed) throw new Error("Movie web player is closed.");
        await this.controller.handleMessage(message, { throwOnError: true });
    }

    private async changed(id: string, value: unknown, operation: () => Promise<void>) {
        const encoded = JSON.stringify(value);
        if (this.previous.get(id) === encoded) return;
        await operation(); this.previous.set(id, encoded);
    }

    private async apply(sample: Sample) {
        await this.send({ op: "set_trajectory_playback", action: "pause" });
        await this.send({ op: "toggle_spin", enable: false });
        if (sample.structure_index !== this.frame) {
            await this.send({ op: "set_trajectory_frame", index: sample.structure_index });
            this.frame = sample.structure_index;
        }
        const grouped = new Map<string, any[]>();
        const appearance = [...(sample.appearance ?? [])];
        if (this.recipe.baseline.environment_capture) {
            const environment = this.scene.environment;
            for (const property of ["background", "lighting"]) {
                if (!appearance.some(row => row.domain === "scene" && row.property === property)) {
                    appearance.push({ domain: "scene", tag: null, property, value: property === "background" ? environment.background.color : environment.lighting });
                }
            }
        }
        for (const row of appearance) {
            const id = key(row.domain, row.tag);
            grouped.set(id, [...(grouped.get(id) ?? []), row]);
        }
        for (const [id, rows] of grouped) await this.changed(id, rows, async () => {
            const { domain, tag } = rows[0];
            const values = Object.fromEntries(rows.map(row => [row.property, row.value]));
            const record = domain === "whole" ? this.scene.whole : this.scene[collection[domain]]?.find((row: any) => row.tag === tag);
            if (domain === "whole" || domain === "region") {
                const params = structuredClone(record.params ?? {});
                if ("color" in values) { delete params.color_scheme; params.molstar_color_theme = { name: "uniform", params: { value: values.color } }; }
                if ("alpha" in values) params.alpha = values.alpha;
                await this.send({ op: domain === "whole" ? "set_whole_representation" : "set_region_representation", tag,
                    order: record.order, representation: values.representation ?? record.representation, preset: null, params });
            } else if (domain === "shape") {
                await this.send({ op: "update_sphere", tag, options: { ...structuredClone(record.options), ...values, tag,
                    layer_tag: record.layer_tag ?? record.options?.layer_tag } });
            } else if (domain === "annotation") await this.send({ op: "update_label", tag, options: { tag, ...values } });
            else if (domain === "interaction") await this.controller.interactions.setMovieStyle(tag, values);
            else for (const [property, value] of Object.entries(values)) {
                await this.send(property === "background" ? { op: "set_background_color", color: value } : { op: "set_lighting", ...(value as object) });
            }
        });
        // Frame changes and shape rebuilds can recreate visible native cells.
        // Reassert final member gates after those owners have completed.
        const visibility = movieWebVisibility(this.scene, sample);
        const layerRows = this.scene.layers.map((row: any) => ({ ...row,
            hidden: sample.visibility.find(item => item.domain === "layer" && item.tag === row.tag)?.visible === false
                || (sample.visibility.some(item => item.domain === "layer" && item.tag === row.tag) ? false : row.hidden) }));
        await this.send({ op: "set_layer_summaries", layers: layerRows });
        for (const row of visibility) await this.send(row.domain === "whole" ? { op: row.visible ? "show_whole" : "hide_whole" }
            : row.domain === "region" ? { op: row.visible ? "show_region" : "hide_region", tag: row.tag }
                : { op: row.visible ? "show_layer" : "hide_layer", tag: row.tag, kind: row.domain });
        await this.send({ op: "set_camera_snapshot", snapshot: sample.camera, duration_ms: 0 });
        const canvas = this.controller.plugin.canvas3d;
        if (!canvas) throw new Error("Movie presentation has no canvas.");
        await readCanvasDraw(canvas, () => undefined, 15000, this.drawing.signal,
            () => !!this.controller.readMovingVisualState());
        this.time = sample.time_ms; this.update();
    }

    private update() {
        this.playButton.textContent = this.playing ? "Pause" : "Play";
        this.range.value = String(this.time);
        this.status.value = `${(this.time / 1000).toFixed(2)} / ${(this.timeline.duration_ms / 1000).toFixed(2)} s`;
    }
    private fail(error: unknown) {
        if (this.closed) return;
        void this.pause();
        this.status.value = error instanceof Error ? error.message : String(error);
        this.status.setAttribute("role", "alert");
        console.error("[MolSysViewer] Movie presentation failed", error);
    }
    dispose() {
        if (this.closed) return;
        void this.pause(); this.closed = true; this.drawing.abort();
        this.host.removeEventListener("pointerdown", this.interact); this.host.removeEventListener("wheel", this.interact);
        this.layoutObserver?.disconnect(); this.controller.setOverlayBottomInset(0);
        this.surface.remove(); delete this.host.dataset.molsysviewerMovieReady;
    }
}
