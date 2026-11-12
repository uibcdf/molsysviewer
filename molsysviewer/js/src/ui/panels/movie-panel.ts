import { BasePanel } from "./base-panel";
import type { PanelAction, PanelContext } from "./types";
import type { StudioActionResult } from "./saved-list-tools";
import { makeButton, makeSectionHeader, makeStyledSelect, studioRequestId, workflowHelp } from "./ui-helpers";

type Key = { time_ms: number; value: any; easing?: string };
type Track = { tag: string; target: { domain: string; tag?: string }; property: string; n_keys: number };
export type MoviePanelState = {
    op: "set_movie_state"; revision: number; version: number | null; duration_ms: number; n_tracks: number;
    system_loaded: boolean; live_available: boolean; busy: string | null; job_id: string | null;
    progress?: { frames_written: number; total_frames: number; time_ms: number } | null;
    last_output?: { path: string; bytes: number } | null; request_id?: string;
    editor?: { offset: number; tracks: Track[]; track: (Track & { keys: Key[]; key_offset: number }) | null;
        representations?: string[]; targets?: Array<{ domain: string; tag?: string }>; target_count?: number };
};

const properties: Record<string, string[]> = {
    camera: ["pose"], structure: ["index"], whole: ["visible", "representation", "color", "alpha"],
    region: ["visible", "representation", "color", "alpha"], shape: ["visible", "color", "alpha"],
    annotation: ["visible", "text"], measurement: ["visible"], interaction: ["visible", "color", "alpha"],
    layer: ["visible"], scene: ["background", "lighting"],
};
const labels: Record<string, string> = { pose: "Camera pose", index: "Structure", visible: "Visibility",
    color: "Color", alpha: "Opacity", representation: "Representation", text: "Text", background: "Background", lighting: "Lighting" };

function note(text: string): HTMLElement {
    const el = document.createElement("p"); el.textContent = text;
    Object.assign(el.style, { fontSize: "11px", lineHeight: "1.5", margin: "4px 0", opacity: "0.8" }); return el;
}
function card(): HTMLDivElement {
    const el = document.createElement("div");
    Object.assign(el.style, { display: "flex", flexDirection: "column", gap: "8px", padding: "10px",
        border: "1px solid rgba(255,255,255,0.12)", borderRadius: "8px", marginBottom: "10px" }); return el;
}

/** Local forms are drafts; every accepted edit and live operation belongs to Python's Movie manager. */
export class MoviePanel extends BasePanel {
    readonly key = "movie";
    private state?: MoviePanelState;
    private tab = "timeline";
    private visible = false;
    private request = "";
    private pending: string | null = null;
    private pendingDuration: string | null = null;
    private pendingAction: PanelAction | null = null;
    private draftRevision: number | null = null;
    private message = "";
    private selected = "";
    private offset = 0;
    private keyOffset = 0;
    private tracks: Track[] = [];
    private track: (Track & { keys: Key[]; key_offset: number }) | null = null;
    private duration = "10";
    private durationTouched = false;
    private tag = "";
    private domain = "camera";
    private target = "";
    private property = "pose";
    private at = "0";
    private easing = "linear";
    private value = "0";
    private secondValue = "0.6";
    private shown = true;
    private replace = false;
    private confirmation = "";
    private previewAt = "0";
    private loop = false;
    private path = "movie.mp4";
    private fps = "25";
    private width = "1280";
    private height = "720";
    private overwrite = false;
    private includeOverlays = true;
    private settingsOpen = false;
    private representations: string[] = [];
    private targets: Array<{ domain: string; tag?: string }> = [];

    constructor(private ctx: PanelContext, private hasAuthority = true) { super(); }

