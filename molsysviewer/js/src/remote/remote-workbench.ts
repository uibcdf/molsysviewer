import type { ActiveSelectionPayload } from "../managers/active-selection";
import type { ViewerMessage } from "../messages/viewer-messages";
import {
    GroupPanel,
    type SavedSelectionSummary,
} from "../ui/group-panel";
import { ProjectedTrajectoryControls } from "../ui/projected-trajectory-controls";
import { RemoteFileControls, type RemoteUploadResult } from "../ui/remote-file-controls";
import { RemoteSurfaceControls } from "../ui/remote-surface-controls";

export type RemoteWorkbenchAction = {
    action: string;
    details?: Record<string, unknown>;
};

export type RemoteDownloadArtifact = {
    url: string;
    filename: string;
    mediaType: string;
};

/**
 * UI-only projection adapter shared by remote browser clients.
 *
 * It deliberately owns no Mol* controller or structure.  The same GroupPanel
 * used by the integrated viewer is fed exclusively from Python's canonical
 * panel projection and sends user intent through a transport port.
 */
export class RemoteWorkbench {
    readonly panel: GroupPanel;
    readonly trajectory: ProjectedTrajectoryControls;
    readonly files: RemoteFileControls;
    readonly controls: RemoteSurfaceControls;
    private savedSelections: SavedSelectionSummary[] = [];
    private wholeSummary: any = null;
    private regions: any[] = [];
    private layers: any[] = [];
    private annotations: any[] = [];
    private measurements: any[] = [];
    private shapes: any[] = [];
    private measurementSettings: any = {
        endpointPolicyDefault: "centroid",
        representativeAtoms: { protein: "CA", nucleic: "P", lipid: "P", other: "" },
        structureIndex: 0,
        systemLoaded: false,
    };
    private selectionAtomCount = 0;

    constructor(
        host: HTMLElement,
        private readonly emit: (intent: RemoteWorkbenchAction) => void,
        private readonly download: (artifact: RemoteDownloadArtifact) => void = () => undefined,
        upload: (file: File) => Promise<RemoteUploadResult> = async () => {
            throw new Error("This host does not provide molecular file upload");
        },
    ) {
        this.panel = new GroupPanel(
            host,
            () => undefined,
            () => undefined,
            () => undefined,
            () => undefined,
            () => undefined,
            () => undefined,
            tag => this.emitAction("activate_selection", { tag }),
            tag => this.emitAction("focus_region", { tag }),
            (action, details) => this.emitPanelAction(action, details),
            { floating: true },
        );
        this.panel.setRuntimeVisible(true);
        this.trajectory = new ProjectedTrajectoryControls(host, intent => {
            const { action, ...details } = intent;
            this.emitAction(action, details);
        });
        this.files = new RemoteFileControls(host, upload);
        this.controls = new RemoteSurfaceControls(host, {
            resetView: () => this.emitAction("reset_view"),
            togglePanel: () => this.panel.setExpanded(!this.panel.isExpanded()),
        });
    }

