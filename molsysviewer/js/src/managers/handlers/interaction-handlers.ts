import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { addNetworkLinksFromPython } from "../../shapes";
import { setSubtreeVisibility } from "molstar/lib/mol-plugin/behavior/static/state";

export type InteractionParticipant = { role: string; atom_indices: number[] };
export type InteractionObservation = {
    occurrence_index: number; interaction_type: string; participants: InteractionParticipant[];
    query_offset?: number;
    measurements: Record<string, number | null>; measure_units?: Record<string, string>;
    start?: number[]; end?: number[]; image_vectors?: number[][] | null; evidence?: string;
    segment_index?: number; geometry?: "atom_pair" | "participant_centroids";
};
export type InteractionSummary = {
    tag: string; analysis_name: string; analysis_revision: string; query_revision: string; layer_tag: string; hidden: boolean; layer_hidden?: boolean;
    style: { color: number; alpha: number; radius_nm: number; radius_unit: "nm" };
    filter: { selection: "all" | number[]; selection_2: "all" | number[] | null; mode: string;
        exclusive: boolean; structure_indices: "all" | number[]; interaction_types: string[] | null };
    projection_revision?: number; frame: number; status: string; n_observations: number; n_supported: number; n_skipped: number;
    n_segments?: number;
};
export type InteractionFrame = InteractionSummary & {
    op: "set_interaction_frame"; coordinate_unit: "nm"; links: InteractionObservation[]; request_id?: number;
};
export type InteractionSeries = Omit<InteractionFrame, "op" | "frame" | "status" | "links"> & {
    op: "set_interaction_series"; frames: Array<Pick<InteractionFrame, "frame" | "status" | "links" | "n_observations" | "n_supported" | "n_skipped" | "n_segments">>;
};
export type InteractionAnalysisSummary = {
    name: string; method: string; n_occurrences: number; n_evaluated_structures: number; n_structures: number;
    interaction_types: string[]; n_references: number; parameters: Record<string, unknown>;
    measure_units: Record<string, string>; software: Record<string, string>;
};
export type InteractionSummariesMessage = {
    op: "set_interaction_summaries"; interactions: InteractionSummary[]; analyses: InteractionAnalysisSummary[];
    projection_revision?: number; frame: number; system_loaded: boolean; backend_available?: boolean;
    calculation_families?: InteractionCalculationFamily[];
};
export type InteractionCalculationFamily = { kind: string; label: string; default_parameters: Record<string, unknown> };
export type InteractionInspection = {
    tag: string; frame: number; analysis_name: string; analysis_revision: string; query_revision: string; method: string;
    parameters: Record<string, unknown>; software: Record<string, string>; evaluation_scope: unknown;
    measure_units: Record<string, string>; offset: number; total: number; status: string;
    observations: InteractionObservation[]; limit_reason?: string | null;
    next_offset?: number | null;
};
const escapeLabel = (value: string) => value.replace(/[&<>"']/g, c => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"}[c]!));

/** One live frame per set; exports contain bounded, precompiled frame geometry. */
export class InteractionHandlers {
    private refs = new Map<string, string>();
    private series = new Map<string, InteractionSeries>();
    private summaries: InteractionSummary[] = [];
    private frame = 0;
    private request = 0;
    private pending: number | null = null;
    private work: Promise<void> = Promise.resolve();
    private generation = 0;
    private latestRevision = -1;
    private tokens = new Map<string, object>();
    private requestTimeout: ReturnType<typeof setTimeout> | null = null;
    constructor(private plugin: PluginContext, private ctx: {
        register: (ref: string, tag: string) => void; unregister: (ref: string, tag: string) => void;
        notify: (message: unknown) => void; summaries: (items: InteractionSummary[], frame: number) => void;
        layerHidden: (tag: string) => boolean;
    }) {}