    override setVisible(visible: boolean): void {
        const opened = visible && !this.visible; this.visible = visible;
        super.setVisible(visible);
        if (opened && this.hasAuthority) this.refresh();
    }
    private refresh(): void {
        this.request = studioRequestId("movie-inspect");
        try {
            this.ctx.onAction("movie_inspect", { request_id: this.request, offset: this.offset,
                key_offset: this.keyOffset, tag: this.selected || undefined });
        } catch (error) {
            this.message = error instanceof Error ? error.message : String(error); this.scheduleRender();
        }
    }
    setState(state: MoviePanelState): void {
        if (this.state && state.revision < this.state.revision) return;
        if (state.editor && state.request_id !== this.request) return;
        const changed = !this.state || state.revision !== this.state.revision;
        const controlsChanged = !this.state || state.busy !== this.state.busy;
        this.state = state;
        this.ctx.setBadge(state.version === 2 ? `${state.n_tracks} tracks` : state.version === 1 ? "Legacy" : "Empty");
        if (!this.durationTouched && state.duration_ms) this.duration = String(state.duration_ms / 1000);
        if (state.editor) {
            this.tracks = state.editor.tracks; this.track = state.editor.track;
            this.representations = state.editor.representations ?? []; this.targets = state.editor.targets ?? [];
            if (this.selected && !this.track) {
                this.selected = ""; this.replace = false;
                this.message = "The selected track is no longer present. Your draft is kept.";
            }
        }
        if (changed && !state.editor && this.visible) this.refresh();
        if (changed || controlsChanged || state.editor) this.scheduleRender();
        else this.updateProgress();
    }
    override updateStudioAction(result: StudioActionResult): void {
        if (result.request_id !== this.pending) return;
        this.pending = null;
        this.message = result.ok ? "Completed." : result.error_message || "The Movie operation could not complete.";
        if (result.ok) {
            if (this.pendingDuration === this.duration) this.durationTouched = false;
            if (this.pendingAction && ["movie_start", "movie_set_duration", "movie_clear", "movie_set_key",
                "movie_capture_key", "movie_remove_track", "movie_remove_key"].includes(this.pendingAction)) {
                this.replace = false; this.confirmation = "";
                this.draftRevision = this.durationTouched ? this.state?.revision ?? null : null;
            }
        }
        this.pendingDuration = null; this.pendingAction = null;
        if (this.visible) this.refresh();
        this.scheduleRender();
    }
    private submit(action: PanelAction, details: Record<string, unknown> = {}): void {
        const request_id = studioRequestId(action);
        this.pending = request_id; this.pendingAction = action; this.message = "Working…";
        this.pendingDuration = ["movie_start", "movie_set_duration"].includes(action) ? this.duration : null;
        try {
            this.ctx.onAction(action, { revision: this.state?.revision, ...details, request_id });
        } catch (error) {
            this.pending = null; this.pendingDuration = null; this.pendingAction = null;
            this.message = error instanceof Error ? error.message : String(error);
        }
        this.scheduleRender();
    }
    private markDraft(): void {
        if (this.tab === "timeline" && this.draftRevision === null) this.draftRevision = this.state?.revision ?? null;
    }
    private get staleDraft(): boolean { return this.draftRevision !== null && this.draftRevision !== this.state?.revision; }
    private useKeptDraft(): void {
        this.draftRevision = this.state?.revision ?? null;
        this.message = "Draft kept. Review its targets and timing before saving.";
        this.refresh(); this.scheduleRender();
    }
    private button(label: string, action: () => void, enabled = true): HTMLButtonElement {
        const button = makeButton(label, action);
        button.disabled = !this.hasAuthority || !enabled; return button;
    }
    private field(label: string, key: string, value: string, change: (value: string) => void,
        type = "text", disabled = false): HTMLElement {
        const row = document.createElement("label"); row.textContent = label;
        Object.assign(row.style, { display: "flex", flexDirection: "column", gap: "4px", fontSize: "11px" });
        const input = document.createElement("input"); input.type = type; input.value = value;
        input.disabled = disabled;
        input.setAttribute(`data-molsysviewer-movie-${key}`, "true");
        Object.assign(input.style, { width: "100%", minWidth: "0", boxSizing: "border-box", color: "#f4f4f5",
            background: "rgba(0,0,0,0.28)", border: "1px solid rgba(255,255,255,0.16)", padding: "6px", borderRadius: "5px" });
        if (type === "number") input.step = "any";
        input.addEventListener("input", () => { this.markDraft(); change(input.value); }); row.appendChild(input); return row;
    }
    private check(label: string, checked: boolean, change: (value: boolean) => void): HTMLElement {
        const row = document.createElement("label"), input = document.createElement("input");
        input.type = "checkbox"; input.checked = checked; input.addEventListener("change", () => { this.markDraft(); change(input.checked); });
        row.append(input, document.createTextNode(label)); row.style.fontSize = "11px"; return row;
    }
    private select(label: string, values: Array<string | { value: string; label: string }>, current: string,
        change: (value: string) => void, disabled = false): HTMLElement {
        const row = document.createElement("label"); row.textContent = label;
        Object.assign(row.style, { display: "flex", flexDirection: "column", gap: "4px", fontSize: "11px" });
        const select = makeStyledSelect(values, current, value => { this.markDraft(); change(value); }); select.disabled = disabled;
        select.setAttribute("aria-label", label);
        row.appendChild(select); return row;
    }
    protected paint(): void {
        if (!this.host) return;
        this.host.replaceChildren(); this.host.appendChild(makeSectionHeader("Movie · experimental"));
        this.host.appendChild(note("Prepare scene objects first, then record their camera, structure and visual changes. The Movie is included when you save work in Export."));
        if (!this.hasAuthority) {
            this.host.appendChild(note("Movie authoring requires a connected Python session. This exported view has no editing authority.")); return;
        }
        const tabs = document.createElement("div"); tabs.setAttribute("role", "tablist"); tabs.setAttribute("aria-label", "Movie workflow");
        Object.assign(tabs.style, { display: "flex", gap: "5px", margin: "8px 0" });
        for (const [value, label] of [["timeline", "Timeline"], ["preview", "Preview"], ["export", "Export"]]) {
            const button = this.button(label, () => { this.tab = value; this.scheduleRender(); });
            button.setAttribute("role", "tab"); button.setAttribute("aria-selected", String(this.tab === value));
            button.setAttribute("data-molsysviewer-movie-tab", value); tabs.appendChild(button);
        }
        this.host.appendChild(tabs);
        const status = note(this.message || (this.state ? `${this.state.n_tracks} tracks · ${(this.state.duration_ms / 1000).toFixed(2)} s` : "Reading Movie…"));
        status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite"); this.host.appendChild(status);
        if (this.staleDraft) {
            this.host.appendChild(note("The Movie changed in Python or another window. Your draft is kept; review the updated plan before using it."));
            this.host.appendChild(this.button("Use kept draft", () => this.useKeptDraft(), !this.state?.busy && this.pending === null));
        }
        if (this.state && !this.state.live_available) this.host.appendChild(note("Live Movie actions require a compatible renderer and an integrated async host. Timeline editing remains available; this host has not advertised that live route."));
        if (this.state?.busy) {
            const progress = note(""); progress.setAttribute("data-molsysviewer-movie-progress", "true"); this.host.appendChild(progress);
            if (this.state.job_id) this.host.appendChild(this.button("Cancel operation", () => this.submit("movie_cancel", { job_id: this.state?.job_id })));
            else this.host.appendChild(note("This operation was started from Python."));
        }
        if (this.tab === "timeline") this.timeline();
        else if (this.tab === "preview") this.preview();
        else this.export();
        this.updateProgress();
    }
    private updateProgress(): void {
        const el = this.host?.querySelector('[data-molsysviewer-movie-progress]');
        if (el) el.textContent = this.state?.progress
            ? `Exporting frame ${this.state.progress.frames_written} of ${this.state.progress.total_frames}`
            : this.state?.busy === "movie_play" ? "Preview is running. Pause to inspect the last drawn moment." : "Waiting for the operation to finish…";
    }
    private get editable(): boolean { return !!this.state && !this.state.busy && this.pending === null && !this.staleDraft; }
    private timeline(): void {
        const setup = card();
        setup.appendChild(this.field("Duration (seconds)", "duration", this.duration, value => { this.duration = value; this.durationTouched = true; }, "number"));
        if (this.state?.version !== 2 || this.confirmation === "new") {
            if (this.state?.version === 1) setup.appendChild(note("A legacy Movie is loaded. Reviewed migration remains available in Python; starting here replaces that plan."));
            const replacing = this.state?.version != null;
            setup.appendChild(this.button(replacing ? "Confirm new Movie from this canvas" : "Capture initial scene", () => this.submit("movie_start",
                { duration_ms: Number(this.duration) * 1000, confirmed: replacing && this.confirmation === "new" }), this.editable && !!this.state?.system_loaded && !!this.state?.live_available && (!replacing || this.confirmation === "new")));
            if (replacing && this.confirmation !== "new") setup.appendChild(this.button("Start a new Movie…", () => { this.confirmation = "new"; this.scheduleRender(); }, this.editable));
            if (this.confirmation === "new") setup.appendChild(this.button("Keep current Movie", () => { this.confirmation = ""; this.scheduleRender(); }));
            this.host!.appendChild(setup); return;
        }
        setup.appendChild(this.button("Set duration", () => this.submit("movie_set_duration", { duration_ms: Number(this.duration) * 1000 }), this.editable));
        setup.appendChild(this.button("New Movie…", () => { this.confirmation = "new"; this.scheduleRender(); }, this.editable));
        setup.appendChild(this.button(this.confirmation === "clear" ? "Confirm remove Movie plan" : "Remove Movie plan…", () => {
            if (this.confirmation === "clear") this.submit("movie_clear", { confirmed: true });
            else { this.confirmation = "clear"; this.scheduleRender(); }
        }, this.editable));
        const settings = document.createElement("details"), summary = document.createElement("summary");
        settings.open = this.settingsOpen; summary.textContent = `Movie settings · ${this.state!.duration_ms / 1000} s`;
        settings.append(summary, setup); settings.addEventListener("toggle", () => { this.settingsOpen = settings.open; });
        this.host!.appendChild(settings);
        const list = card(); list.appendChild(makeSectionHeader("Tracks"));
        list.appendChild(this.button("New track", () => {
            this.selected = ""; this.track = null; this.tag = ""; this.domain = "camera"; this.property = "pose";
            this.target = ""; this.at = "0"; this.replace = false;
            this.draftRevision = this.state?.revision ?? null;
            this.scheduleRender();
        }, this.editable));
        for (const track of this.tracks) {
            const button = this.button(`${track.tag} · ${labels[track.property] ?? track.property} · ${track.n_keys} keys`, () => {
                this.selected = track.tag; this.tag = track.tag; this.domain = track.target.domain;
                this.target = track.target.tag ?? ""; this.property = track.property; this.keyOffset = 0; this.track = null;
                this.defaultValue();
                this.draftRevision = this.state?.revision ?? null;
                this.replace = false; this.refresh();
            }); button.setAttribute("data-molsysviewer-movie-track", track.tag); list.appendChild(button);
        }
        if (this.offset > 0) list.appendChild(this.button("Previous tracks", () => { this.offset = Math.max(0, this.offset - 20); this.refresh(); }));
        if (this.offset + this.tracks.length < this.state!.n_tracks) list.appendChild(this.button("Next tracks", () => { this.offset += 20; this.refresh(); }));
        if (this.state!.n_tracks) this.host!.appendChild(list);
        this.editor();
    }
    private editor(): void {
        const form = card(); form.appendChild(makeSectionHeader(this.selected ? "Edit track" : "New track"));
        form.appendChild(this.field("Track name", "track-name", this.tag, value => { this.tag = value; }, "text", !!this.selected));
        form.appendChild(this.select("Target", Object.keys(properties), this.domain, value => {
            this.domain = value; this.property = properties[value][0]; this.defaultValue(); this.scheduleRender();
        }, !!this.selected));
        if (!["camera", "structure", "whole", "scene"].includes(this.domain)) {
            const field = this.field("Object name in the initial scene", "target", this.target, value => { this.target = value; }, "text", !!this.selected);
            const input = field.querySelector("input")!, choices = document.createElement("datalist");
            choices.id = studioRequestId("movie-targets"); input.setAttribute("list", choices.id);
            for (const target of this.targets.filter(target => target.domain === this.domain)) {
                const option = document.createElement("option"); option.value = target.tag ?? ""; choices.appendChild(option);
            }
            field.appendChild(choices); form.appendChild(field);
        }
        form.appendChild(this.select("Property", properties[this.domain].map(value => ({ value, label: labels[value] })), this.property,
            value => { this.property = value; this.defaultValue(); this.scheduleRender(); }, !!this.selected));
        form.appendChild(this.field("Key time (seconds)", "key-time", this.at, value => { this.at = value; }, "number"));
        if (["pose", "color", "alpha", "background", "lighting"].includes(this.property)) {
            form.appendChild(this.select("Transition to next key", ["linear", "ease-in", "ease-out", "ease-in-out"], this.easing, value => { this.easing = value; }));
        } else form.appendChild(note("This property changes at the saved key time; it is held between keys."));
        if (this.property === "visible") form.appendChild(this.check("Visible", this.shown, value => { this.shown = value; }));
        else if (this.property === "representation") form.appendChild(this.select("Representation", this.representations, this.value, value => { this.value = value; }));
        else if (this.property !== "pose") {
            form.appendChild(this.field(this.property === "lighting" ? "Ambient intensity (0–1)" : labels[this.property], "value", this.value,
                value => { this.value = value; }, ["index", "alpha", "lighting"].includes(this.property) ? "number" : ["color", "background"].includes(this.property) ? "color" : "text"));
            if (this.property === "lighting") form.appendChild(this.field("Diffuse intensity (0–1)", "diffuse", this.secondValue, value => { this.secondValue = value; }, "number"));
        }
        if (this.domain === "shape" && this.property !== "visible") form.appendChild(note("Shape material tracks currently support spheres."));
        form.appendChild(this.check("Replace a key at the same time", this.replace, value => { this.replace = value; }));
        form.appendChild(this.button(this.property === "pose" ? "Capture this camera as key" : "Save key", () => {
            const target = { domain: this.domain, ...(!["camera", "structure", "whole", "scene"].includes(this.domain) ? { tag: this.target } : {}) };
            const value = this.property === "visible" ? this.shown : ["index", "alpha"].includes(this.property) ? Number(this.value)
                : ["color", "background"].includes(this.property) ? Number.parseInt(this.value.slice(1), 16)
                : this.property === "lighting" ? { ambient: Number(this.value), diffuse: Number(this.secondValue) } : this.value;
            this.submit(this.property === "pose" ? "movie_capture_key" : "movie_set_key", { tag: this.tag, target,
                property: this.property, time_ms: Number(this.at) * 1000, easing: this.easing, value, replace: this.replace });
        }, this.editable && (this.property !== "pose" || !!this.state?.live_available)));
        if (this.track) {
            form.appendChild(makeSectionHeader("Saved keys"));
            for (const key of this.track.keys) {
                const row = document.createElement("div");
                row.appendChild(this.button(`Edit ${(key.time_ms / 1000).toFixed(3)} s`, () => {
                    this.markDraft();
                    this.at = String(key.time_ms / 1000); this.easing = key.easing ?? "linear"; this.replace = true;
                    this.shown = !!key.value;
                    this.value = ["color", "background"].includes(this.property) ? `#${Number(key.value).toString(16).padStart(6, "0")}`
                        : this.property === "lighting" ? String(key.value.ambient) : String(key.value);
                    if (this.property === "lighting") this.secondValue = String(key.value.diffuse);
                    this.scheduleRender();
                }));
                if (this.track.n_keys > 1) row.appendChild(this.button("Remove key", () => this.submit("movie_remove_key", { tag: this.selected, time_ms: key.time_ms }), this.editable));
                form.appendChild(row);
            }
            if (this.keyOffset > 0) form.appendChild(this.button("Previous keys", () => { this.keyOffset = Math.max(0, this.keyOffset - 100); this.refresh(); }));
            if (this.keyOffset + this.track.keys.length < this.track.n_keys) form.appendChild(this.button("Next keys", () => { this.keyOffset += 100; this.refresh(); }));
            form.appendChild(this.button(this.confirmation === "track" ? "Confirm remove track" : "Remove track…", () => {
                if (this.confirmation === "track") this.submit("movie_remove_track", { tag: this.selected, confirmed: true });
                else { this.confirmation = "track"; this.scheduleRender(); }
            }, this.editable));
        }
        form.appendChild(workflowHelp("movie", ["Prepare regions, interactions and labels before recording the initial scene.",
            "For a camera move, add a key, rotate or zoom the canvas, then capture another camera key at a later time.",
            "Time and duration are shown in seconds; the Python Movie API stores milliseconds. Edits do not move the scene until preview or seek."]));
        this.host!.appendChild(form);
    }
    private preview(): void {
        const root = card(), enabled = this.state?.version === 2 && this.state.live_available;
        root.appendChild(this.field("Movie time (seconds)", "preview-time", this.previewAt, value => { this.previewAt = value; }, "number"));
        const slider = document.createElement("input"); slider.type = "range"; slider.min = "0";
        slider.max = String((this.state?.duration_ms ?? 0) / 1000); slider.step = "0.01"; slider.value = this.previewAt;
        slider.setAttribute("aria-label", "Movie time"); slider.addEventListener("input", () => {
            this.previewAt = slider.value;
            const input = this.host?.querySelector<HTMLInputElement>('[data-molsysviewer-movie-preview-time]');
            if (input) input.value = this.previewAt;
        });
        root.appendChild(slider);
        root.appendChild(this.button("Go to time", () => this.submit("movie_seek", { time_ms: Number(this.previewAt) * 1000 }), enabled && this.editable));
        root.appendChild(this.check("Loop preview", this.loop, value => { this.loop = value; }));
        root.appendChild(this.button("Play", () => this.submit("movie_play", { time_ms: Number(this.previewAt) * 1000, loop: this.loop }), enabled && this.editable));
        root.appendChild(this.button("Pause", () => this.submit("movie_pause"), this.state?.busy === "movie_play"));
        root.appendChild(this.button(this.confirmation === "reset" ? "Confirm restore initial scene" : "Restore initial scene…", () => {
            if (this.confirmation === "reset") this.submit("movie_reset", { confirmed: true });
            else { this.confirmation = "reset"; this.scheduleRender(); }
        }, enabled && this.editable));
        root.appendChild(note("Restoring the initial scene replaces current scene objects with the recorded baseline. The molecular system and scientific analyses are preserved."));
        this.host!.appendChild(root);
    }
    private export(): void {
        const root = card();
        root.appendChild(this.field("Output path in Python session (.mp4, .webm or .zip)", "path", this.path, value => { this.path = value; }));
        root.appendChild(this.field("Frames per second", "fps", this.fps, value => { this.fps = value; }));
        root.appendChild(this.field("Width (pixels)", "width", this.width, value => { this.width = value; }, "number"));
        root.appendChild(this.field("Height (pixels)", "height", this.height, value => { this.height = value; }, "number"));
        root.appendChild(this.check("Allow replacing an existing output file", this.overwrite, value => { this.overwrite = value; }));
        root.appendChild(this.check("Include visible plots and legends; refuse unsupported composition", this.includeOverlays, value => { this.includeOverlays = value; }));
        root.appendChild(note("Native labels are included. Visible plot/legend composition is not yet available: hide those overlays or explicitly exclude them. Output is written in the Python session, including when that session runs remotely."));
        root.appendChild(this.button("Export Movie", () => this.submit("movie_export", { path: this.path, fps: this.fps,
            width_px: Number(this.width), height_px: Number(this.height), overwrite: this.overwrite,
            include_overlays: this.includeOverlays }), this.editable && this.state?.version === 2 && !!this.state?.live_available));
        if (this.state?.last_output) root.appendChild(note(`Saved ${this.state.last_output.path} · ${this.state.last_output.bytes} bytes`));
        this.host!.appendChild(root);
    }
    private defaultValue(): void {
        if (!["pose", "color", "alpha", "background", "lighting"].includes(this.property)) this.easing = "linear";
        this.value = this.property === "representation" ? "ball-and-stick" : ["color", "background"].includes(this.property)
            ? "#34d399" : this.property === "text" ? "" : this.property === "alpha" ? "1" : this.property === "lighting" ? "0.4" : "0";
        this.secondValue = "0.6";
    }
}