    apply(message: ViewerMessage | Record<string, unknown>): void {
        const msg = message as any;
        switch (msg?.op) {
            case "set_region_summaries":
                this.regions = (Array.isArray(msg.regions) ? msg.regions : [])
                    .filter((item: any) => typeof item?.tag === "string")
                    .map((item: any) => ({
                        ...item,
                        atom_count: typeof item.atom_count === "number"
                            ? item.atom_count
                            : Array.isArray(item.atom_indices) ? item.atom_indices.length : 0,
                        hidden: !!item.hidden,
                        layer: typeof item.layer === "string" ? item.layer : null,
                        mode: item.mode === "dynamic" ? "dynamic" : "static",
                    }))
                    .sort((a: any, b: any) => a.tag.localeCompare(b.tag));
                this.panel.setRegions(this.regions);
                this.panel.setRegionStyleOptions({
                    representations: strings(msg.representations),
                    presets: strings(msg.presets),
                });
                this.refreshLayers();
                return;
            case "set_whole_summary":
                this.wholeSummary = {
                    ...msg,
                    params: record(msg.params),
                    visible: msg.visible !== false,
                    available_attributes: strings(msg.available_attributes),
                    color_schemes: strings(msg.color_schemes),
                    inheriting_region_count: numberOr(msg.inheriting_region_count, 0),
                    none_state_region_count: numberOr(msg.none_state_region_count, 0),
                    covering_layer_count: numberOr(msg.covering_layer_count, 0),
                };
                this.panel.setWholeSummary(this.wholeSummary);
                return;
            case "show_whole":
            case "hide_whole":
                if (this.wholeSummary !== null) {
                    this.wholeSummary = { ...this.wholeSummary, visible: msg.op === "show_whole" };
                    this.panel.setWholeSummary(this.wholeSummary);
                }
                return;
            case "set_layer_summaries":
                this.layers = (Array.isArray(msg.layers) ? msg.layers : [])
                    .filter((item: any) => typeof item?.tag === "string" && ["auto", "user"].includes(item.provenance))
                    .map((item: any) => ({ ...item, hidden: !!item.hidden }));
                this.refreshLayers();
                return;
            case "set_annotation_summaries":
                this.annotations = (Array.isArray(msg.annotations) ? msg.annotations : [])
                    .filter((item: any) => typeof item?.tag === "string")
                    .map(mapAnnotation);
                this.refreshObjects();
                return;
            case "set_measurement_summaries":
                this.measurements = (Array.isArray(msg.measurements) ? msg.measurements : [])
                    .filter((item: any) => typeof item?.tag === "string")
                    .map(mapMeasurement);
                this.measurementSettings = {
                    ...this.measurementSettings,
                    structureIndex: numberOr(msg.structure_index, this.measurementSettings.structureIndex),
                    systemLoaded: msg.system_loaded !== false,
                };
                this.refreshMeasurements();
                this.refreshObjects();
                return;
            case "set_measurement_settings": {
                const source = record(msg.options ?? msg);
                const atoms = record(source.representative_atoms);
                this.measurementSettings = {
                    ...this.measurementSettings,
                    endpointPolicyDefault: typeof source.endpoint_policy_default === "string"
                        ? source.endpoint_policy_default : this.measurementSettings.endpointPolicyDefault,
                    representativeAtoms: {
                        protein: typeof atoms.protein === "string" ? atoms.protein : "CA",
                        nucleic: typeof atoms.nucleic === "string" ? atoms.nucleic : "P",
                        lipid: typeof atoms.lipid === "string" ? atoms.lipid : "P",
                        other: typeof atoms.other === "string" ? atoms.other : "",
                    },
                };
                this.refreshMeasurements();
                return;
            }
            case "set_shape_summaries":
                this.shapes = (Array.isArray(msg.shapes) ? msg.shapes : [])
                    .filter((item: any) => typeof item?.tag === "string")
                    .map(mapShape);
                this.panel.setShapes(this.shapes);
                this.refreshObjects();
                return;
            case "set_section_summaries":
                this.panel.setSections(
                    (Array.isArray(msg.sections) ? msg.sections : []).filter((item: any) => typeof item?.tag === "string"),
                    {
                        activeSelectionCount: numberOr(msg.active_selection_count, 0),
                        systemLoaded: !!msg.system_loaded,
                    },
                );
                return;
            case "set_active_selection":
                this.selectionAtomCount = stringsToNumbers(msg.atom_indices).length;
                this.panel.updateSelection(activeSelection(stringsToNumbers(msg.atom_indices)));
                return;
            case "clear_active_selection":
                this.selectionAtomCount = 0;
                this.panel.updateSelection(activeSelection([]));
                return;
            case "set_history_state":
                this.panel.updateSelectionHistoryState({ canUndo: !!msg.can_undo, canRedo: !!msg.can_redo });
                return;
            case "set_trajectory_summary":
                this.trajectory.apply(msg);
                return;
            case "remote_download_ready":
                if (typeof msg.url === "string" && typeof msg.filename === "string") {
                    this.download({
                        url: msg.url,
                        filename: msg.filename,
                        mediaType: typeof msg.media_type === "string" ? msg.media_type : "application/octet-stream",
                    });
                }
                return;
            case "remote_download_failed":
                console.error("[MolSysViewer remote download]", String(msg.message ?? "Download failed"));
                return;
            case "save_selection": {
                if (typeof msg.tag !== "string") return;
                const atomIndices = stringsToNumbers(msg.atom_indices);
                this.savedSelections = this.savedSelections.filter(item => item.tag !== msg.tag);
                this.savedSelections.push({
                    tag: msg.tag,
                    atom_count: atomIndices.length,
                    atom_indices: atomIndices,
                    element_level: typeof msg.element_level === "string" ? msg.element_level : undefined,
                });
                this.savedSelections.sort((a, b) => a.tag.localeCompare(b.tag));
                this.panel.setSavedSelections(this.savedSelections);
                return;
            }
            case "set_selection_tag":
                if (typeof msg.tag === "string" && typeof msg.new_tag === "string") {
                    this.savedSelections = this.savedSelections.map(item => item.tag === msg.tag ? { ...item, tag: msg.new_tag } : item);
                    this.panel.setSavedSelections(this.savedSelections);
                }
                return;
            case "delete_selection":
                this.savedSelections = this.savedSelections.filter(item => item.tag !== msg.tag);
                this.panel.setSavedSelections(this.savedSelections);
                return;
            case "clear_selections":
                this.savedSelections = [];
                this.panel.setSavedSelections([]);
                return;
            case "whole_details":
                this.panel.updateWholeDetails(msg);
                return;
            case "region_details":
                this.panel.updateRegionDetails(msg);
                return;
            case "measurement_series":
                this.panel.updateMeasurementSeries({
                    tag: String(msg.tag ?? ""),
                    requestId: typeof msg.request_id === "number" ? msg.request_id : null,
                    unit: typeof msg.unit === "string" ? msg.unit : "",
                    nFrames: numberOr(msg.n_frames, 0),
                    sparkline: stringsToNumbers(msg.sparkline),
                    sparklineIndices: stringsToNumbers(msg.sparkline_indices),
                    seriesIndex: typeof msg.series_index === "number" ? msg.series_index : null,
                });
                return;
        }
    }