    get currentFrame(): number { return this.frame; }
    setSummaries(items: InteractionSummary[], revision = -1): boolean {
        if (revision < this.latestRevision && revision !== -1) return false;
        this.latestRevision = Math.max(this.latestRevision, revision);
        for (const tag of this.tokens.keys()) if (!items.some(item => item.tag === tag)) this.drop(tag);
        this.summaries = items;
        this.latestRevision = Math.max(this.latestRevision, ...items.map(item => item.projection_revision ?? -1));
        if (items.some(item => item.frame !== this.frame)) {
            this.pending = null; this.requestedFrame = -1; this.requestFrame();
        }
        return true;
    }
    async setSeries(message: InteractionSeries) {
        this.series.set(message.tag, message);
        await this.apply({ ...message, ...message.frames[this.frame], op: "set_interaction_frame" });
    }
    async apply(message: InteractionFrame) {
        if ((message.projection_revision ?? this.latestRevision) < this.latestRevision) return;
        this.latestRevision = Math.max(this.latestRevision, message.projection_revision ?? -1);
        if (message.request_id !== undefined && !this.summaries.some(item => item.tag === message.tag)) return;
        if (message.style.radius_unit !== "nm") throw new Error("Interaction radius requires explicit nm units.");
        if (message.coordinate_unit !== "nm") throw new Error("Interaction geometry requires explicit nm units.");
        if (message.request_id !== undefined && message.request_id !== this.pending) return;
        if (message.frame !== this.frame) return;
        const generation = this.generation;
        if (!this.tokens.has(message.tag)) this.tokens.set(message.tag, {});
        const token = this.tokens.get(message.tag);
        const valid = () => generation === this.generation && this.tokens.get(message.tag) === token
            && message.frame === this.frame && (message.projection_revision ?? this.latestRevision) >= this.latestRevision;
        this.work = this.work.then(async () => {
            if (!valid()) return;
            await this.remove(message.tag);
            if (!valid()) return;
            if (message.links.length) {
                const ref = await addNetworkLinksFromPython(this.plugin, {
                    mode: "coordinates", tag: message.tag, dashed: true,
                    interaction: { analysis_name: message.analysis_name, analysis_revision: message.analysis_revision,
                                   query_revision: message.query_revision, frame: message.frame, observations: message.links },
                    coordinate_pairs: message.links.map(link => [link.start!.map(v => v * 10), link.end!.map(v => v * 10)] as [[number, number, number], [number, number, number]]),
                    radii: message.style.radius_nm * 10, colors: message.style.color, alpha: message.style.alpha,
                    labels: message.links.map(link => escapeLabel(`${link.interaction_type} · occurrence ${link.occurrence_index}${link.geometry === "participant_centroids" ? " · participant-centroid guide" : ""} · ${link.participants.map(p => `${p.role}: ${p.atom_indices.join(",")}`).join(" → ")}`)),
                });
                if (ref) {
                    if (!valid()) {
                        await PluginCommands.State.RemoveObject(this.plugin, {
                            state: this.plugin.state.data, ref, removeParentGhosts: true,
                        });
                        return;
                    }
                    this.refs.set(message.tag, ref);
                    this.ctx.register(ref, message.tag);
                    setSubtreeVisibility(this.plugin.state.data, ref, message.hidden || this.ctx.layerHidden(message.layer_tag));
                }
            }
            this.summaries = this.summaries.map(item => item.tag === message.tag ? { ...item, ...message } : item);
            this.ctx.summaries(this.summaries, this.frame);
        }).catch(error => {
            console.error("[MolSysViewer] interaction render failed", error);
            if (valid()) {
                this.summaries = this.summaries.map(item => item.tag === message.tag ? { ...item, status: "render-error", n_supported: 0, n_segments: 0 } : item);
                this.ctx.summaries(this.summaries, this.frame);
            }
        });
        await this.work;
    }
    finishResponse(requestId: number) {
        if (requestId === this.pending) {
            this.pending = null;
            if (this.requestTimeout) clearTimeout(this.requestTimeout);
            this.requestFrame();
        }
    }
    onFrame(frame: number) {
        if (frame === this.frame) return;
        this.frame = frame;
        this.generation++;
        this.summaries = this.summaries.map(item => ({ ...item, frame, status: "pending", n_observations: 0, n_supported: 0, n_segments: 0, n_skipped: 0 }));
        this.ctx.summaries(this.summaries, frame);
        // Hide immediately: no links belonging to the preceding structure.
        for (const ref of this.refs.values()) setSubtreeVisibility(this.plugin.state.data, ref, true);
        if (this.series.size) {
            for (const message of this.series.values()) {
                void this.apply({ ...message, ...message.frames[frame], op: "set_interaction_frame" });
            }
        } else this.requestFrame();
    }
    private requestedFrame = -1;
    private requestFrame() {
        if (!this.summaries.length || this.pending !== null || this.requestedFrame === this.frame) return;
        this.requestedFrame = this.frame;
        this.pending = ++this.request;
        this.ctx.notify({ event: "request_interaction_frame", frame: this.frame, request_id: this.pending });
        if (this.requestTimeout) clearTimeout(this.requestTimeout);
        this.requestTimeout = setTimeout(() => {
            this.pending = null;
            this.summaries = this.summaries.map(item => ({ ...item, status: "unavailable" }));
            this.ctx.summaries(this.summaries, this.frame);
        }, 10000);
    }
    private async remove(tag: string) {
        const ref = this.refs.get(tag);
        if (!ref) return;
        this.refs.delete(tag);
        this.ctx.unregister(ref, tag);
        if (this.plugin.state.data.cells.has(ref)) await PluginCommands.State.RemoveObject(this.plugin, {
            state: this.plugin.state.data, ref, removeParentGhosts: true,
        });
    }
    drop(tag: string) { this.tokens.delete(tag); this.series.delete(tag); this.summaries = this.summaries.filter(item => item.tag !== tag); void this.remove(tag); }
    clear() { if (this.requestTimeout) clearTimeout(this.requestTimeout); this.generation++; this.tokens.clear(); this.series.clear(); this.summaries = []; this.pending = null; this.requestedFrame = -1; for (const tag of this.refs.keys()) void this.remove(tag); }
}