    dispose(): void {
        this.controls.dispose();
        this.files.dispose();
        this.trajectory.dispose();
        this.panel.dispose();
    }

    get activeSelectionAtomCount(): number {
        return this.selectionAtomCount;
    }

    private emitPanelAction(action: string, details?: Record<string, unknown>): void {
        const direct: Record<string, string> = {
            undo_active_selection: "scene_history_undo",
            redo_active_selection: "scene_history_redo",
            begin_scene_history_coalescing: "scene_history_coalescing_begin",
            end_scene_history_coalescing: "scene_history_coalescing_end",
            selection_query_preview_request: "selection_query_preview_request",
        };
        const runtimeAction = direct[action];
        if (runtimeAction) {
            this.emit({ action: runtimeAction, details });
            return;
        }
        this.emitAction(action, details);
    }

    private emitAction(action: string, details?: Record<string, unknown>): void {
        this.emit({ action: "interaction_context_action", details: { action, ...details } });
    }

    private refreshMeasurements(): void {
        this.panel.setMeasurements(this.measurements, this.measurementSettings);
    }

    private refreshLayers(): void {
        this.panel.setLayers(this.layers);
        this.panel.setRegions(this.regions);
    }

    private refreshObjects(): void {
        this.panel.setAnnotations(this.annotations, { systemLoaded: true, activeSelectionCount: 0 });
        this.refreshMeasurements();
        this.panel.setShapes(this.shapes);
        this.panel.setLayerObjects([
            ...this.annotations.map((item: any) => layerObject("annotation", item)),
            ...this.measurements.map((item: any) => layerObject("measurement", item)),
            ...this.shapes.map((item: any) => layerObject("shape", item)),
        ]);
    }
}

function strings(value: unknown): string[] {
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function stringsToNumbers(value: unknown): number[] {
    return Array.isArray(value) ? value.filter((item): item is number => typeof item === "number" && Number.isFinite(item)) : [];
}

function record(value: unknown): Record<string, any> {
    return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, any> : {};
}

function numberOr(value: unknown, fallback: number): number {
    return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function activeSelection(atomIndices: number[]): ActiveSelectionPayload {
    return {
        event: "interaction_active_selection_changed",
        source_kind: atomIndices.length ? "element" : "empty",
        target_level: atomIndices.length ? "mixed" : "none",
        element_level: atomIndices.length ? "group" : "none",
        items: [], atom_indices: atomIndices, group_indices: [], component_indices: [],
        chain_indices: [], molecule_indices: [], entity_indices: [],
        count_atoms: atomIndices.length, count_groups: 0, count_shapes: 0, count_annotations: 0,
    };
}

function mapAnnotation(item: any): any {
    return {
        ...item,
        layerTag: typeof item.layer_tag === "string" ? item.layer_tag : undefined,
        nAtoms: numberOr(item.n_atoms, 0),
        atomIndices: stringsToNumbers(item.atom_indices),
        hidden: !!item.hidden,
        style: record(item.style),
        anchor: record(item.anchor),
        broken: !!item.broken,
        brokenReason: typeof item.broken_reason === "string" ? item.broken_reason : undefined,
    };
}

function mapMeasurement(item: any): any {
    return {
        ...item,
        layerTag: typeof item.layer_tag === "string" ? item.layer_tag : undefined,
        picks: numberOr(item.n_picks, 0),
        atomIndices: stringsToNumbers(item.atom_indices),
        endpointLabels: strings(item.endpoint_labels),
        endpointPolicy: typeof item.endpoint_policy === "string" ? item.endpoint_policy : "centroid",
        value: typeof item.value === "number" ? item.value : null,
        unit: typeof item.unit === "string" ? item.unit : "",
        hidden: !!item.hidden,
        broken: !!item.broken,
        brokenReason: typeof item.broken_reason === "string" ? item.broken_reason : undefined,
    };
}

function mapShape(item: any): any {
    return {
        ...item,
        layerTag: typeof item.layer_tag === "string" ? item.layer_tag : undefined,
        title: typeof item.title === "string" ? item.title : item.tag,
        atomIndices: stringsToNumbers(item.atom_indices),
        hidden: !!item.hidden,
        broken: !!item.broken,
        brokenReason: typeof item.broken_reason === "string" ? item.broken_reason : undefined,
    };
}

function layerObject(kind: "annotation" | "measurement" | "shape", item: any): any {
    return {
        kind,
        tag: item.tag,
        owner: item.owner,
        title: item.title ?? item.text ?? item.tag,
        layerTag: item.layerTag,
        hidden: !!item.hidden,
    };
}
