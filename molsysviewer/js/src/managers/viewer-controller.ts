import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";
import { PluginBehaviors } from "molstar/lib/mol-plugin/behavior";
import { StateObjectRef } from "molstar/lib/mol-state";
import { Structure, StructureElement, Unit } from "molstar/lib/mol-model/structure";
import { Shape, ShapeGroup } from "molstar/lib/mol-model/shape";
import { Loci } from "molstar/lib/mol-model/loci";
import { StructureComponentRef } from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";
import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { SortedArray } from "molstar/lib/mol-data/int/sorted-array";
import { ButtonsType } from "molstar/lib/mol-util/input/input-observer";

import { ViewerMessage } from "../messages/viewer-messages";
import { LoadedStructure } from "../plugin/structure";
import { LoaderHandlers } from "./handlers/loader-handlers";
import { AnnotationHandlers } from "./handlers/annotation-handlers";
import { MeasurementHandlers } from "./handlers/measurement-handlers";
import { ShapeHandlers } from "./handlers/shape-handlers";
import { SceneHandlers } from "./handlers/scene-handlers";
import { StateHandlers } from "./handlers/state-handlers";
import { TrajectoryHandlers, TrajectoryState } from "./handlers/trajectory-handlers";
import { MovieHandlers } from "./handlers/movie-handlers";
import { LastMeasurementSummary, RegionSummary, SavedSelectionSummary, ViewerContextMenu } from "../ui/context-menu";
import { MeasurementEndpointPolicy, MeasurementToolAction, MeasurementToolController } from "./measurement-tools";
import { ToolStatusOverlay } from "../ui/tool-status";
import { LegendOverlay } from "../ui/legend-overlay";
import { ActiveSelectionController, ActiveSelectionItem, buildGroupItemsFromStructure, lociToGroupItems } from "./active-selection";
import type { ActiveSelectionPayload } from "./active-selection";
import { GroupPanel } from "../ui/group-panel";
import { WorkbenchPanel } from "../ui/workbench-panel";
import { FloatingPanelShell } from "../ui/floating-panel-shell";
import { MsvPerAtomColorThemeProvider } from "../themes/per-atom-color";
import { HoverTooltip } from "../ui/hover-tooltip";
type SavedSelectionRecord = SavedSelectionSummary & { atom_indices: number[] };

type InteractionKind = "hover" | "click" | "context";
type AddonRuntimeSummary = {
    name: string;
    workspaceTitles: string[];
    panelTitles: string[];
    workbenchTitles: string[];
    contextActionTitles: string[];
    exportHelperTitles: string[];
    active?: boolean;
};
type WorkspaceRuntime = {
    id: string;
    title: string;
    subtitle?: string;
    addon?: string;
    panelCount?: number;
    workbenchSectionCount?: number;
    workbenchSectionTitles?: string[];
    contextActionCount?: number;
    exportHelperCount?: number;
};
type AddonPanelRuntime = {
    key: string;
    workspaceId: string;
    addon: string;
    id: string;
    title: string;
    description?: string;
    entry?: string;
    widget_class?: string;
};
type AddonWorkbenchSectionRuntime = {
    key: string;
    workspaceId: string;
    addon: string;
    title: string;
    itemTitle: string;
    itemSubtitle?: string;
};
type AddonContextActionRuntime = { addon: string; id: string; title: string; target_kinds: string[]; group?: string };
type AddonContextItemRuntime = { addon: string; id: string; title: string; group?: string; order?: number; enabled?: boolean; target_kinds?: string[]; payload?: any };

type InteractionPayload =
    | { event: "interaction_hover" | "interaction_click"; kind: "empty" }
    | {
        event: "interaction_hover" | "interaction_click";
        kind: "structure";
        atom_indices: number[];
        group_indices?: number[];
        chain_indices?: number[];
        entity_indices?: number[];
        group_name?: string;
        chain_name?: string;
        entity_name?: string;
        atom_index?: number;
        atom_id?: string;
        metadata?: {
            chain_id: string;
            group_name: string;
            group_id: string;
            group_index: number;
            atom_name: string;
            element: string;
        };
    }
    | { event: "interaction_hover" | "interaction_click"; kind: "shape"; atom_indices: number[]; tag?: string; shape_name?: string }
    | { event: "interaction_hover" | "interaction_click"; kind: "measurement"; atom_indices: number[]; tag?: string; measurement_name?: string }
    | { event: "interaction_hover" | "interaction_click"; kind: "annotation"; atom_indices: number[]; tag: string; text?: string };

type ContextInteractionPayload =
    | { event: "interaction_context_menu"; kind: "empty"; page_x?: number; page_y?: number }
    | {
        event: "interaction_context_menu";
        kind: "structure";
        atom_indices: number[];
        group_indices?: number[];
        chain_indices?: number[];
        entity_indices?: number[];
        group_name?: string;
        chain_name?: string;
        entity_name?: string;
        page_x?: number;
        page_y?: number;
        atom_index?: number;
        atom_id?: string;
        metadata?: {
            chain_id: string;
            group_name: string;
            group_id: string;
            group_index: number;
            atom_name: string;
            element: string;
        };
    }
    | { event: "interaction_context_menu"; kind: "shape"; atom_indices: number[]; tag?: string; shape_name?: string; page_x?: number; page_y?: number }
    | { event: "interaction_context_menu"; kind: "measurement"; atom_indices: number[]; tag?: string; measurement_name?: string; page_x?: number; page_y?: number }
    | {
        event: "interaction_context_menu";
        kind: "annotation";
        atom_indices: number[];
        tag?: string;
        text?: string;
        page_x?: number;
        page_y?: number;
    };

function normalizeToElementLoci(loci: any): any {
    if (StructureElement.Loci.is(loci)) return loci;
    try {
        return Loci.normalize(loci, "element", true);
    } catch {
        return loci;
    }
}

function lociToAtomIndices(loci: any): number[] {
    const normalized = normalizeToElementLoci(loci);
    if (!StructureElement.Loci.is(normalized)) return [];
    const atomIndices: number[] = [];
    const seen = new Set<number>();
    for (const element of normalized.elements) {
        const size = OrderedSet.size(element.indices);
        for (let i = 0; i < size; i++) {
            const unitIndex = OrderedSet.getAt(element.indices, i);
            const atomIndex = element.unit.elements[unitIndex];
            if (!seen.has(atomIndex)) {
                seen.add(atomIndex);
                atomIndices.push(atomIndex);
            }
        }
    }
    return atomIndices;
}

function shapeTargetFromLoci(loci: any): { atom_indices: number[]; tag?: string; shape_name?: string } | null {
    const shape = ShapeGroup.isLoci(loci) ? loci.shape : Shape.isLoci(loci) ? loci.shape : null;
    if (!shape) return null;
    const sourceData = (shape.sourceData ?? {}) as Record<string, unknown>;
    const atomIndices = Array.isArray(sourceData.atom_indices)
        ? sourceData.atom_indices.map((i) => (typeof i === "number" ? Math.trunc(i) : Number(i))).filter((i) => Number.isFinite(i))
        : [];

    let shapeName = shape.name;
    let groupAtoms: number[] | null = null;
    if (ShapeGroup.isLoci(loci) && loci.groups.length > 0) {
        try {
            const groupIdx = OrderedSet.getAt(loci.groups[0].ids, 0);
            if (typeof shape.getLabel === "function") {
                shapeName = shape.getLabel(groupIdx);
            }
            // Prefer the picked group's own atoms (face/edge/tetra) when the shape
            // exposes them, so a pick selects only that simplex, not the whole shape.
            const perGroup = (sourceData as any).__groupAtoms;
            if (Array.isArray(perGroup) && Array.isArray(perGroup[groupIdx])) {
                groupAtoms = perGroup[groupIdx].map((i: any) => Math.trunc(Number(i))).filter((i: number) => Number.isFinite(i));
            }
        } catch (e) {
            console.warn("[MolSysViewer] Error getting shape group label:", e);
        }
    }

    return {
        atom_indices: groupAtoms ?? atomIndices,
        tag: typeof sourceData.tag === "string" ? sourceData.tag : undefined,
        shape_name: shapeName,
    };
}

function extractAtomMetadata(loci: any) {
    const normalized = normalizeToElementLoci(loci);
    if (!StructureElement.Loci.is(normalized) || normalized.elements.length === 0) return null;
    const element = normalized.elements[0];
    const size = OrderedSet.size(element.indices);
    if (size === 0) return null;
    const unitIndex = OrderedSet.getAt(element.indices, 0);
    const atomIndex = element.unit.elements[unitIndex];
    
    const unit = element.unit;
    const model = unit.model;
    const hierarchy = model?.atomicHierarchy;
    if (!hierarchy) return null;
    
    const residueIndexByAtom = hierarchy.residueAtomSegments.index;
    const chainIndexByAtom = hierarchy.chainAtomSegments.index;
    const atoms = hierarchy.atoms;
    const residues = hierarchy.residues;
    const chains = hierarchy.chains;
    
    const groupIndex = residueIndexByAtom[atomIndex];
    const chainIndex = chainIndexByAtom[atomIndex];
    
    const authSeqId = residues.auth_seq_id.value(groupIndex);
    const compId = atoms.label_comp_id.value(atomIndex);
    const chainId = chains.label_asym_id.value(chainIndex);
    const atomName = atoms.label_atom_id.value(atomIndex);
    const elementSymbol = atoms.type_symbol.value(atomIndex);
    const atomId = atoms.id.value(atomIndex).toString();
    
    return {
        atom_index: atomIndex,
        atom_id: atomId,
        metadata: {
            chain_id: chainId,
            group_name: compId,
            group_id: authSeqId.toString(),
            group_index: groupIndex,
            atom_name: atomName,
            element: elementSymbol,
        }
    };
}

function normalizeContextPayloadFromLoci(loci: any, page_x?: number, page_y?: number): ContextInteractionPayload {
    const groupItems = lociToGroupItems(loci);
    const atomIndices = lociToAtomIndices(loci);
    const meta = extractAtomMetadata(loci);
    if (groupItems.length === 0) {
        if (atomIndices.length > 0) {
            return { event: "interaction_context_menu", kind: "structure", atom_indices: atomIndices, page_x, page_y, ...(meta || {}) };
        }
        const shapeTarget = shapeTargetFromLoci(loci);
        if (shapeTarget) return { event: "interaction_context_menu", kind: "shape", ...shapeTarget, page_x, page_y };
        return { event: "interaction_context_menu", kind: "empty", page_x, page_y };
    }
    const item = groupItems[0];
    return {
        event: "interaction_context_menu",
        kind: "structure",
        atom_indices: item.atom_indices,
        group_indices: item.group_indices,
        chain_indices: item.chain_indices,
        entity_indices: item.entity_indices,
        group_name: item.group_name,
        chain_name: item.chain_name,
        entity_name: item.entity_name,
        page_x,
        page_y,
        ...(meta || {}),
    };
}

export function normalizeInteractionEvent(kind: InteractionKind, ev: any): InteractionPayload {
    if (kind === "context") {
        throw new Error("Use normalizeContextInteractionEvent for context interactions");
    }
    const event = kind === "hover" ? "interaction_hover" : "interaction_click";
    const groupItems = lociToGroupItems(ev?.current?.loci);
    const atomIndices = lociToAtomIndices(ev?.current?.loci);
    const meta = extractAtomMetadata(ev?.current?.loci);
    if (groupItems.length === 0) {
        if (atomIndices.length > 0) {
            return { event, kind: "structure", atom_indices: atomIndices, ...(meta || {}) };
        }
        const shapeTarget = shapeTargetFromLoci(ev?.current?.loci);
        if (shapeTarget) return { event, kind: "shape", ...shapeTarget };
        return { event, kind: "empty" };
    }
    const item = groupItems[0];
    return {
        event,
        kind: "structure",
        atom_indices: item.atom_indices,
        group_indices: item.group_indices,
        chain_indices: item.chain_indices,
        entity_indices: item.entity_indices,
        group_name: item.group_name,
        chain_name: item.chain_name,
        entity_name: item.entity_name,
        ...(meta || {}),
    };
}

export function normalizeContextInteractionEvent(ev: any, fallbackLoci?: any): ContextInteractionPayload {
    const loci = ev?.current?.loci ?? fallbackLoci;
    const page = ev?.page;
    const page_x = typeof page?.[0] === "number" ? page[0] : undefined;
    const page_y = typeof page?.[1] === "number" ? page[1] : undefined;
    return normalizeContextPayloadFromLoci(loci, page_x, page_y);
}

function isSecondaryButton(ev: any): boolean {
    return ev?.button === ButtonsType.Flag.Secondary;
}

type ContextMenuSuppressTarget = Pick<HTMLElement, "addEventListener" | "removeEventListener">;

type ContextMenuHost = ContextMenuSuppressTarget & Pick<HTMLElement, "contains">;

export function suppressCanvasContextMenu(host: ContextMenuHost, ...targets: ContextMenuSuppressTarget[]): () => void {
    let secondaryPressInsideHost = false;
    const globalTarget = typeof window !== "undefined" ? window : undefined;

    const isInsideHost = (event: Event): boolean => {
        const target = event.target;
        if (target != null && host.contains(target as Node)) return true;
        const composedPath = (event as Event & { composedPath?: () => EventTarget[] }).composedPath;
        if (typeof composedPath === "function") {
            return composedPath.call(event).includes(host as unknown as EventTarget);
        }
        return false;
    };

    const onPointerDown = (event: Event) => {
        const pointer = event as Event & { button?: number };
        if (pointer.button === 2 && isInsideHost(event)) {
            secondaryPressInsideHost = true;
        }
    };

    const clearSecondaryPress = () => {
        secondaryPressInsideHost = false;
    };

    const onContextMenu = (event: Event) => {
        const target = event.target;
        const canMatchElement = typeof Element !== "undefined" && target instanceof Element;
        if (canMatchElement && target.closest("[data-molsysviewer-group-strip]")) return;
        if (canMatchElement && target.closest("[data-molsysviewer-context-menu]")) return;
        if (!secondaryPressInsideHost && !isInsideHost(event)) return;
        event.preventDefault();
        event.stopPropagation();
        secondaryPressInsideHost = false;
    };

    for (const target of [host, ...targets]) {
        target.addEventListener("contextmenu", onContextMenu, true);
    }
    globalTarget?.addEventListener("pointerdown", onPointerDown, true);
    globalTarget?.addEventListener("pointerup", clearSecondaryPress, true);
    globalTarget?.addEventListener("pointercancel", clearSecondaryPress, true);
    globalTarget?.addEventListener("contextmenu", onContextMenu, true);

    return () => {
        for (const target of [host, ...targets]) {
            target.removeEventListener?.("contextmenu", onContextMenu, true);
        }
        globalTarget?.removeEventListener("pointerdown", onPointerDown, true);
        globalTarget?.removeEventListener("pointerup", clearSecondaryPress, true);
        globalTarget?.removeEventListener("pointercancel", clearSecondaryPress, true);
        globalTarget?.removeEventListener("contextmenu", onContextMenu, true);
    };
}

/** Extracts annotation or measurement payload from a Mol* interaction event carrying a tooltip tag.
 *  Returns null when the event has no tooltip or the tag is unknown to both registries. */
export function resolveTooltipPayload(
    interactionKind: "hover" | "click",
    ev: any,
    annotations: { hasTag: (t: string) => boolean; getSpec: (t: string) => { text: string; atom_indices: number[] } | undefined },
    measurements: { hasTag: (t: string) => boolean; getSpec: (t: string) => { kind: string; atom_indices: number[] } | undefined },
): InteractionPayload | null {
    const tooltipTag = (ev?.current?.repr as any)?.props?.tooltip?.trim();
    if (!tooltipTag) return null;
    const event = interactionKind === "hover" ? "interaction_hover" : "interaction_click";
    if (annotations.hasTag(tooltipTag)) {
        const spec = annotations.getSpec(tooltipTag);
        return { event, kind: "annotation", tag: tooltipTag, text: spec?.text, atom_indices: spec?.atom_indices ?? [] };
    }
    if (measurements.hasTag(tooltipTag)) {
        const spec = measurements.getSpec(tooltipTag);
        return { event, kind: "measurement", tag: tooltipTag, measurement_name: spec?.kind, atom_indices: spec?.atom_indices ?? [] };
    }
    return null;
}

export function registerInteractionObservers(
    plugin: any,
    notify?: (msg: any) => void,
    openContextMenu?: (payload: ContextInteractionPayload) => void,
    onPrimaryClick?: (ev: any) => void,
    onSecondaryClick?: (ev: any) => void,
    onHover?: (ev: any) => void,
    notifyHover?: (ev: any) => void,
    notifyClick?: (ev: any) => void,
): void {
    const hover = plugin?.behaviors?.interaction?.hover;
    const click = plugin?.behaviors?.interaction?.click;
    if (typeof hover?.subscribe === "function") {
        hover.subscribe((ev: any) => {
            onHover?.(ev);
            if (notifyHover) {
                notifyHover(ev);
            } else {
                notify?.(normalizeInteractionEvent("hover", ev));
            }
        });
    }
    if (typeof click?.subscribe === "function") {
        click.subscribe((ev: any) => {
            if (isSecondaryButton(ev)) {
                const payload = normalizeContextInteractionEvent(ev);
                notify?.(payload);
                onSecondaryClick?.(ev);
                openContextMenu?.(payload);
                return;
            }
            onPrimaryClick?.(ev);
            if (notifyClick) {
                notifyClick(ev);
            } else {
                notify?.(normalizeInteractionEvent("click", ev));
            }
        });
    }
}

export function createMolSysViewerPluginSpec() {
    const spec = DefaultPluginSpec();
    const behaviors = (spec.behaviors ?? []).filter((behavior: any) =>
        behavior.transformer !== PluginBehaviors.Camera.FocusLoci
        && behavior.transformer !== PluginBehaviors.Representation.FocusLoci
    );
    return {
        ...spec,
        behaviors,
    };
}

/**
 * Controller that translates Python messages into Mol* actions and manages state refs.
 * Refactored to use specialized handlers for better maintainability.
 */
export class MolSysViewerController {
    private readonly contextMenu: ViewerContextMenu;
    private readonly measurementTools: MeasurementToolController;
    private readonly activeSelection: ActiveSelectionController;
    private readonly toolStatusOverlay: ToolStatusOverlay;
    private readonly legendOverlay: LegendOverlay;
    private readonly groupPanel: GroupPanel;
    private readonly workbenchPanel: WorkbenchPanel;
    private readonly sharedShell?: FloatingPanelShell;
    private splitResizeObserver?: ResizeObserver;
    private readonly canvasHost: HTMLDivElement;
    private readonly isPanelOnly: boolean;
    private canvasInsetAnimFrame: ReturnType<typeof requestAnimationFrame> | null = null;
    private canvasInsetFrom = { left: 0, right: 0 };
    private canvasInsetTo = { left: 0, right: 0 };
    private canvasInsetStart = 0;
    private readonly canvasInsetDuration = 160; // ms — must match panel slide duration
    private readonly releaseContextMenuSuppression?: () => void;
    private readonly releaseGlobalEscapeHandler?: () => void;
    private lastContextLoci: any = null;
    private lastContextPayload: ContextInteractionPayload | null = null;
    private lastHoverLoci: any = null;
    private lastHoverPayload: InteractionPayload | null = null;
    private lastPrimaryGroupClick: { key: string; time: number } | null = null;
    private savedSelections: SavedSelectionRecord[] = [];
    private readonly workbenchAnnotations = new Map<string, { text: string; layerTag?: string; hidden: boolean; atomIndices: number[] }>();
    private readonly workbenchMeasurements = new Map<string, { kind: string; picks: number; layerTag?: string; hidden: boolean; atomIndices: number[] }>();
    private readonly workbenchShapes = new Map<string, { title: string; subtitle?: string; layerTag?: string; hidden: boolean; atomIndices: number[] }>();
    private workbenchScene: { styleTag?: string; preset?: string; figurePreset?: string; figureScale?: number; figureVariants?: string[] } | null = null;
    private workbenchAddons: AddonRuntimeSummary[] = [];
    private addonWorkspaces: WorkspaceRuntime[] = [];
    private addonPanels: AddonPanelRuntime[] = [];
    private addonRuntimeInitialized = false;
    private workbenchAddonSections: AddonWorkbenchSectionRuntime[] = [];
    private addonContextActions: AddonContextActionRuntime[] = [];
    private addonContextItems: AddonContextItemRuntime[] = [];
    private workbenchActive: { section: "annotations" | "measurements" | "shapes"; tag: string } | null = null;
    private workbenchContext: { section: "annotations" | "shapes"; tag: string } | null = null;
    private syncingPanelExpansion = false;
    private lastPanelMode: "navigate" | "workbench" = "navigate";
    private lastCorePanelMode: "navigate" | "workbench" = "navigate";
    private currentWorkspace = "core";
    private readonly currentWorkspacePanelByWorkspace = new Map<string, string>();
    private activePanelMsgListeners: Array<(msg: any) => void> = [];
    private activePanelCleanup: (() => void) | null = null;
    private activePanelWidgetKey: string | null = null;
    private readonly addonListeners = new Map<string, Map<string, Array<(payload: any) => void>>>();

    public registerAddonListener(addonName: string, eventName: string, cb: (payload: any) => void) {
        if (!this.addonListeners.has(addonName)) {
            this.addonListeners.set(addonName, new Map());
        }
        const addonEvents = this.addonListeners.get(addonName)!;
        if (!addonEvents.has(eventName)) {
            addonEvents.set(eventName, []);
        }
        addonEvents.get(eventName)!.push(cb);
    }

    public unregisterAddonListener(addonName: string, eventName: string, cb: (payload: any) => void) {
        const addonEvents = this.addonListeners.get(addonName);
        if (!addonEvents) return;
        const callbacks = addonEvents.get(eventName);
        if (!callbacks) return;
        const idx = callbacks.indexOf(cb);
        if (idx >= 0) {
            callbacks.splice(idx, 1);
        }
    }

    private triggerLocalAddonEvent(eventName: string, payload: any) {
        for (const [addonName, addonEvents] of this.addonListeners) {
            const callbacks = addonEvents.get(eventName);
            if (callbacks) {
                for (const cb of callbacks) {
                    try { cb(payload); } catch (e) { console.error(`Error in local addon listener for ${addonName}:${eventName}`, e); }
                }
            }
        }
    }
    private static showInitFailureOverlay(target: HTMLElement, message: string) {
        const overlay = document.createElement("div");
        overlay.setAttribute("data-molsysviewer-error", "webgl");
        Object.assign(overlay.style, {
            position: "absolute",
            inset: "0",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            textAlign: "center",
            background: "rgba(10, 10, 10, 0.78)",
            color: "#f2f2f2",
            fontFamily: "\"IBM Plex Sans\", system-ui, sans-serif",
            fontSize: "14px",
            lineHeight: "1.4",
            zIndex: "10",
            pointerEvents: "none",
        });
        overlay.textContent = message;
        target.appendChild(overlay);
    }

    static async create(target: HTMLElement, notify?: (msg: any) => void, existingCanvas?: HTMLCanvasElement, options?: { panelModeStyle?: string, model?: any, onPanelPopClick?: () => void, isPanelOnly?: boolean }): Promise<MolSysViewerController> {
        // Wrap the Mol* canvas in a host div so panels can shift it without
        // resizing the outer target element.  No CSS transition here — inset
        // animation is driven frame-by-frame via rAF so Mol*'s ResizeObserver
        // fires on every frame and keeps the molecule in sync with the panel.
        const canvasHost = document.createElement("div");
        Object.assign(canvasHost.style, {
            position: "absolute",
            top: "0",
            left: "0",
            right: "0",
            bottom: "0",
        });
        target.appendChild(canvasHost);

        const canvas = existingCanvas ?? document.createElement("canvas");
        if (!existingCanvas) {
            canvas.style.width = "100%";
            canvas.style.height = "100%";
            canvas.style.display = "block";
            canvasHost.appendChild(canvas);
        } else if (existingCanvas.parentElement !== canvasHost) {
            canvasHost.appendChild(existingCanvas);
        }

        const plugin = new PluginContext(createMolSysViewerPluginSpec());
        await plugin.init();

        // Register custom colour themes after plugin init.
        plugin.representation.structure.themes.colorThemeRegistry.add(MsvPerAtomColorThemeProvider);

        const init = (plugin as any).initViewerAsync ?? (plugin as any).initViewer;
        let ok = false;
        if (typeof init === "function") {
            const result = init.call(plugin, canvas, canvasHost);
            ok = typeof result?.then === "function" ? await result : !!result;
        } else {
            console.error("[MolSysViewer] Plugin init function not found (initViewer/initViewerAsync missing)");
        }
        if (!ok) {
            const message = "WebGL unavailable / GPU driver mismatch. Mol* viewer failed to initialize.";
            console.error("[MolSysViewer] Failed to init Mol* viewer");
            MolSysViewerController.showInitFailureOverlay(target, message);
            notify?.({ event: "viewer_init_failed", reason: "webgl", message });
        }

        return new MolSysViewerController(plugin, target, notify, canvasHost, options);
    }

    public readonly loader: LoaderHandlers;
    public readonly annotations: AnnotationHandlers;
    public readonly measurements: MeasurementHandlers;
    public readonly shapes: ShapeHandlers;
    public readonly scene: SceneHandlers;
    public readonly state: StateHandlers;
    public readonly trajectory: TrajectoryHandlers;
    public readonly movie: MovieHandlers;

    private currentStructure?: StateObjectRef; // Ref to structure root
    private loadedStructure?: LoadedStructure; // Loaded structure bundle
    private currentActiveSelection: ActiveSelectionPayload | null = null;
    private lastMeasurementSummary: LastMeasurementSummary | null = null;
    private measurementTagCounter = 0;
    private welcomeCard: HTMLDivElement | null = null;
    private readonly model?: any;

    private localViewerMode = "classic";
    private localControlsMode = "classic";
    private localPanelModeStyle = "drawer";

    getViewerMode(): string {
        return this.model ? (this.model.get("viewer_mode") || "classic") : this.localViewerMode;
    }
    getControlsMode(): string {
        return this.model ? (this.model.get("controls_mode") || "classic") : this.localControlsMode;
    }
    getPanelModeStyle(): string {
        return this.model ? (this.model.get("panel_mode_style") || "drawer") : this.localPanelModeStyle;
    }

    getActivePanel(): "navigate" | "workbench" | null {
        if (this.groupPanel.isExpanded()) return "navigate";
        if (this.workbenchPanel.isExpanded()) return "workbench";
        return null;
    }

    private savedHostPanelState: any = null;

    public saveHostPanelState(): void {
        if (this.sharedShell) {
            this.savedHostPanelState = {
                isSplit: this.sharedShell.isSplit,
                isAmbient: this.sharedShell.isAmbient,
                minimized: this.sharedShell.minimized,
                expanded: this.groupPanel.isExpanded() || this.workbenchPanel.isExpanded(),
                activePanel: this.getActivePanel(),
            };
        }
    }

    public restoreHostPanelState(): void {
        if (this.sharedShell && this.savedHostPanelState) {
            this.sharedShell.setSplit(this.savedHostPanelState.isSplit);
            this.sharedShell.setAmbient(this.savedHostPanelState.isAmbient);
            this.sharedShell.setVisible(true);
            this.setPanelMode(this.savedHostPanelState.activePanel, this.savedHostPanelState.expanded);
        } else if (this.sharedShell) {
            this.sharedShell.setVisible(true);
        }
    }

    setViewerMode(mode: string) {
        if (this.model) {
            this.model.set("viewer_mode", mode);
            this.model.save_changes();
        } else {
            this.localViewerMode = mode;
        }
    }
    setControlsMode(mode: string) {
        if (this.model) {
            this.model.set("controls_mode", mode);
            this.model.save_changes();
        } else {
            this.localControlsMode = mode;
        }
    }
    setPanelModeStyle(style: string) {
        if (this.model) {
            this.model.set("panel_mode_style", style);
            this.model.save_changes();
        } else {
            this.localPanelModeStyle = style;
        }
    }

    setCanvasVisibility(visible: boolean) {
        if (this.canvasHost) {
            this.canvasHost.style.display = visible ? "block" : "none";
            this.sharedShell?.setCanvasHidden(!visible);
            this.updateCanvasInsets();
        }
    }

    // Getters for scene state delegated to scene handler
    get isSpinActive() { return this.scene.isSpinActive; }
    get isSwingActive() { return this.scene.isSwingActive; }
    get isDarkMode() { return this.scene.isDarkMode; }

    private nextMeasurementTag(): string {
        this.measurementTagCounter += 1;
        return `measurement_${this.measurementTagCounter}`;
    }

    private constructor(public readonly plugin: PluginContext, private readonly host: HTMLElement, private readonly notify?: (msg: any) => void, canvasHost?: HTMLDivElement, initOptions?: { panelModeStyle?: string, viewerMode?: string, controlsMode?: string, isAmbient?: boolean, isSplit?: boolean, model?: any, isPanelOnly?: boolean }) {
        this.model = initOptions?.model;
        this.isPanelOnly = !!initOptions?.isPanelOnly;
        if (initOptions?.viewerMode) {
            this.localViewerMode = initOptions.viewerMode;
        }
        if (initOptions?.controlsMode) {
            this.localControlsMode = initOptions.controlsMode;
        }
        if (initOptions?.panelModeStyle) {
            this.localPanelModeStyle = initOptions.panelModeStyle;
        }
        this.canvasHost = canvasHost ?? (() => { const d = document.createElement("div"); host.appendChild(d); return d; })();
        if (this.isPanelOnly) {
            this.canvasHost.style.display = "none";
        }
        this.injectGlobalStyles();
        const emitInteractionEvent = (msg: any) => {
            if (msg?.event === "interaction_tool_state") {
                if (msg?.status === "started" || msg?.status === "progress") {
                    this.toolStatusOverlay.update({
                        action: msg.action,
                        pickedCount: msg.picked_count,
                        requiredPicks: msg.required_picks,
                        remainingPicks: msg.remaining_picks,
                    });
                } else {
                    this.toolStatusOverlay.update({ action: null });
                }
            } else if (msg?.event === "interaction_active_selection_changed") {
                this.currentActiveSelection = msg;
                this.groupPanel.updateSelection(msg);
                this.syncVisualSelection(msg);
                this.triggerLocalAddonEvent("selection-changed", msg);
            } else if (msg?.event === "interaction_measurement_created") {
                this.lastMeasurementSummary = {
                    action: msg.action,
                    picked_count: msg.picked_count,
                };
            }
            this.notify?.(msg);
        };

        this.toolStatusOverlay = new ToolStatusOverlay(host);
        this.legendOverlay = new LegendOverlay(host);
        new HoverTooltip(host, plugin);
        this.measurementTools = new MeasurementToolController(plugin, emitInteractionEvent, async ({ action, picks_atom_indices, endpoint_policy }) => {
            const tag = this.nextMeasurementTag();
            const structure = this.getStructureData();
            const measurementOptions = this.measurements.buildMeasurementOptions(
                picks_atom_indices,
                endpoint_policy,
                structure,
            );
            const value = this.measurements.computeMeasurementValue(picks_atom_indices, measurementOptions, structure);
            const msg = {
                op: action === "distance"
                    ? "add_distance_measurement"
                    : action === "angle"
                        ? "add_angle_measurement"
                        : "add_dihedral_measurement",
                tag,
                options: {
                    tag,
                    picks_atom_indices,
                    endpoint_policy: measurementOptions.endpoint_policy,
                    endpoint_kinds: measurementOptions.endpoint_kinds,
                    endpoint_labels: measurementOptions.endpoint_labels,
                    endpoint_atom_indices: measurementOptions.endpoint_atom_indices,
                },
            } as const;
            if (action === "distance") {
                await this.measurements.addDistance(msg);
            } else if (action === "angle") {
                await this.measurements.addAngle(msg);
            } else {
                await this.measurements.addDihedral(msg);
            }
            return {
                tag,
                endpoint_policy: measurementOptions.endpoint_policy,
                endpoint_kinds: measurementOptions.endpoint_kinds,
                endpoint_labels: measurementOptions.endpoint_labels,
                endpoint_atom_indices: measurementOptions.endpoint_atom_indices,
                value,
            };
        });
        const floatingPanels = initOptions?.panelModeStyle === "floating" || 
                               initOptions?.panelModeStyle === "floating-unified" || 
                               initOptions?.panelModeStyle === "integrated" ||
                               initOptions?.panelModeStyle === "ambient" ||
                               initOptions?.panelModeStyle === "split";
        const floatingUnified = initOptions?.panelModeStyle === "floating-unified" || 
                                initOptions?.panelModeStyle === "integrated" ||
                                initOptions?.panelModeStyle === "ambient" ||
                                initOptions?.panelModeStyle === "split";

        let sharedShell: FloatingPanelShell | undefined = undefined;
        if (floatingUnified) {
            sharedShell = new FloatingPanelShell(host, { 
                title: "Navigate", 
                panelModeStyle: initOptions?.panelModeStyle,
                onPanelPopClick: initOptions?.onPanelPopClick,
                isPanelOnly: this.isPanelOnly,
            });
            if (this.isPanelOnly) {
                sharedShell.setSplit(true);
                sharedShell.setVisible(true);
                sharedShell.setExpanded(true);
            } else {
                if (initOptions?.isAmbient !== undefined) {
                    sharedShell.setAmbient(initOptions.isAmbient);
                }
                if (initOptions?.isSplit !== undefined) {
                    sharedShell.setSplit(initOptions.isSplit);
                }
            }
            // Close button of the shared shell collapses both panels (or closes the window in isPanelOnly)
            sharedShell.toggleButton.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                if (this.isPanelOnly) {
                    try { window.close(); } catch (e) {}
                } else {
                    this.collapsePanels();
                }
            });
            sharedShell.setVisible(true);
            this.sharedShell = sharedShell;

            if (floatingUnified && !this.isPanelOnly) {
                sharedShell.onResize = () => {
                    this.updateCanvasInsets();
                };

                const ro = new ResizeObserver(() => {
                    this.updateCanvasInsets();
                    sharedShell?.clampPosition();
                });
                ro.observe(host);
                this.splitResizeObserver = ro;
            }
        }

        this.activeSelection = new ActiveSelectionController(emitInteractionEvent);
        this.groupPanel = new GroupPanel(host, (items, additive) => {
            this.activeSelection.setItems(items, additive);
        }, (item, modifiers) => {
            this.activeSelection.handleItemClick(item, modifiers);
        }, (item) => {
            const loci = this.groupPanel.focusItem(item);
            if (loci) this.plugin.managers.camera.focusLoci(loci);
        }, (item) => {
            if (!item) {
                this.plugin.managers.interactivity.lociHighlights.clearHighlights();
                emitInteractionEvent({ event: "interaction_hover", kind: "empty" });
                return;
            }
            const loci = this.groupPanel.focusItem(item);
            if (!loci) return;
            this.plugin.managers.interactivity.lociHighlights.highlightOnly({ loci }, false);
            emitInteractionEvent({
                event: "interaction_hover",
                kind: "structure",
                atom_indices: item.atom_indices,
            });
        }, (item, pageX, pageY) => {
            this.openContextMenuForItem(item, pageX, pageY, emitInteractionEvent);
        }, (target, pageX, pageY) => {
            this.openContextMenuForAnnotation(target, pageX, pageY, emitInteractionEvent);
        }, (tag) => {
            const saved = this.savedSelections.find((item) => item.tag === tag);
            if (!saved) return;
            this.activeSelection.setFromAtomIndices(saved.atom_indices, this.getStructureData());
        }, (tag) => {
            const region = this.state.getRegionSummaries().find((item) => item.tag === tag);
            if (!region) return;
            this.focusTarget({ atom_indices: region.atom_indices });
        }, sharedShell ? { sharedShell } : (floatingPanels ? { floating: true } : undefined));
        this.workbenchPanel = new WorkbenchPanel(host, sharedShell ? { sharedShell } : (floatingPanels ? { floating: true } : undefined));
        if (this.isPanelOnly) {
            this.groupPanel.setExpanded(true);
        }
        this.refreshPanelWorkspaceChrome();
        this.groupPanel.setOnExpandedChange((expanded) => {
            this.handlePanelExpansionChanged("navigate", expanded);
        });
        this.workbenchPanel.setOnExpandedChange((expanded) => {
            this.handlePanelExpansionChanged("workbench", expanded);
        });
        const getCameraDirection = (): [number, number, number] => {
            const snap = this.plugin.canvas3d?.camera.getSnapshot?.();
            if (!snap) return [0, 0, -1];
            const dx = snap.target[0] - snap.position[0];
            const dy = snap.target[1] - snap.position[1];
            const dz = snap.target[2] - snap.position[2];
            const len = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
            return [dx / len, dy / len, dz / len];
        };
        this.contextMenu = new ViewerContextMenu(host, emitInteractionEvent, (action, target, details) => {
            if (action === "focus_target") {
                this.focusTarget(target);
                return;
            }
            if (action === "focus_region") {
                const tag = typeof details?.tag === "string" ? details.tag : null;
                if (!tag) return;
                const region = this.state.getRegionSummaries().find((item) => item.tag === tag);
                if (!region) return;
                this.focusTarget({ atom_indices: region.atom_indices });
                return;
            }
            if (action === "focus_selection") {
                this.focusCurrentSelection();
                return;
            }
            if (action === "hide_measurement") {
                const tag = typeof details?.tag === "string" ? details.tag : null;
                if (!tag) return;
                void this.handleMessage({ op: "hide_layer", tag });
                return;
            }
            if (action === "delete_measurement") {
                const tag = typeof details?.tag === "string" ? details.tag : null;
                if (!tag) return;
                void this.handleMessage({ op: "clear_layer", tag });
                return;
            }
            if (action === "activate_selection") {
                return;
            }
            if (action === "clear_selection") {
                this.activeSelection.clear();
                return;
            }
            if (action === "toggle_canvas_visibility") {
                const isHidden = this.canvasHost.style.display === "none";
                this.setCanvasVisibility(isHidden);
                return;
            }
            if (action === "reset_view") {
                void this.resetView();
                return;
            }
            if (action === "toggle_background") {
                void this.toggleBackground();
                return;
            }
            if (action === "toggle_spin") {
                void this.toggleSpin();
                return;
            }
            if (action === "toggle_swing") {
                void this.toggleSwing();
                return;
            }
            if (action === "open_navigate") {
                this.setPanelMode("navigate", true);
                return;
            }
            if (action === "open_workbench") {
                this.setPanelMode("workbench", true);
                return;
            }
            if (action === "set_viewer_mode") {
                const mode = details?.text;
                if (mode && this.model) {
                    this.model.set("viewer_mode", mode);
                    this.model.save_changes();
                }
                return;
            }
            if (action === "toggle_region_visibility") {
                const tag = typeof details?.tag === "string" ? details.tag : null;
                if (!tag) return;
                this.notify?.({ event: "interaction_context_action", action, tag });
                return;
            }
            if (action === "delete_region") {
                const tag = typeof details?.tag === "string" ? details.tag : null;
                if (!tag) return;
                this.notify?.({ event: "interaction_context_action", action, tag });
                return;
            }
            if (action === "rename_region") {
                const tag = typeof details?.tag === "string" ? details.tag : null;
                const new_tag = typeof details?.new_tag === "string" ? details.new_tag : null;
                if (!tag || !new_tag) return;
                this.notify?.({ event: "interaction_context_action", action, tag, new_tag });
                return;
            }
            if (
                action === "delete_annotation"
                || action === "delete_shape"
                || action === "save_selection"
                || action === "remove_selection"
                || action === "create_region_from_selection"
                || action === "create_section_from_selection"
                || action === "add_label_from_selection"
            ) {
                return;
            }
            this.startMeasurementTool(action, details?.endpoint_policy);
        }, () => {
            this.workbenchContext = null;
            this.refreshWorkbenchPanel();
        }, getCameraDirection);
        const canvas = this.plugin.canvas3d?.props?.canvas ?? this.plugin.canvas3d?.getCanvas?.();
        if (canvas) {
            this.releaseContextMenuSuppression = suppressCanvasContextMenu(host, canvas as HTMLElement);
        }
        this.releaseGlobalEscapeHandler = this.installGlobalEscapeHandler();
        registerInteractionObservers(plugin, emitInteractionEvent, undefined, (ev) => {
            if (!this.measurementTools.isActive()) {
                this.activeSelection.handlePrimaryClick(ev);
                this.handlePotentialDoubleClickFocus(ev);
            }
            this.measurementTools.handlePrimaryClick(ev?.current?.loci);
        }, (ev) => {
            this.lastContextLoci = ev?.current?.loci ?? null;
            const page = ev?.page;
            // ev.page contains canvas-relative coordinates (clientX - canvasEl.rect.left).
            // identify() expects canvas-relative; contextMenu.open expects viewport-relative.
            const canvas_x = typeof page?.[0] === "number" ? page[0] : undefined;
            const canvas_y = typeof page?.[1] === "number" ? page[1] : undefined;
            const canvasOffset = this.canvasHost.getBoundingClientRect();
            const page_x = canvas_x !== undefined ? canvas_x + canvasOffset.left : undefined;
            const page_y = canvas_y !== undefined ? canvas_y + canvasOffset.top : undefined;
            // Detect annotation/measurement context: repr embeds its tag in props.tooltip
            const tooltipTag = (ev?.current?.repr as any)?.props?.tooltip?.trim();
            if (tooltipTag && this.annotations.hasTag(tooltipTag)) {
                const spec = this.annotations.getSpec(tooltipTag);
                const annPayload: ContextInteractionPayload = {
                    event: "interaction_context_menu",
                    kind: "annotation",
                    atom_indices: spec?.atom_indices ?? [],
                    tag: tooltipTag,
                    text: spec?.text,
                    page_x,
                    page_y,
                };
                this.lastContextPayload = annPayload;
                this.groupPanel.updateContextTarget(annPayload);
                this.syncWorkbenchContextFromPayload(annPayload);
                emitInteractionEvent(annPayload);
                this.contextMenu.open(
                    annPayload,
                    page_x ?? 0,
                    page_y ?? 0,
                    this.currentActiveSelection,
                    this.lastMeasurementSummary,
                    this.savedSelections.map(({ tag, atom_count }) => ({ tag, atom_count })),
                    this.getRelevantRegionSummaries(annPayload),
                    this.addonContextActions,
                    this.addonContextItems,
                    {
                        isSpinActive: this.scene.isSpinActive,
                        isSwingActive: this.scene.isSwingActive,
                        isDarkMode: this.scene.isDarkMode,
                        isNavigateExpanded: this.groupPanel.isExpanded(),
                        isWorkbenchExpanded: this.workbenchPanel.isExpanded(),
                        currentViewerMode: this.model?.get("viewer_mode") || "classic",
                    }
                );
                return;
            }
            if (tooltipTag && this.measurements.hasTag(tooltipTag)) {
                const spec = this.measurements.getSpec(tooltipTag);
                const measPayload: ContextInteractionPayload = {
                    event: "interaction_context_menu",
                    kind: "measurement",
                    atom_indices: spec?.atom_indices ?? [],
                    tag: tooltipTag,
                    measurement_name: spec?.kind,
                    page_x,
                    page_y,
                };
                this.lastContextPayload = measPayload;
                this.groupPanel.updateContextTarget(measPayload);
                this.syncWorkbenchContextFromPayload(measPayload);
                emitInteractionEvent(measPayload);
                this.contextMenu.open(
                    measPayload,
                    page_x ?? 0,
                    page_y ?? 0,
                    this.currentActiveSelection,
                    this.lastMeasurementSummary,
                    this.savedSelections.map(({ tag, atom_count }) => ({ tag, atom_count })),
                    this.getRelevantRegionSummaries(measPayload),
                    this.addonContextActions,
                    this.addonContextItems,
                    {
                        isSpinActive: this.scene.isSpinActive,
                        isSwingActive: this.scene.isSwingActive,
                        isDarkMode: this.scene.isDarkMode,
                        isNavigateExpanded: this.groupPanel.isExpanded(),
                        isWorkbenchExpanded: this.workbenchPanel.isExpanded(),
                        currentViewerMode: this.model?.get("viewer_mode") || "classic",
                    }
                );
                return;
            }
            let payload = normalizeContextInteractionEvent(ev, this.lastHoverLoci);
            payload = this.normalizeManagedContextPayload(payload);
            if (canvas_x !== undefined && canvas_y !== undefined) {
                const pickData = this.plugin.canvas3d?.identify?.([canvas_x, canvas_y] as any);
                const pickedLoci = pickData ? this.plugin.canvas3d?.getLoci?.(pickData.id)?.loci : null;
                if (pickedLoci) {
                    payload = normalizeContextPayloadFromLoci(pickedLoci, page_x, page_y);
                    payload = this.normalizeManagedContextPayload(payload);
                }
            }
            if (payload.kind === "empty" && this.lastHoverPayload && this.lastHoverPayload.kind !== "empty") {
                if (this.lastHoverPayload.kind === "structure") {
                    payload = {
                        event: "interaction_context_menu",
                        kind: "structure",
                        atom_indices: this.lastHoverPayload.atom_indices,
                        group_indices: this.lastHoverPayload.group_indices,
                        chain_indices: this.lastHoverPayload.chain_indices,
                        entity_indices: this.lastHoverPayload.entity_indices,
                        group_name: this.lastHoverPayload.group_name,
                        chain_name: this.lastHoverPayload.chain_name,
                        entity_name: this.lastHoverPayload.entity_name,
                        page_x: payload.page_x,
                        page_y: payload.page_y,
                    };
                } else if (this.lastHoverPayload.kind === "shape") {
                    payload = {
                        event: "interaction_context_menu",
                        kind: "shape",
                        atom_indices: this.lastHoverPayload.atom_indices,
                        tag: this.lastHoverPayload.tag,
                        shape_name: this.lastHoverPayload.shape_name,
                        page_x: payload.page_x,
                        page_y: payload.page_y,
                    };
                } else if (this.lastHoverPayload.kind === "measurement") {
                    payload = {
                        event: "interaction_context_menu",
                        kind: "measurement",
                        atom_indices: this.lastHoverPayload.atom_indices,
                        tag: this.lastHoverPayload.tag,
                        measurement_name: this.lastHoverPayload.measurement_name,
                        page_x: payload.page_x,
                        page_y: payload.page_y,
                    };
                } else if (this.lastHoverPayload.kind === "annotation") {
                    payload = {
                        event: "interaction_context_menu",
                        kind: "annotation",
                        atom_indices: this.lastHoverPayload.atom_indices,
                        tag: this.lastHoverPayload.tag,
                        text: this.lastHoverPayload.text,
                        page_x: payload.page_x,
                        page_y: payload.page_y,
                    };
                }
            }
            const pageX = page_x ?? payload.page_x ?? 0;
            const pageY = page_y ?? payload.page_y ?? 0;
            this.lastContextPayload = payload;
            this.groupPanel.updateContextTarget(payload);
            this.syncWorkbenchContextFromPayload(payload);
            emitInteractionEvent(payload);
            this.contextMenu.open(
                payload,
                pageX,
                pageY,
                this.currentActiveSelection,
                this.lastMeasurementSummary,
                this.savedSelections.map(({ tag, atom_count }) => ({ tag, atom_count })),
                this.getRelevantRegionSummaries(payload),
                this.addonContextActions,
                this.addonContextItems,
                {
                    isSpinActive: this.scene.isSpinActive,
                    isSwingActive: this.scene.isSwingActive,
                    isDarkMode: this.scene.isDarkMode,
                    isNavigateExpanded: this.groupPanel.isExpanded(),
                    isWorkbenchExpanded: this.workbenchPanel.isExpanded(),
                    currentViewerMode: this.model?.get("viewer_mode") || "classic",
                    isCanvasVisible: this.canvasHost.style.display !== "none",
                }
            );
        }, (ev) => {
            this.lastHoverLoci = ev?.current?.loci ?? null;
            const tooltipTag = (ev?.current?.repr as any)?.props?.tooltip?.trim();
            if (tooltipTag && this.annotations.hasTag(tooltipTag)) {
                const spec = this.annotations.getSpec(tooltipTag);
                this.lastHoverPayload = {
                    event: "interaction_hover",
                    kind: "annotation",
                    atom_indices: spec?.atom_indices ?? [],
                    tag: tooltipTag,
                    text: spec?.text,
                };
            } else if (tooltipTag && this.measurements.hasTag(tooltipTag)) {
                const spec = this.measurements.getSpec(tooltipTag);
                this.lastHoverPayload = {
                    event: "interaction_hover",
                    kind: "measurement",
                    atom_indices: spec?.atom_indices ?? [],
                    tag: tooltipTag,
                    measurement_name: spec?.kind,
                };
            } else {
                this.lastHoverPayload = this.normalizeManagedInteractionPayload(normalizeInteractionEvent("hover", ev));
            }
        }, (ev) => {
            const resolved = resolveTooltipPayload("hover", ev, this.annotations, this.measurements);
            if (resolved) {
                emitInteractionEvent(resolved);
            } else {
                emitInteractionEvent(this.normalizeManagedInteractionPayload(normalizeInteractionEvent("hover", ev)));
            }
        }, (ev) => {
            const resolved = resolveTooltipPayload("click", ev, this.annotations, this.measurements);
            if (resolved) {
                emitInteractionEvent(resolved);
            } else {
                emitInteractionEvent(this.normalizeManagedInteractionPayload(normalizeInteractionEvent("click", ev)));
            }
        });

        // Initialize handlers with necessary context callbacks
        
        this.state = new StateHandlers(plugin, {
            getStructure: () => this.getStructureData(),
            getLoadedStructure: () => this.loadedStructure,
            getCurrentStructureRef: () => this.currentStructure,
            getComponents: () => this.getComponents(),
            notify: (msg) => this.notify?.(msg),
            setManagedLayerVisibility: async (tag, kind, visible) => {
                if (kind === "annotation") {
                    await this.annotations.setVisibility(tag, visible);
                    return true;
                }
                if (kind === "measurement") {
                    await this.measurements.setVisibility(tag, visible);
                    return true;
                }
                return false;
            }
        });

        this.shapes = new ShapeHandlers(
            plugin,
            (ref, tag) => this.state.registerShapeRef(ref, tag),
            {
                clearByTag: (tag) => this.state.clearShapesByTag(tag),
                subscribeToTrajectoryState: (cb) =>
                    this.trajectory.onTrajectoryState(
                        (state) => cb(state.currentFrame),
                        { immediate: false },
                    ),
            },
        );
        this.annotations = new AnnotationHandlers(plugin, {
            getStructure: () => this.getStructureData(),
            registerRef: (ref, tag) => this.state.registerTaggedRef(ref, tag, "annotation"),
            addLabelOverlay: (msg) => this.groupPanel.addLabelOverlay(msg),
        });
        this.measurements = new MeasurementHandlers(plugin, {
            getStructure: () => this.getStructureData(),
            registerRef: (ref, tag) => this.state.registerTaggedRef(ref, tag, "measurement"),
        });

        this.scene = new SceneHandlers(plugin, host, {
            clearShapes: () => this.state.clearShapesByTag(), // clear all shapes
            clearLabels: async () => {
                await this.annotations.clearLabels();
                this.groupPanel.clearAnnotationOverlays();
            },
            getComponents: () => this.getComponents(),
            clearShapesByTag: (tag) => {
                this.state.clearShapesByTag(tag);
                this.groupPanel.clearAnnotationOverlaysByTag(tag);
                this.annotations.clearLabelByTag(tag);
            },
            registerShapeRef: (ref, tag) => this.state.registerShapeRef(ref, tag),
            removeLoadedStructure: () => this.removeLoadedStructure(),
            notify: (msg) => this.notify?.(msg)
        });

        this.loader = new LoaderHandlers(plugin, {
            clearGlobalRepresentations: async () => { /* handled by state via events usually, but direct call needed? state handles globals */ },
            captureCurrentStructure: () => this.captureCurrentStructure(),
            setLoadedStructure: (ls) => { this.loadedStructure = ls; },
            getLoadedStructure: () => this.loadedStructure,
            setExpectedFrameCount: (n) => this.trajectory.setExpectedFrameCount(n),
        });

        this.trajectory = new TrajectoryHandlers(plugin, {
            getLoadedStructure: () => this.loadedStructure,
            notifyTrajectoryState: () => this.notifyTrajectoryState(),
            onPlaybackStopped: (frame) => this.notify?.({ event: "trajectory_frame_changed", frame }),
            notify: (msg) => this.notify?.(msg),
        });
        this.movie = new MovieHandlers({
            setTrajectoryFrame: (index) => this.trajectory.setTrajectoryFrame(index),
            setCameraSnapshot: (snap, durationMs) => this.setCameraSnapshot(snap, durationMs),
            getCameraSnapshot: () => this.getCameraSnapshot(),
            getImageDataUri: (options) => this.getImageDataUri(options),
            showLayer: (tag) => this.state.showLayer({ op: "show_layer", tag }),
            hideLayer: (tag) => this.state.hideLayer({ op: "hide_layer", tag }),
            notify: (msg) => this.notify?.(msg),
        });
        // Subscriptions to local event bus
        this.trajectory.onTrajectoryState(
            (state) => {
                this.triggerLocalAddonEvent("frame-changed", state.currentFrame);
            },
            { immediate: false },
        );

        if (plugin.canvas3d?.didDraw) {
            plugin.canvas3d.didDraw.subscribe(() => {
                const cameraState = plugin.canvas3d!.camera.getSnapshot();
                this.triggerLocalAddonEvent("camera-moved", cameraState);
            });
        }

        this.refreshNavigatePanel();
        this.refreshWorkbenchPanel();
        this.updateWelcomeState();
    }

    dispose(): void {
        this.measurementTools.dispose();
        this.toolStatusOverlay.dispose();
        this.legendOverlay.dispose();
        this.groupPanel.dispose();
        this.workbenchPanel.dispose();
        this.sharedShell?.dispose();
        this.splitResizeObserver?.disconnect();
        this.contextMenu.dispose();
        this.releaseContextMenuSuppression?.();
        this.releaseGlobalEscapeHandler?.();
        this.plugin.dispose();
    }

    private startMeasurementTool(action: MeasurementToolAction, endpointPolicy?: MeasurementEndpointPolicy): void {
        if (!this.lastContextLoci) return;
        this.measurementTools.start(action, this.lastContextLoci, endpointPolicy);
    }

    private installGlobalEscapeHandler(): () => void {
        const onKeyDown = (event: KeyboardEvent) => {
            if ((event.target as HTMLElement)?.closest?.("input, textarea, [contenteditable]")) return;
            if (!this.host.contains(event.target as Node)) return;

            if (event.key === "Escape") {
                if (this.measurementTools.isActive()) return;
                if (this.groupPanel.isExpanded() || this.workbenchPanel.isExpanded()) {
                    event.preventDefault();
                    event.stopPropagation();
                    this.collapsePanels();
                    this.contextMenu.close();
                    return;
                }
                if (this.currentActiveSelection?.source_kind !== "empty") {
                    event.preventDefault();
                    event.stopPropagation();
                    this.activeSelection.clear();
                    this.contextMenu.close();
                }
                return;
            }

            if (event.key === "n" || event.key === "N") {
                event.preventDefault();
                event.stopPropagation();
                if (this.groupPanel.isVisible()) {
                    const open = this.groupPanel.isExpanded();
                    this.collapsePanels();
                    if (!open) this.setPanelMode("navigate", true);
                }
                return;
            }

            if (event.key === "w" || event.key === "W") {
                event.preventDefault();
                event.stopPropagation();
                if (this.workbenchPanel.isVisible()) {
                    const open = this.workbenchPanel.isExpanded();
                    this.collapsePanels();
                    if (!open) this.setPanelMode("workbench", true);
                }
                return;
            }
        };
        window.addEventListener("keydown", onKeyDown, true);
        return () => window.removeEventListener("keydown", onKeyDown, true);
    }

    private panelOpenState = false;

    public onTogglePanelModeOverride?: () => boolean;

    public togglePanelMode(): void {
        if (this.onTogglePanelModeOverride && this.onTogglePanelModeOverride()) {
            return;
        }
        const isOpened = this.panelOpenState || 
                         (this.sharedShell && this.sharedShell.isVisible() && this.sharedShell.isExpanded());
        if (isOpened) {
            this.collapsePanels();
        } else {
            if (this.sharedShell) {
                this.sharedShell.setVisible(true);
            }
            this.setPanelMode(undefined, true);
        }
    }

    private collapsePanels(): void {
        this.panelOpenState = false;
        this.syncingPanelExpansion = true;
        try {
            this.groupPanel.setExpanded(false);
            this.workbenchPanel.setExpanded(false);
            this.sharedShell?.setExpanded(false);
        } finally {
            this.syncingPanelExpansion = false;
        }
        this.updateCanvasInsets();
        this.emitPanelModeState();
    }

    private updateCanvasInsets(): void {
        const leftOpen = this.groupPanel.isVisible() && this.groupPanel.isExpanded();
        const rightOpen = this.workbenchPanel.isVisible() && this.workbenchPanel.isExpanded();
        const toLeft = leftOpen ? this.groupPanel.panelContentWidth : 0;
        const toRight = rightOpen ? this.workbenchPanel.panelContentWidth : 0;

        // Cancel any running animation and read current *animated* position as start.
        if (this.canvasInsetAnimFrame !== null) {
            cancelAnimationFrame(this.canvasInsetAnimFrame);
            this.canvasInsetAnimFrame = null;
        }
        const fromLeft = parseFloat(this.canvasHost.style.left) || 0;
        const fromRight = parseFloat(this.canvasHost.style.right) || 0;
        if (fromLeft === toLeft && fromRight === toRight) return;

        this.canvasInsetFrom = { left: fromLeft, right: fromRight };
        this.canvasInsetTo = { left: toLeft, right: toRight };
        this.canvasInsetStart = performance.now();

        // CSS `ease` ≈ easeOutQuad: starts fast, decelerates — matches the
        // panel's `transition: transform 160ms ease`.
        const ease = (t: number) => t * (2 - t);

        const tick = (now: number) => {
            const t = Math.min((now - this.canvasInsetStart) / this.canvasInsetDuration, 1);
            const e = ease(t);
            const l = this.canvasInsetFrom.left + (this.canvasInsetTo.left - this.canvasInsetFrom.left) * e;
            const r = this.canvasInsetFrom.right + (this.canvasInsetTo.right - this.canvasInsetFrom.right) * e;
            this.canvasHost.style.left = `${l}px`;
            this.canvasHost.style.right = `${r}px`;
            // Force a synchronous layout flush so that plugin.handleResize()
            // reads the *new* offsetWidth in this same rAF tick and not the
            // stale value from the previous frame.
            // eslint-disable-next-line @typescript-eslint/no-unused-expressions
            void this.canvasHost.offsetWidth;
            // Tell Mol* to resize now: resizeCanvas() reads the new offsetWidth,
            // sets canvas.width, and schedules a viewport update for the next
            // _animate tick — keeps the molecule one frame behind at most.
            this.plugin.handleResize();
            if (t < 1) {
                this.canvasInsetAnimFrame = requestAnimationFrame(tick);
            } else {
                this.canvasInsetAnimFrame = null;
            }
        };

        this.canvasInsetAnimFrame = requestAnimationFrame(tick);
    }

    private handlePanelExpansionChanged(source: "navigate" | "workbench", expanded: boolean): void {
        if (this.syncingPanelExpansion) return;
        if (expanded) {
            this.lastPanelMode = source;
            if (this.currentWorkspace === "core") {
                this.lastCorePanelMode = source;
            }
        }
        if (!expanded) {
            this.updateCanvasInsets();
            return;
        }
        this.syncingPanelExpansion = true;
        try {
            if (source === "navigate") {
                this.workbenchPanel.setExpanded(false);
            } else {
                this.groupPanel.setExpanded(false);
            }
        } finally {
            this.syncingPanelExpansion = false;
        }
        this.updateCanvasInsets();
        this.emitPanelModeState();
    }

    private setPanelMode(panel?: "navigate" | "workbench" | null, expanded?: boolean): void {
        const shouldExpand = this.isPanelOnly ? true : (expanded !== false);
        if (!shouldExpand) {
            this.collapsePanels();
            return;
        }

        const requested =
            this.currentWorkspace === "core"
                ? (panel ?? this.lastCorePanelMode)
                : "workbench";
        let target: "navigate" | "workbench" | null = null;
        if (this.isPanelOnly) {
            target = requested === "workbench" ? "workbench" : "navigate";
        } else {
            if (requested === "navigate" && this.groupPanel.isVisible()) {
                target = "navigate";
            } else if (requested === "workbench" && this.workbenchPanel.isVisible()) {
                target = "workbench";
            } else if (this.groupPanel.isVisible()) {
                target = "navigate";
            } else if (this.workbenchPanel.isVisible()) {
                target = "workbench";
            }
        }
        if (!target) return;

        this.panelOpenState = true;
        this.syncingPanelExpansion = true;
        try {
            this.groupPanel.setExpanded(target === "navigate");
            this.workbenchPanel.setExpanded(target === "workbench");
            this.sharedShell?.setExpanded(true);
            this.lastPanelMode = target;
            if (this.currentWorkspace === "core") {
                this.lastCorePanelMode = target;
            }
        } finally {
            this.syncingPanelExpansion = false;
        }
        this.updateCanvasInsets();
        this.emitPanelModeState();
    }

    private refreshPanelWorkspaceChrome(): void {
        const workspaceOptions = this.getWorkspaceOptions();
        const availableWorkspaces = new Set(workspaceOptions.map((item) => item.id));
        if (!availableWorkspaces.has(this.currentWorkspace)) {
            this.currentWorkspace = "core";
        }

        if (this.currentWorkspace === "core") {
            this.groupPanel.setRuntimeVisible(null);
            this.groupPanel.setOnNavigateToWorkbench(() => {
                this.setPanelMode("workbench", true);
            }, "Workbench");
            this.workbenchPanel.setOnNavigateToNavigate(() => {
                this.setPanelMode("navigate", true);
            }, "Navigate");
        } else {
            this.groupPanel.setRuntimeVisible(false);
            this.groupPanel.setOnNavigateToWorkbench(undefined);
            this.workbenchPanel.setOnNavigateToNavigate(() => {
                this.selectWorkspace("core");
                this.setPanelMode(this.lastCorePanelMode, true);
            }, "Core");
        }

        this.groupPanel.setWorkspaces(workspaceOptions, this.currentWorkspace, (workspaceId) => {
            this.selectWorkspace(workspaceId);
        });
        this.workbenchPanel.setWorkspaces(workspaceOptions, this.currentWorkspace, (workspaceId) => {
            this.selectWorkspace(workspaceId);
        });

        if (this.currentWorkspace === "core") {
            if (this.sharedShell) {
                const activeMode = this.lastPanelMode;
                this.sharedShell.setOnSelectPanel((panelId) => {
                    if (panelId === "navigate" || panelId === "workbench") {
                        this.setPanelMode(panelId, true);
                        this.refreshPanelWorkspaceChrome();
                    }
                });
                this.sharedShell.setPanelOptions([
                    { id: "navigate", title: "Navigate", active: activeMode === "navigate" },
                    { id: "workbench", title: "Workbench", active: activeMode === "workbench" },
                ]);
            }
            this.groupPanel.setPanelStack([
                { id: "navigate", title: "Navigate", active: true },
                { id: "workbench", title: "Workbench" },
            ], (panelId) => {
                if (panelId === "workbench") this.setPanelMode("workbench", true);
            });
            this.workbenchPanel.setWorkspacePanels(
                [
                    { id: "navigate", title: "Navigate" },
                    { id: "workbench", title: "Workbench", active: true },
                ],
                (panelId) => {
                    if (panelId === "navigate") this.setPanelMode("navigate", true);
                },
            );
            return;
        }

        this.groupPanel.setPanelStack([], undefined);
        const panels = this.getWorkspacePanels(this.currentWorkspace);
        const selectedId = this.ensureWorkspacePanelSelection(this.currentWorkspace);
        if (this.sharedShell) {
            this.sharedShell.setOnSelectPanel((panelId) => {
                this.selectWorkspacePanel(this.currentWorkspace, panelId);
            });
            this.sharedShell.setPanelOptions(
                panels.map((item) => ({
                    id: item.id,
                    title: item.title,
                    active: item.id === selectedId,
                }))
            );
        }
        this.workbenchPanel.setWorkspacePanels(
            panels.map((item) => ({
                id: item.id,
                title: item.title,
                description: item.description,
                entry: item.entry,
                addon: item.addon,
                active: item.id === selectedId,
            })),
            (panelId) => {
                this.selectWorkspacePanel(this.currentWorkspace, panelId);
            },
        );
    }

    private openContextMenuForItem(
        item: ActiveSelectionItem,
        pageX: number,
        pageY: number,
        emitInteractionEvent: (msg: any) => void,
    ): void {
        const loci = this.groupPanel.focusItem(item);
        if (!loci) return;
        this.lastContextLoci = loci;
        const payload = {
            event: "interaction_context_menu" as const,
            kind: "structure" as const,
            atom_indices: item.atom_indices,
            page_x: pageX,
            page_y: pageY,
        };
        this.lastContextPayload = payload;
        this.groupPanel.updateContextTarget(payload);
        this.syncWorkbenchContextFromPayload(payload);
        emitInteractionEvent(payload);
        this.contextMenu.open(
            payload,
            pageX,
            pageY,
            this.currentActiveSelection,
            this.lastMeasurementSummary,
            this.savedSelections.map(({ tag, atom_count }) => ({ tag, atom_count })),
            this.getRelevantRegionSummaries(payload),
            this.addonContextActions,
            this.addonContextItems,
            {
                isSpinActive: this.scene.isSpinActive,
                isSwingActive: this.scene.isSwingActive,
                isDarkMode: this.scene.isDarkMode,
                isNavigateExpanded: this.groupPanel.isExpanded(),
                isWorkbenchExpanded: this.workbenchPanel.isExpanded(),
                currentViewerMode: this.model?.get("viewer_mode") || "classic",
            }
        );
    }

    private openContextMenuForAnnotation(
        target: Extract<ContextInteractionPayload, { kind: "annotation" }>,
        pageX: number,
        pageY: number,
        emitInteractionEvent: (msg: any) => void,
    ): void {
        const payload = {
            ...target,
            page_x: pageX,
            page_y: pageY,
        };
        this.lastContextPayload = payload;
        this.groupPanel.updateContextTarget(payload);
        this.syncWorkbenchContextFromPayload(payload);
        emitInteractionEvent(payload);
        this.contextMenu.open(
            payload,
            pageX,
            pageY,
            this.currentActiveSelection,
            this.lastMeasurementSummary,
            this.savedSelections.map(({ tag, atom_count }) => ({ tag, atom_count })),
            this.getRelevantRegionSummaries(payload),
            this.addonContextActions,
            this.addonContextItems,
            {
                isSpinActive: this.scene.isSpinActive,
                isSwingActive: this.scene.isSwingActive,
                isDarkMode: this.scene.isDarkMode,
                isNavigateExpanded: this.groupPanel.isExpanded(),
                isWorkbenchExpanded: this.workbenchPanel.isExpanded(),
                currentViewerMode: this.model?.get("viewer_mode") || "classic",
            }
        );
    }

    private focusCurrentSelection(): void {
        const selection = this.currentActiveSelection;
        if (!selection || selection.source_kind === "empty" || selection.atom_indices.length === 0) return;
        const loci = this.atomIndicesToLoci(selection.atom_indices);
        if (!loci) return;
        this.plugin.managers.camera.focusLoci(loci);
    }

    private focusTarget(target: { atom_indices?: number[] }): void {
        const atomIndices = Array.isArray(target.atom_indices) ? target.atom_indices : [];
        if (atomIndices.length === 0) return;
        const loci = this.atomIndicesToLoci(atomIndices);
        if (!loci) return;
        this.plugin.managers.camera.focusLoci(loci);
    }

    private syncWorkbenchContextFromPayload(payload: ContextInteractionPayload | null): void {
        if (!payload) {
            this.workbenchContext = null;
            this.refreshWorkbenchPanel();
            return;
        }
        if (payload.kind === "annotation" && typeof payload.tag === "string") {
            this.workbenchContext = { section: "annotations", tag: payload.tag };
        } else if (payload.kind === "measurement" && typeof payload.tag === "string") {
            this.workbenchContext = { section: "measurements", tag: payload.tag };
        } else if (payload.kind === "shape" && typeof payload.tag === "string") {
            this.workbenchContext = { section: "shapes", tag: payload.tag };
        } else {
            this.workbenchContext = null;
        }
        this.refreshWorkbenchPanel();
    }

    private normalizeManagedInteractionPayload(payload: InteractionPayload): InteractionPayload {
        if (payload.kind !== "shape" || typeof payload.tag !== "string") return payload;
        if (!this.measurements.hasTag(payload.tag)) return payload;
        return {
            event: payload.event,
            kind: "measurement",
            atom_indices: payload.atom_indices,
            tag: payload.tag,
            measurement_name: payload.shape_name,
        };
    }

    private normalizeManagedContextPayload(payload: ContextInteractionPayload): ContextInteractionPayload {
        if (payload.kind !== "shape" || typeof payload.tag !== "string") return payload;
        if (!this.measurements.hasTag(payload.tag)) return payload;
        return {
            event: payload.event,
            kind: "measurement",
            atom_indices: payload.atom_indices,
            tag: payload.tag,
            measurement_name: payload.shape_name,
            page_x: payload.page_x,
            page_y: payload.page_y,
        };
    }

    private getRelevantRegionSummaries(target: { atom_indices?: number[] }): RegionSummary[] {
        const atomIndices = Array.isArray(target.atom_indices) ? target.atom_indices : [];
        if (atomIndices.length === 0) return [];
        const targetSet = new Set(atomIndices);
        return this.state
            .getRegionSummaries()
            .filter((region) => region.atom_indices.some((idx) => targetSet.has(idx)));
    }

    private upsertSavedSelection(msg: any): void {
        const tag = typeof msg?.tag === "string" ? msg.tag : null;
        if (!tag) return;
        const atomIndices = Array.isArray(msg?.atom_indices)
            ? msg.atom_indices.filter((value: unknown) => typeof value === "number")
            : [];
        const atomCount = atomIndices.length;
        const next = this.savedSelections.filter((item) => item.tag !== tag);
        next.push({ tag, atom_count: atomCount, atom_indices: atomIndices });
        this.savedSelections = next.sort((a, b) => a.tag.localeCompare(b.tag));
    }

    private renameSavedSelection(msg: any): void {
        const tag = typeof msg?.tag === "string" ? msg.tag : null;
        const newTag = typeof msg?.new_tag === "string" ? msg.new_tag : null;
        if (!tag || !newTag) return;
        this.savedSelections = this.savedSelections.map((item) => item.tag === tag ? { ...item, tag: newTag } : item)
            .sort((a, b) => a.tag.localeCompare(b.tag));
    }

    private deleteSavedSelection(msg: any): void {
        const tag = typeof msg?.tag === "string" ? msg.tag : null;
        if (!tag) return;
        this.savedSelections = this.savedSelections.filter((item) => item.tag !== tag);
    }

    private handlePotentialDoubleClickFocus(ev: any): void {
        if (!!ev?.modifiers?.shift) return;
        const items = lociToGroupItems(ev?.current?.loci);
        if (items.length !== 1) {
            this.lastPrimaryGroupClick = null;
            return;
        }
        const item = items[0];
        const key = `${item.chain_indices.join(",")}:${item.group_indices.join(",")}`;
        const time = Date.now();
        if (this.lastPrimaryGroupClick && this.lastPrimaryGroupClick.key === key && time - this.lastPrimaryGroupClick.time <= 400) {
            this.lastPrimaryGroupClick = null;
            this.focusTarget({ atom_indices: item.atom_indices });
            return;
        }
        this.lastPrimaryGroupClick = { key, time };
    }

    private atomIndicesToLoci(atomIndices: number[]): StructureElement.Loci | null {
        const structure = this.getStructureData();
        if (!structure) return null;
        const target = new Set(atomIndices);
        const lociElements: { unit: Unit.Atomic; indices: any }[] = [];
        for (const unit of structure.units) {
            if (!Unit.isAtomic(unit)) continue;
            const elements = unit.elements;
            const count = OrderedSet.size(elements);
            const matched: number[] = [];
            for (let i = 0; i < count; i++) {
                if (target.has(OrderedSet.getAt(elements, i))) matched.push(i);
            }
            if (matched.length > 0) {
                lociElements.push({ unit, indices: SortedArray.ofSortedArray(matched) });
            }
        }
        if (lociElements.length === 0) return null;
        return StructureElement.Loci(structure, lociElements as any);
    }

    private syncVisualSelection(selection: ActiveSelectionPayload): void {
        this.plugin.managers.interactivity.lociSelects.deselectAll();
        if (!selection || selection.source_kind === "empty" || selection.items.length === 0) return;
        const orderedItems = [...selection.items].sort((a, b) => {
            const left = a.group_indices[0] ?? a.atom_indices[0] ?? Number.MAX_SAFE_INTEGER;
            const right = b.group_indices[0] ?? b.atom_indices[0] ?? Number.MAX_SAFE_INTEGER;
            return left - right;
        });
        // Shape items: select the picked shape-group loci (face triangle, edge
        // cylinder, etc.) so it stays visually marked alongside its atoms. The
        // ``_loci`` refs only survive on the frontend's live JS items (not the
        // JSON-round-tripped ``msg.items``), so we read them from the controller.
        const liveItems = this.activeSelection.getCurrentItems();
        for (const liveItem of liveItems) {
            const shapeLoci = (liveItem as any)._loci;
            if (shapeLoci) {
                try {
                    this.plugin.managers.interactivity.lociSelects.select({ loci: shapeLoci }, true);
                } catch (e) {
                    console.warn("[MolSysViewer] shape loci select failed:", e);
                }
            }
        }
        for (const item of orderedItems) {
            const loci = this.atomIndicesToLoci(item.atom_indices);
            if (!loci) continue;
            this.plugin.managers.interactivity.lociSelects.select({ loci }, true);
        }
    }

    // Message Dispatcher
    async handleMessage(msg: ViewerMessage) {
        if (!msg || typeof msg !== "object") return;
        if (!("op" in msg)) {
            console.warn("[MolSysViewer] message missing 'op'", msg);
            return;
        }

        try {
            if ((msg as any).op === "load_molsys_payload") {
                const structures = (msg as any).payload?.structures;
                if (Array.isArray(structures)) {
                    this.trajectory.setExpectedFrameCount(structures.length);
                } else if ((msg as any).multiple_structures === true) {
                    // No structures array yet, but Python told us there are multiple frames.
                    this.trajectory.setExpectedFrameCount(2);
                }
            }
            switch (msg.op) {
                // Loader Ops
                case "load_structure_from_string":
                case "load_pdb_string": await this.loader.loadFromString(msg); break;
                case "load_molsys_payload": await this.loader.loadMolSysPayload(msg); break;
                case "load_structure_from_url": await this.loader.loadFromUrl(msg); break;
                case "load_pdb_id": await this.loader.loadPdbId(msg); break;

                // Shape Ops
                case "add_sphere": await this.shapes.addSphere(msg); break;
                case "update_sphere": {
                    const tag = typeof (msg as any).tag === "string"
                        ? (msg as any).tag
                        : typeof (msg as any).options?.tag === "string"
                            ? (msg as any).options.tag
                            : undefined;
                    if (typeof tag === "string") {
                        await this.state.deleteLayer({ op: "delete_layer", tag });
                        await this.shapes.addSphere({ op: "add_sphere", options: { ...((msg as any).options ?? {}), tag } });
                    }
                    break;
                }
                case "add_alpha_sphere_set": await this.shapes.addAlphaSphereSet(msg); break;
                case "add_pocket_surface": await this.shapes.addPocketSurface(msg); break;
                case "add_pocket_blob": await this.shapes.addPocketBlob(msg); break;
                case "add_scalar_isosurface": await this.shapes.addScalarIsosurface(msg); break;
                case "add_channel_tube": await this.shapes.addChannelTube(msg); break;
                case "add_rings": await this.shapes.addRings(msg); break;
                case "add_anisotropy_ellipsoids": await this.shapes.addAnisotropyEllipsoids(msg); break;
                case "add_pharmacophore_features": await this.shapes.addPharmacophore(msg); break;
                case "add_network_links": await this.shapes.addNetworkLinks(msg); break;
                case "add_hbonds": await this.shapes.addHbonds(msg); break;
                case "add_displacement_vectors": await this.shapes.addDisplacementVectors(msg); break;
                case "add_tetrahedra": await this.shapes.addTetrahedra(msg); break;
                case "add_triangle_faces": await this.shapes.addTriangleFaces(msg); break;
                case "add_label": {
                    await this.annotations.addLabel(msg);
                    const tag = (msg as any).tag ?? (msg as any).options?.tag ?? "annotation";
                    this.showToast(`Label added${tag !== "annotation" ? ` ('${tag}')` : ""}`);
                    break;
                }
                case "update_label": await this.annotations.updateLabel(msg); break;
                case "add_distance_measurement": {
                    await this.measurements.addDistance(msg);
                    const tag = (msg as any).tag ?? (msg as any).options?.tag ?? "measurement";
                    this.showToast(`Distance measurement added${tag !== "measurement" ? ` ('${tag}')` : ""}`);
                    break;
                }
                case "add_angle_measurement": {
                    await this.measurements.addAngle(msg);
                    const tag = (msg as any).tag ?? (msg as any).options?.tag ?? "measurement";
                    this.showToast(`Angle measurement added${tag !== "measurement" ? ` ('${tag}')` : ""}`);
                    break;
                }
                case "add_dihedral_measurement": {
                    await this.measurements.addDihedral(msg);
                    const tag = (msg as any).tag ?? (msg as any).options?.tag ?? "measurement";
                    this.showToast(`Dihedral measurement added${tag !== "measurement" ? ` ('${tag}')` : ""}`);
                    break;
                }
                case "set_measurement_settings": this.measurements.setSettings(msg.options); break;

                // Scene Ops
                case "reset_view":
                case "reset_camera": await this.scene.resetView(); break;
                case "toggle_fullscreen": await this.scene.toggleFullscreen(msg); break;
                case "toggle_background": await this.scene.toggleBackground(msg); break;
                case "toggle_swing": await this.scene.toggleSwing(msg); break;
                case "toggle_spin": await this.scene.toggleSpin(msg); break;
                case "set_fog": await this.scene.setFog(msg as any); break;
                case "set_sections": await this.scene.setSections(msg as any); break;
                case "sync_section_position": await this.scene.syncSectionPosition(msg as any); break;
                case "set_section_drag": await this.scene.setActiveSectionDrag(msg as any); break;
                case "set_background_color": await this.scene.setBackgroundColor(msg as any); break;
                case "set_lighting": await this.scene.setLighting(msg as any); break;
                case "set_clip_planes": await this.scene.setClipPlanes(msg as any); break;
                case "set_legend": this.legendOverlay.set((msg as any).options?.items, (msg as any).options?.position); break;
                case "set_camera_mode": await this.scene.setCameraMode(msg as any); break;
                case "set_panel_mode": this.setPanelMode((msg as any).panel, (msg as any).expanded); break;
                case "set_workspace": this.selectWorkspace((msg as any).workspace ?? "core"); break;
                case "set_workspace_panel": {
                    const workspaceId = typeof (msg as any).workspace === "string"
                        ? (msg as any).workspace
                        : this.currentWorkspace;
                    const panelId = typeof (msg as any).panel === "string"
                        ? (msg as any).panel
                        : "";
                    if (!panelId) break;
                    if (workspaceId === "core") {
                        this.selectWorkspace("core");
                        if (panelId === "navigate" || panelId === "workbench") {
                            this.setPanelMode(panelId, true);
                        }
                        break;
                    }
                    this.selectWorkspace(workspaceId);
                    this.selectWorkspacePanel(workspaceId, panelId);
                    break;
                }
                case "clear_scene": await this.scene.clearScene(msg); break;
                case "clear_all": await this.scene.clearAll(); break;
                case "clear_shapes_by_tag": await this.scene.clearShapesByTag(msg); break;

                // State/Region Ops
                case "update_visibility": await this.state.updateVisibility(msg); break;
                case "set_focus_fade": await this.state.setFocusFade(msg); break;
                case "create_region": {
                    await this.state.createRegion(msg);
                    const tag = (msg as any).tag || "region";
                    this.showToast(`Region '${tag}' created`);
                    break;
                }
                case "set_region_representation": await this.state.setRegionRepresentation(msg); break;
                case "show_region": await this.state.showRegion(msg); break;
                case "hide_region": await this.state.hideRegion(msg); break;
                case "delete_region": {
                    await this.state.deleteRegion(msg);
                    const tag = (msg as any).tag || "region";
                    this.showToast(`Region '${tag}' deleted`);
                    break;
                }
                case "rename_region": await this.state.renameRegion(msg); break;
                case "create_layer": await this.state.createLayer(msg); break;
                case "show_layer": await this.state.showLayer(msg); break;
                case "hide_layer": await this.state.hideLayer(msg); break;
                case "delete_layer":
                    if (typeof (msg as any).tag === "string" && this.measurements.hasTag((msg as any).tag)) {
                        this.measurements.dropTag((msg as any).tag);
                    }
                    await this.state.deleteLayer(msg);
                    break;
                case "set_layer_tag":
                    if (
                        typeof (msg as any).tag === "string"
                        && typeof (msg as any).new_tag === "string"
                        && this.measurements.hasTag((msg as any).tag)
                    ) {
                        this.measurements.renameTag((msg as any).tag, (msg as any).new_tag);
                    }
                    await this.state.setLayerTag(msg);
                    break;
                case "set_atom_colors": await this.state.setAtomColors(msg as any); break;
                case "clear_atom_colors": await this.state.clearAtomColors(msg as any); break;
                case "set_global_representation": await this.state.setGlobalRepresentation(msg); break;
                case "show_global": await this.state.showGlobal(msg); break;
                case "hide_global": await this.state.hideGlobal(msg); break;
                case "zoom": await this.state.zoom(msg); break;
                case "zoom_to_position": await this.scene.zoomToPosition(msg as any); break;
                case "set_camera_snapshot": await this.setCameraSnapshot((msg as any).snapshot, (msg as any).duration_ms); break;
                case "clear_active_selection":
                    this.activeSelection.clear();
                    break;
                case "set_active_selection":
                    this.activeSelection.setFromAtomIndices(
                        Array.isArray(msg.atom_indices) ? msg.atom_indices : [],
                        this.getStructureData(),
                    );
                    break;
                case "save_selection":
                    this.upsertSavedSelection(msg);
                    break;
                case "set_selection_tag":
                    this.renameSavedSelection(msg);
                    break;
                case "delete_selection":
                    this.deleteSavedSelection(msg);
                    break;
                case "clear_selections":
                    this.savedSelections = [];
                    break;

                // Trajectory Ops
                case "step_trajectory": await this.trajectory.stepTrajectory(msg); break;
                case "set_trajectory_frame": await this.trajectory.setTrajectoryFrame(msg); break;
                case "set_trajectory_playback": await this.trajectory.setTrajectoryPlayback(msg); break;
                case "partial_coordinates_update": await this.trajectory.partialCoordinatesUpdate(msg as any); break;

                // Movie Ops
                case "play_movie": {
                    const mode = (msg as any).mode ?? "play";
                    if (mode === "export") {
                        void this.movie.exportFrames(
                            (msg as any).keyframes ?? [],
                            Number((msg as any).fps ?? 25),
                            Number((msg as any).total_frames ?? 0),
                            typeof (msg as any).width_px === "number" ? (msg as any).width_px : undefined,
                            typeof (msg as any).height_px === "number" ? (msg as any).height_px : undefined,
                        );
                    } else {
                        this.movie.play(
                            (msg as any).keyframes ?? [],
                            !!(msg as any).loop,
                            typeof (msg as any).start_time_ms === "number" ? (msg as any).start_time_ms : 0.0
                        );
                    }
                    break;
                }
                case "stop_movie": this.movie.stop(); break;
                case "set_addon_runtime_summary": {
                    const prevWorkspaceIds = this.addonRuntimeInitialized
                        ? new Set(this.getWorkspaceOptions().map((item) => item.id))
                        : null;
                    this.addonWorkspaces = this.buildAddonWorkspaceSummary(msg as any);
                    this.addonPanels = this.buildAddonPanelSummary(msg as any);
                    if (!this.getWorkspaceOptions().some((item) => item.id === this.currentWorkspace)) {
                        this.currentWorkspace = "core";
                    }
                    this.workbenchAddons = this.buildAddonRuntimeSummary(msg as any);
                    this.workbenchAddonSections = this.buildAddonWorkbenchSectionSummary(msg as any);
                    this.addonContextActions = this.buildAddonContextActionSummary(msg as any);
                    this.addonRuntimeInitialized = true;
                    if (prevWorkspaceIds !== null) {
                        const newWorkspaces = this.getWorkspaceOptions().filter((item) => !prevWorkspaceIds.has(item.id));
                        if (newWorkspaces.length === 1 && this.currentWorkspace === "core") {
                            this.selectWorkspace(newWorkspaces[0].id);
                            break;
                        }
                    }
                    this.refreshWorkbenchPanel();
                    break;
                }

                case "set_addon_context_items": {
                    const rawItems = Array.isArray((msg as any).items) ? (msg as any).items : [];
                    this.addonContextItems = rawItems
                        .filter((it: any) => it && typeof it.addon === "string" && typeof it.id === "string" && typeof it.title === "string")
                        .map((it: any) => ({
                            addon: it.addon as string,
                            id: it.id as string,
                            title: it.title as string,
                            group: typeof it.group === "string" ? it.group : undefined,
                            order: typeof it.order === "number" ? it.order : 0,
                            enabled: it.enabled !== false,
                            target_kinds: Array.isArray(it.target_kinds)
                                ? it.target_kinds.filter((v: unknown): v is string => typeof v === "string")
                                : [],
                            payload: it.payload ?? {},
                        }));
                    break;
                }

                case "mount_addon_panel": {
                    const mAddon = (msg as any).addon as string | undefined;
                    const mPanel = (msg as any).panel as string | undefined;
                    const mEsm = (msg as any).esm as string | undefined;
                    const mCss = (msg as any).css as string | undefined;
                    if (!mAddon || !mPanel || !mEsm) break;
                    const mKey = `${mAddon}:${mPanel}`;
                    if (this.activePanelWidgetKey === mKey) break; // already mounted
                    this.cleanupActivePanelWidget();
                    const el = document.createElement("div");
                    Object.assign(el.style, { display: "flex", flexDirection: "column", gap: "8px", width: "100%" });
                    let styleEl: HTMLStyleElement | null = null;
                    if (mCss) {
                        styleEl = document.createElement("style");
                        styleEl.textContent = mCss;
                        el.appendChild(styleEl);
                    }
                    const msgListeners: Array<(msg: any) => void> = [];
                    this.activePanelMsgListeners = msgListeners;

                    const addonStateLocal: Record<string, any> = this.model
                        ? { ...((this.model.get("addon_states") || {})[mAddon] || {}) }
                        : {};
                    const changeListeners: Record<string, Array<(model: any, val: any) => void>> = {};

                    const panelModel = {
                        send: (content: any) => {
                            this.notify?.({ event: "addon_panel_action", addon: mAddon, panel: mPanel, content });
                        },
                        on: (event: string, cb: (msg: any) => void) => {
                            if (event === "msg:custom") {
                                msgListeners.push(cb);
                            } else if (event.startsWith("change:")) {
                                const key = event.split(":")[1];
                                if (key) {
                                     (changeListeners[key] || (changeListeners[key] = [])).push(cb);
                                }
                            } else if (event.startsWith("viewer:")) {
                                const viewerEvent = event.split(":")[1];
                                if (viewerEvent && mAddon) {
                                    this.registerAddonListener(mAddon, viewerEvent, cb);
                                }
                            }
                        },
                        off: (event: string, cb: (msg: any) => void) => {
                            if (event === "msg:custom") {
                                const idx = msgListeners.indexOf(cb);
                                if (idx >= 0) msgListeners.splice(idx, 1);
                            } else if (event.startsWith("change:")) {
                                const key = event.split(":")[1];
                                if (key && changeListeners[key]) {
                                    const idx = changeListeners[key].indexOf(cb);
                                    if (idx >= 0) changeListeners[key].splice(idx, 1);
                                }
                            } else if (event.startsWith("viewer:")) {
                                const viewerEvent = event.split(":")[1];
                                if (viewerEvent && mAddon) {
                                    this.unregisterAddonListener(mAddon, viewerEvent, cb);
                                }
                            }
                        },
                        get: (key: string) => {
                            if (this.model) {
                                const states = this.model.get("addon_states") || {};
                                const addonState = states[mAddon] || {};
                                return addonState[key];
                            }
                            return addonStateLocal[key];
                        },
                        set: (keyOrObj: any, val?: any) => {
                            const updates: Record<string, any> = {};
                            if (typeof keyOrObj === "string") {
                                updates[keyOrObj] = val;
                            } else if (keyOrObj && typeof keyOrObj === "object") {
                                Object.assign(updates, keyOrObj);
                            }

                            let changed = false;
                            for (const [k, v] of Object.entries(updates)) {
                                if (addonStateLocal[k] !== v) {
                                    addonStateLocal[k] = v;
                                    changed = true;
                                    if (changeListeners[k]) {
                                        for (const cb of changeListeners[k]) {
                                            try { cb(panelModel, v); } catch (e) { console.error(e); }
                                        }
                                    }
                                }
                            }

                            if (this.model && changed) {
                                const states = { ...this.model.get("addon_states") || {} };
                                states[mAddon] = { ...states[mAddon] || {}, ...addonStateLocal };
                                this.model.set("addon_states", states);
                                this.model.save_changes();
                            }

                            this.notify?.({
                                event: "addon_panel_state_changed",
                                addon: mAddon,
                                panel: mPanel,
                                state: updates
                            });
                        }
                    };

                    let onModelChange: (() => void) | undefined = undefined;
                    if (this.model) {
                        onModelChange = () => {
                            const states = this.model.get("addon_states") || {};
                            const addonState = states[mAddon] || {};
                            for (const key of Object.keys(changeListeners)) {
                                const v = addonState[key];
                                if (addonStateLocal[key] !== v) {
                                    addonStateLocal[key] = v;
                                    for (const cb of changeListeners[key]) {
                                        try { cb(panelModel, v); } catch (e) { console.error(e); }
                                    }
                                }
                            }
                        };
                        this.model.on("change:addon_states", onModelChange);
                    }

                    const blob = new Blob([mEsm], { type: "application/javascript" });
                    const blobUrl = URL.createObjectURL(blob);
                    try {
                        const module = await import(/* @vite-ignore */ blobUrl);
                        const renderFn = module.default?.render ?? module.render;
                        let cleanup: (() => void) | undefined;
                        if (typeof renderFn === "function") {
                            const result = renderFn({ model: panelModel, el });
                            if (typeof result === "function") cleanup = result;
                        }
                        this.activePanelCleanup = () => {
                            if (typeof cleanup === "function") { try { cleanup(); } catch { /* ignore */ } }
                            if (this.model && onModelChange) {
                                this.model.off("change:addon_states", onModelChange);
                            }
                            URL.revokeObjectURL(blobUrl);
                        };
                    } catch (err) {
                        console.error("[MolSysViewer] Error loading addon panel ESM:", err);
                        URL.revokeObjectURL(blobUrl);
                        break;
                    }
                    this.activePanelWidgetKey = mKey;
                    this.workbenchPanel.mountAddonWidget(el);
                    break;
                }

                case "addon_panel_message": {
                    const content = (msg as any).content;
                    if (content) {
                        for (const cb of this.activePanelMsgListeners) {
                            try { cb(content); } catch { /* ignore */ }
                        }
                    }
                    break;
                }

                case "set_canvas_visibility": {
                    const visible = (msg as any).visible !== false;
                    this.setCanvasVisibility(visible);
                    break;
                }

                default:
                    console.warn("[MolSysViewer] unknown op:", (msg as any).op, msg);
                    break;
            }
            this.applyWorkbenchMessage(msg);
            this.refreshNavigatePanel();
            this.refreshWorkbenchPanel();
            this.syncStripOverlaysForMessage(msg);
        } catch (error) {
            console.error("[MolSysViewer] Error handling message:", msg, error);
        }
    }

    // Helper accessors for internal state management
    
    private getStructureData(): Structure | undefined {
        const structures = this.plugin.managers.structure.hierarchy.current.structures;
        const last = structures.length ? structures[structures.length - 1] : undefined;
        return last?.cell.obj?.data;
    }

    private getComponents(): StructureComponentRef[] {
        const structures = this.plugin.managers.structure.hierarchy.current.structures;
        const last = structures.length ? structures[structures.length - 1] : undefined;
        return last?.components ?? [];
    }

    private captureCurrentStructure() {
        const structures = this.plugin.managers.structure.hierarchy.current.structures;
        const last = structures.length ? structures[structures.length - 1] : undefined;
        if (last) {
            const structure = last.cell.obj?.data;
            this.currentStructure = last.cell.transform.ref as any;
            this.groupPanel.setStructure(structure);
            this.refreshNavigatePanel();
            this.workbenchPanel.setVisible(true);
            if (structure) {
                this.activeSelection.setAllAvailableItems(buildGroupItemsFromStructure(structure));
            }
            // Notify state handler that structure is ready so it can apply pending ops
            this.state.onStructureLoaded();
            this.trajectory.notifyListeners();
        } else {
            this.currentStructure = undefined;
            this.groupPanel.setStructure(undefined);
            this.refreshNavigatePanel();
            this.activeSelection.setAllAvailableItems([]);
        }
        this.updateWelcomeState();
    }

    private async removeLoadedStructure() {
        if (!this.loadedStructure) return;
        await this.state.clearState(); // Clear regions/layers first
        const refs: Array<StateObjectRef | undefined> = [
            this.loadedStructure.structure,
            this.loadedStructure.trajectory,
            this.loadedStructure.data,
        ];
        for (const ref of refs) {
            if (ref) {
                await PluginCommands.State.RemoveObject(this.plugin, {
                    state: this.plugin.state.data,
                    ref,
                    removeParentGhosts: true,
                });
            }
        }
        this.loadedStructure = undefined;
        this.currentStructure = undefined;
        this.groupPanel.setStructure(undefined);
        this.workbenchPanel.setVisible(false);
        this.updateWelcomeState();
    }

    private applyWorkbenchMessage(msg: ViewerMessage): void {
        const op = (msg as any)?.op;
        if (typeof op !== "string") return;

        const upsertWorkbenchShape = (
            tag: string,
            title: string,
            subtitle: string | undefined,
            layerTag: string | undefined,
            atomIndices: number[],
        ) => {
            const existing = this.workbenchShapes.get(tag);
            this.workbenchShapes.set(tag, {
                title: existing?.title ?? title,
                subtitle: existing?.subtitle ?? subtitle,
                layerTag,
                hidden: existing?.hidden ?? false,
                atomIndices: atomIndices.length > 0 ? atomIndices : (existing?.atomIndices ?? []),
            });
        };

        if (op === "clear_all") {
            this.workbenchAnnotations.clear();
            this.workbenchMeasurements.clear();
            this.workbenchShapes.clear();
            this.workbenchScene = null;
            this.workbenchActive = null;
            this.workbenchContext = null;
            return;
        }

        if (op === "clear_scene") {
            const options = (msg as any).options ?? {};
            if (options.labels) this.workbenchAnnotations.clear();
            if (options.shapes) this.workbenchShapes.clear();
            if (options.styles) this.workbenchScene = null;
            if (this.workbenchActive?.section === "annotations" && options.labels) this.workbenchActive = null;
            if (this.workbenchActive?.section === "shapes" && options.shapes) this.workbenchActive = null;
            if (this.workbenchContext?.section === "annotations" && options.labels) this.workbenchContext = null;
            if (this.workbenchContext?.section === "shapes" && options.shapes) this.workbenchContext = null;
            return;
        }

        if (op === "add_label") {
            const tag = (msg as any).tag ?? (msg as any).options?.tag;
            const text = (msg as any).options?.text;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            const atomIndices = Array.isArray((msg as any).options?.atom_indices)
                ? (msg as any).options.atom_indices.filter((value: unknown) => typeof value === "number")
                : [];
            if (typeof tag === "string" && typeof text === "string" && text.trim()) {
                this.workbenchAnnotations.set(tag, { text: text.trim(), layerTag, hidden: false, atomIndices });
            }
            return;
        }

        if (op === "update_label") {
            const tag = (msg as any).tag ?? (msg as any).options?.tag;
            const existing = typeof tag === "string" ? this.workbenchAnnotations.get(tag) : undefined;
            if (!existing || typeof tag !== "string") return;
            const nextText = (msg as any).options?.text;
            const nextAtomIndices = Array.isArray((msg as any).options?.atom_indices)
                ? (msg as any).options.atom_indices.filter((value: unknown) => typeof value === "number")
                : existing.atomIndices;
            this.workbenchAnnotations.set(tag, {
                text: typeof nextText === "string" && nextText.trim() ? nextText.trim() : existing.text,
                layerTag: typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : existing.layerTag,
                hidden: existing.hidden,
                atomIndices: nextAtomIndices,
            });
            return;
        }

        if (op === "add_distance_measurement" || op === "add_angle_measurement" || op === "add_dihedral_measurement") {
            const tag = (msg as any).tag ?? (msg as any).options?.tag;
            const picksArray = Array.isArray((msg as any).options?.picks_atom_indices) ? (msg as any).options.picks_atom_indices : [];
            const picks = picksArray.length;
            const atomIndices = Array.from(new Set(
                picksArray.flatMap((item: unknown) => Array.isArray(item) ? item : [])
                    .filter((value: unknown) => typeof value === "number")
            ));
            const kind = op === "add_distance_measurement" ? "distance" : op === "add_angle_measurement" ? "angle" : "dihedral";
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            if (typeof tag === "string") {
                this.workbenchMeasurements.set(tag, { kind, picks, layerTag, hidden: false, atomIndices });
            }
            return;
        }

        if (op === "add_sphere" || op === "update_sphere") {
            const tag = (msg as any).tag ?? (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Sphere", "sphere", layerTag, []);
            }
            return;
        }

        if (op === "add_network_links") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            const atomPairs = Array.isArray((msg as any).options?.atom_pairs) ? (msg as any).options.atom_pairs : [];
            const atomIndices = Array.from(new Set(
                atomPairs.flatMap((item: unknown) => Array.isArray(item) ? item : [])
                    .filter((value: unknown) => typeof value === "number")
            ));
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Links", "links", layerTag, atomIndices);
            }
            return;
        }

        if (op === "add_triangle_faces") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            const atomTriplets = Array.isArray((msg as any).options?.atom_triplets)
                ? (msg as any).options.atom_triplets
                : Array.isArray((msg as any).options?.atomTriplets)
                    ? (msg as any).options.atomTriplets
                    : [];
            const atomIndices = Array.from(new Set(
                atomTriplets.flatMap((item: unknown) => Array.isArray(item) ? item : [])
                    .filter((value: unknown) => typeof value === "number")
            ));
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Triangle Faces", "triangle_faces", layerTag, atomIndices);
            }
            return;
        }

        if (op === "add_channel_tube") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Channel Tube", "channel_tube", layerTag, []);
            }
            return;
        }

        if (op === "add_tetrahedra") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            const atomQuads = Array.isArray((msg as any).options?.atom_quads)
                ? (msg as any).options.atom_quads
                : Array.isArray((msg as any).options?.atomQuads)
                    ? (msg as any).options.atomQuads
                    : [];
            const atomIndices = Array.from(new Set(
                atomQuads.flatMap((item: unknown) => Array.isArray(item) ? item : [])
                    .filter((value: unknown) => typeof value === "number")
            ));
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Tetrahedra", "tetrahedra", layerTag, atomIndices);
            }
            return;
        }

        if (op === "add_anisotropy_ellipsoids") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            const atomIndices = Array.isArray((msg as any).options?.atom_indices)
                ? (msg as any).options.atom_indices.filter((value: unknown) => typeof value === "number")
                : [];
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Anisotropy Ellipsoids", "anisotropy_ellipsoids", layerTag, atomIndices);
            }
            return;
        }

        if (op === "add_pharmacophore_features") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Pharmacophore", "pharmacophore", layerTag, []);
            }
            return;
        }

        if (op === "add_displacement_vectors") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            const atomIndices = Array.isArray((msg as any).options?.atom_indices)
                ? (msg as any).options.atom_indices.filter((value: unknown) => typeof value === "number")
                : [];
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Displacement Vectors", "displacement_vectors", layerTag, atomIndices);
            }
            return;
        }

        if (op === "add_pocket_blob" || op === "add_scalar_isosurface") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Pocket Blob", "pocket_blob", layerTag, []);
            }
            return;
        }

        if (op === "add_pocket_surface") {
            const tag = (msg as any).options?.tag;
            const layerTag = typeof (msg as any).options?.layer_tag === "string" ? (msg as any).options.layer_tag : undefined;
            const atomIndices = Array.isArray((msg as any).options?.atom_indices)
                ? (msg as any).options.atom_indices.filter((value: unknown) => typeof value === "number")
                : [];
            if (typeof tag === "string") {
                upsertWorkbenchShape(tag, "Pocket Surface", "pocket_surface", layerTag, atomIndices);
            }
            return;
        }

        if (op === "create_layer") {
            const tag = (msg as any).tag;
            const kind = (msg as any).kind;
            const meta = (msg as any).meta ?? {};
            if (typeof tag === "string" && kind === "shape") {
                const title =
                    typeof meta.shape_name === "string" && meta.shape_name.trim()
                        ? meta.shape_name.trim()
                        : typeof meta.label === "string" && meta.label.trim()
                            ? meta.label.trim()
                            : "Shape";
                const subtitle = typeof meta.shape_kind === "string" && meta.shape_kind.trim() ? meta.shape_kind.trim() : undefined;
                const layerTag = typeof meta.layer_tag === "string" && meta.layer_tag.trim() ? meta.layer_tag.trim() : undefined;
                const atomIndices = Array.isArray(meta.atom_indices)
                    ? meta.atom_indices.filter((value: unknown) => typeof value === "number")
                    : [];
                this.workbenchShapes.set(tag, { title, subtitle, layerTag, hidden: false, atomIndices });
            }
            return;
        }

        if (op === "hide_layer" || op === "show_layer") {
            const tag = (msg as any).tag;
            if (typeof tag !== "string") return;
            const hidden = op === "hide_layer";
            if (this.workbenchAnnotations.has(tag)) {
                const item = this.workbenchAnnotations.get(tag)!;
                this.workbenchAnnotations.set(tag, { ...item, hidden });
            }
            if (this.workbenchMeasurements.has(tag)) {
                const item = this.workbenchMeasurements.get(tag)!;
                this.workbenchMeasurements.set(tag, { ...item, hidden });
            }
            if (this.workbenchShapes.has(tag)) {
                const item = this.workbenchShapes.get(tag)!;
                this.workbenchShapes.set(tag, { ...item, hidden });
            }
            return;
        }

        if (op === "delete_layer") {
            const tag = (msg as any).tag;
            if (typeof tag !== "string") return;
            this.workbenchAnnotations.delete(tag);
            this.workbenchMeasurements.delete(tag);
            this.workbenchShapes.delete(tag);
            if (this.workbenchActive?.tag === tag) this.workbenchActive = null;
            if (this.workbenchContext?.tag === tag) this.workbenchContext = null;
            return;
        }

        if (op === "set_layer_tag") {
            const oldTag = (msg as any).tag;
            const newTag = (msg as any).new_tag;
            if (typeof oldTag !== "string" || typeof newTag !== "string") return;
            if (this.workbenchAnnotations.has(oldTag)) {
                const item = this.workbenchAnnotations.get(oldTag)!;
                this.workbenchAnnotations.delete(oldTag);
                this.workbenchAnnotations.set(newTag, item);
                if (this.workbenchActive?.section === "annotations" && this.workbenchActive.tag === oldTag) {
                    this.workbenchActive = { section: "annotations", tag: newTag };
                }
                if (this.workbenchContext?.section === "annotations" && this.workbenchContext.tag === oldTag) {
                    this.workbenchContext = { section: "annotations", tag: newTag };
                }
            }
            if (this.workbenchMeasurements.has(oldTag)) {
                const item = this.workbenchMeasurements.get(oldTag)!;
                this.workbenchMeasurements.delete(oldTag);
                this.workbenchMeasurements.set(newTag, item);
                if (this.workbenchActive?.section === "measurements" && this.workbenchActive.tag === oldTag) {
                    this.workbenchActive = { section: "measurements", tag: newTag };
                }
            }
            if (this.workbenchShapes.has(oldTag)) {
                const item = this.workbenchShapes.get(oldTag)!;
                this.workbenchShapes.delete(oldTag);
                this.workbenchShapes.set(newTag, item);
                if (this.workbenchActive?.section === "shapes" && this.workbenchActive.tag === oldTag) {
                    this.workbenchActive = { section: "shapes", tag: newTag };
                }
                if (this.workbenchContext?.section === "shapes" && this.workbenchContext.tag === oldTag) {
                    this.workbenchContext = { section: "shapes", tag: newTag };
                }
            }
            return;
        }

        if (op === "load_molsys_payload" || op === "load_structure_from_string" || op === "load_pdb_string" ||
            op === "load_structure_from_url" || op === "load_pdb_id") {
            if (this.workbenchScene === null) {
                this.workbenchScene = {
                    figurePreset: "publication-light",
                    figureScale: 2.0,
                    figureVariants: ["dark", "transparent"],
                };
            }
            return;
        }

        if (op === "set_global_representation") {
            const styleTag =
                typeof (msg as any).user_preset?.name === "string"
                    ? (msg as any).user_preset.name
                    : typeof (msg as any).preset === "string"
                        ? (msg as any).preset
                        : undefined;
            const preset =
                typeof (msg as any).preset === "string"
                    ? (msg as any).preset
                    : typeof (msg as any).representation === "string"
                        ? (msg as any).representation
                        : undefined;
            this.workbenchScene = {
                ...this.workbenchScene,
                styleTag,
                preset,
                figurePreset: "publication-light",
                figureScale: 2.0,
                figureVariants: ["dark", "transparent"],
            };
        }

        if (op === "set_figure_spec") {
            const figurePreset = typeof (msg as any).figure_preset === "string" ? (msg as any).figure_preset : undefined;
            const figureScale = typeof (msg as any).figure_scale === "number" ? (msg as any).figure_scale : undefined;
            const figureVariants = Array.isArray((msg as any).figure_variants) ? (msg as any).figure_variants as string[] : undefined;
            this.workbenchScene = {
                ...this.workbenchScene,
                ...(figurePreset !== undefined ? { figurePreset } : {}),
                ...(figureScale !== undefined ? { figureScale } : {}),
                ...(figureVariants !== undefined ? { figureVariants } : {}),
            };
        }
    }

    private refreshWorkbenchPanel(): void {
        this.workbenchPanel.setAnnotations(
            Array.from(this.workbenchAnnotations.entries())
                .sort(([left], [right]) => left.localeCompare(right))
                .map(([tag, item]) => ({
                    key: tag,
                    title: item.text,
                    subtitle: item.layerTag && item.layerTag !== tag ? `${tag} · layer: ${item.layerTag}` : tag,
                    hidden: item.hidden,
                    active: this.workbenchActive?.section === "annotations" && this.workbenchActive.tag === tag,
                    context: this.workbenchContext?.section === "annotations" && this.workbenchContext.tag === tag,
                    onActivate: item.atomIndices.length > 0 ? () => {
                        this.workbenchActive = { section: "annotations", tag };
                        this.refreshWorkbenchPanel();
                        this.focusTarget({ atom_indices: item.atomIndices });
                    } : undefined,
                    onToggleVisibility: () => {
                        void this.handleMessage({ op: item.hidden ? "show_layer" : "hide_layer", tag });
                    },
                }))
        );
        this.workbenchPanel.setMeasurements(
            Array.from(this.workbenchMeasurements.entries())
                .sort(([left], [right]) => left.localeCompare(right))
                .map(([tag, item]) => ({
                    key: tag,
                    title: item.kind[0].toUpperCase() + item.kind.slice(1),
                    subtitle: item.layerTag && item.layerTag !== tag
                        ? `${tag} · ${item.picks} picks · layer: ${item.layerTag}`
                        : `${tag} · ${item.picks} picks`,
                    hidden: item.hidden,
                    active: this.workbenchActive?.section === "measurements" && this.workbenchActive.tag === tag,
                    onActivate: item.atomIndices.length > 0 ? () => {
                        this.workbenchActive = { section: "measurements", tag };
                        this.refreshWorkbenchPanel();
                        this.focusTarget({ atom_indices: item.atomIndices });
                    } : undefined,
                    onToggleVisibility: () => {
                        void this.handleMessage({ op: item.hidden ? "show_layer" : "hide_layer", tag });
                    },
                }))
        );
        this.workbenchPanel.setShapes(
            Array.from(this.workbenchShapes.entries())
                .sort(([left], [right]) => left.localeCompare(right))
                .map(([tag, item]) => ({
                    key: tag,
                    title: item.title,
                    subtitle: item.layerTag && item.layerTag !== tag
                        ? item.subtitle ? `${tag} · ${item.subtitle} · layer: ${item.layerTag}` : `${tag} · layer: ${item.layerTag}`
                        : item.subtitle ? `${tag} · ${item.subtitle}` : tag,
                    hidden: item.hidden,
                    active: this.workbenchActive?.section === "shapes" && this.workbenchActive.tag === tag,
                    context: this.workbenchContext?.section === "shapes" && this.workbenchContext.tag === tag,
                    onActivate: item.atomIndices.length > 0 ? () => {
                        this.workbenchActive = { section: "shapes", tag };
                        this.refreshWorkbenchPanel();
                        this.focusTarget({ atom_indices: item.atomIndices });
                    } : undefined,
                    onToggleVisibility: () => {
                        void this.handleMessage({ op: item.hidden ? "show_layer" : "hide_layer", tag });
                    },
                }))
        );
        this.workbenchPanel.setScene(this.workbenchScene);
        if (this.currentWorkspace === "core") {
            this.workbenchPanel.setActiveWorkspacePanel(null);
        } else {
            const panels = this.getWorkspacePanels(this.currentWorkspace);
            const selectedId = this.ensureWorkspacePanelSelection(this.currentWorkspace);
            this.workbenchPanel.setWorkspacePanels(
                panels.map((item) => ({
                    id: item.id,
                    title: item.title,
                    description: item.description,
                    entry: item.entry,
                    addon: item.addon,
                    active: item.id === selectedId,
                })),
                (panelId) => {
                    this.selectWorkspacePanel(this.currentWorkspace, panelId);
                },
            );
            const activePanel = panels.find((item) => item.id === selectedId) ?? null;
            const workspaceTitle = this.getWorkspaceOptions().find((item) => item.id === this.currentWorkspace)?.title ?? this.currentWorkspace;
            const workspaceSections = this.workbenchAddonSections.filter((item) => item.workspaceId === this.currentWorkspace);
            const activeAddonSummary = activePanel
                ? this.workbenchAddons.find((item) => item.name === activePanel.addon)
                : null;
            this.workbenchPanel.setActiveWorkspacePanel(
                activePanel
                    ? {
                        workspaceTitle,
                        title: activePanel.title,
                        description: activePanel.description,
                        entry: activePanel.entry,
                        addon: activePanel.addon,
                        contextActionTitles: activeAddonSummary?.contextActionTitles ?? [],
                        exportHelperTitles: activeAddonSummary?.exportHelperTitles ?? [],
                        sections: workspaceSections.map((item) => ({
                            key: item.key,
                            title: item.title,
                            itemTitle: item.itemTitle,
                            itemSubtitle: item.itemSubtitle,
                        })),
                    }
                    : null,
            );
        }
        this.refreshPanelWorkspaceChrome();
        this.workbenchPanel.setAddons(
            this.workbenchAddons.map((item) => ({
                ...item,
                active: this.currentWorkspace !== "core" && this.workspaceBelongsToAddon(this.currentWorkspace, item.name),
            }))
        );
        this.workbenchPanel.setAddonWorkbenchSections([]);
    }

    private buildAddonWorkspaceSummary(msg: any): WorkspaceRuntime[] {
        const specs = Array.isArray(msg?.workspace_specs) ? msg.workspace_specs : [];
        return specs
            .filter((item: any) => typeof item?.id === "string" && typeof item?.title === "string")
            .map((item: any) => ({
                id: item.id as string,
                title: item.title as string,
                addon: typeof item?.addon === "string" ? item.addon as string : undefined,
            }))
            .sort((left, right) => left.id.localeCompare(right.id));
    }

    private buildAddonPanelSummary(msg: any): AddonPanelRuntime[] {
        const specs = Array.isArray(msg?.panel_specs) ? msg.panel_specs : [];
        const workspaceSpecs = Array.isArray(msg?.workspace_specs) ? msg.workspace_specs : [];
        const workspaceByAddon = new Map<string, string>();
        for (const item of workspaceSpecs) {
            if (typeof item?.addon !== "string" || typeof item?.id !== "string") continue;
            if (!workspaceByAddon.has(item.addon)) workspaceByAddon.set(item.addon, item.id);
        }
        return specs
            .filter(
                (item: any) =>
                    typeof item?.addon === "string"
                    && typeof item?.id === "string"
                    && typeof item?.title === "string"
                    && (item?.target === undefined || item?.target === "panel_mode"),
            )
            .map((item: any) => ({
                key: `${item.addon}:${item.id}`,
                workspaceId: workspaceByAddon.get(item.addon as string) ?? (item.addon as string),
                addon: item.addon as string,
                id: item.id as string,
                title: item.title as string,
                description: typeof item?.description === "string" ? item.description as string : undefined,
                entry: typeof item?.entry === "string" ? item.entry as string : undefined,
                widget_class: typeof item?.widget_class === "string" ? item.widget_class as string : undefined,
            }))
            .sort((left, right) => left.key.localeCompare(right.key));
    }

    private buildAddonRuntimeSummary(msg: any): AddonRuntimeSummary[] {
        const names = Array.isArray(msg?.addons)
            ? msg.addons.filter((value: unknown): value is string => typeof value === "string")
            : [];
        const workspaceSpecs = Array.isArray(msg?.workspace_specs) ? msg.workspace_specs : [];
        const panelSpecs = Array.isArray(msg?.panel_specs) ? msg.panel_specs : [];
        const workbenchSections = Array.isArray(msg?.workbench_sections) ? msg.workbench_sections : [];
        const contextActionSpecs = Array.isArray(msg?.context_action_specs) ? msg.context_action_specs : [];
        const exportHelperSpecs = Array.isArray(msg?.export_helper_specs) ? msg.export_helper_specs : [];

        return names
            .map((name) => ({
                name,
                workspaceTitles: workspaceSpecs
                    .filter((item: any) => item?.addon === name && typeof item?.title === "string")
                    .map((item: any) => item.title as string),
                panelTitles: panelSpecs
                    .filter((item: any) => item?.addon === name && typeof item?.title === "string")
                    .map((item: any) => item.title as string),
                workbenchTitles: workbenchSections
                    .filter((item: any) => item?.addon === name && typeof item?.title === "string")
                    .map((item: any) => item.title as string),
                contextActionTitles: contextActionSpecs
                    .filter((item: any) => item?.addon === name && typeof item?.title === "string")
                    .map((item: any) => item.title as string),
                exportHelperTitles: exportHelperSpecs
                    .filter((item: any) => item?.addon === name && typeof item?.title === "string")
                    .map((item: any) => item.title as string),
            }))
            .sort((left, right) => left.name.localeCompare(right.name));
    }

    private buildAddonWorkbenchSectionSummary(msg: any): AddonWorkbenchSectionRuntime[] {
        const specs = Array.isArray(msg?.workbench_sections) ? msg.workbench_sections : [];
        const workspaceSpecs = Array.isArray(msg?.workspace_specs) ? msg.workspace_specs : [];
        const workspaceByAddon = new Map<string, string>();
        for (const item of workspaceSpecs) {
            if (typeof item?.addon !== "string" || typeof item?.id !== "string") continue;
            if (!workspaceByAddon.has(item.addon)) workspaceByAddon.set(item.addon, item.id);
        }
        return specs
            .filter(
                (item: any) =>
                    typeof item?.addon === "string"
                    && typeof item?.id === "string"
                    && typeof item?.title === "string"
                    && (item?.target_panel === undefined || item?.target_panel === "workbench")
            )
            .map((item: any) => ({
                key: `${item.addon}:${item.id}`,
                workspaceId: workspaceByAddon.get(item.addon as string) ?? (item.addon as string),
                addon: item.addon as string,
                title: item.title as string,
                itemTitle: `Add-on: ${item.addon as string}`,
                itemSubtitle: typeof item?.entry === "string" ? item.entry as string : undefined,
            }))
            .sort((left, right) => left.key.localeCompare(right.key));
    }

    private buildAddonContextActionSummary(msg: any): AddonContextActionRuntime[] {
        const specs = Array.isArray(msg?.context_action_specs) ? msg.context_action_specs : [];
        return specs
            .filter((item: any) => typeof item?.addon === "string" && typeof item?.id === "string" && typeof item?.title === "string")
            .map((item: any) => ({
                addon: item.addon as string,
                id: item.id as string,
                title: item.title as string,
                target_kinds: Array.isArray(item.target_kinds)
                    ? item.target_kinds.filter((value: unknown): value is string => typeof value === "string")
                    : [],
                group: typeof item.group === "string" ? item.group : undefined,
            }))
            .sort((left, right) => `${left.addon}:${left.id}`.localeCompare(`${right.addon}:${right.id}`));
    }

    private refreshNavigatePanel(): void {
        this.groupPanel.setSavedSelections(this.savedSelections);
        this.groupPanel.setRegions(
            this.state.getRegionSummaries().map((item) => ({
                tag: item.tag,
                atom_count: item.atom_count,
                hidden: item.hidden,
            }))
        );
        this.refreshPanelWorkspaceChrome();
    }

    private getWorkspaceOptions(): WorkspaceRuntime[] {
        const options: WorkspaceRuntime[] = [
            { id: "core", title: "Core", subtitle: "Navigate + Workbench" },
        ];

        for (const workspace of this.addonWorkspaces) {
            const panelCount = this.getWorkspacePanels(workspace.id).length;
            const workbenchSections = this.workbenchAddonSections.filter((item) => item.workspaceId === workspace.id);
            const workbenchSectionCount = workbenchSections.length;
            const workbenchSectionTitles = workbenchSections.map((item) => item.title);
            const contextActionCount = this.addonContextActions.filter((item) => this.workspaceBelongsToAddon(workspace.id, item.addon)).length;
            const exportHelperCount = this.workbenchAddons.find((item) => item.name === workspace.addon)?.exportHelperTitles.length ?? 0;
            const totalVisible = panelCount + workbenchSectionCount;
            if (totalVisible <= 0) continue;

            const summaryParts: string[] = [];
            if (panelCount > 0) summaryParts.push(`${panelCount} panel${panelCount === 1 ? "" : "s"}`);
            if (workbenchSectionCount > 0) summaryParts.push(`${workbenchSectionCount} section${workbenchSectionCount === 1 ? "" : "s"}`);
            if (contextActionCount > 0) summaryParts.push(`${contextActionCount} context action${contextActionCount === 1 ? "" : "s"}`);
            if (exportHelperCount > 0) summaryParts.push(`${exportHelperCount} export helper${exportHelperCount === 1 ? "" : "s"}`);

            options.push({
                ...workspace,
                subtitle: summaryParts.join(" · "),
                panelCount,
                workbenchSectionCount,
                workbenchSectionTitles,
                contextActionCount,
                exportHelperCount,
            });
        }

        return options;
    }

    private getWorkspacePanels(workspaceId: string): AddonPanelRuntime[] {
        return this.addonPanels.filter((item) => item.workspaceId === workspaceId);
    }

    private ensureWorkspacePanelSelection(workspaceId: string): string | null {
        const panels = this.getWorkspacePanels(workspaceId);
        if (panels.length === 0) {
            this.currentWorkspacePanelByWorkspace.delete(workspaceId);
            return null;
        }
        const current = this.currentWorkspacePanelByWorkspace.get(workspaceId);
        if (current && panels.some((item) => item.id === current)) return current;
        const next = panels[0].id;
        this.currentWorkspacePanelByWorkspace.set(workspaceId, next);
        return next;
    }

    private cleanupActivePanelWidget(): void {
        if (this.activePanelWidgetKey) {
            const parts = this.activePanelWidgetKey.split(":");
            if (parts.length > 0) {
                const addonName = parts[0];
                this.addonListeners.delete(addonName);
            }
        }
        if (this.activePanelCleanup) {
            try { this.activePanelCleanup(); } catch { /* ignore */ }
            this.activePanelCleanup = null;
        }
        this.activePanelMsgListeners = [];
        this.activePanelWidgetKey = null;
        this.workbenchPanel.unmountAddonWidget();
    }

    private selectWorkspacePanel(workspaceId: string, panelId: string): void {
        const panels = this.getWorkspacePanels(workspaceId);
        if (!panels.some((item) => item.id === panelId)) return;

        // Unmount previous widget panel if navigating away from one
        const prevPanelId = this.currentWorkspacePanelByWorkspace.get(workspaceId);
        if (prevPanelId && prevPanelId !== panelId) {
            const prevPanel = panels.find((item) => item.id === prevPanelId);
            if (prevPanel?.widget_class) {
                this.notify?.({ event: "panel_unmount", addon: prevPanel.addon, panel: prevPanelId });
                this.cleanupActivePanelWidget();
            }
        }

        this.currentWorkspacePanelByWorkspace.set(workspaceId, panelId);

        // Mount new widget panel if it has one
        const newPanel = panels.find((item) => item.id === panelId);
        const newKey = `${workspaceId}:${panelId}`;
        if (newPanel?.widget_class && this.activePanelWidgetKey !== newKey) {
            this.notify?.({ event: "panel_navigate", addon: newPanel.addon, panel: panelId });
        } else if (!newPanel?.widget_class) {
            this.cleanupActivePanelWidget();
        }

        this.refreshWorkbenchPanel();
        this.emitPanelModeState();
    }

    private workspaceBelongsToAddon(workspaceId: string, addonName: string): boolean {
        return this.addonWorkspaces.some((item) => item.id === workspaceId && item.addon === addonName);
    }

    private showToast(message: string, durationMs = 3000): void {
        const toast = document.createElement("div");
        toast.setAttribute("data-molsysviewer-toast", "true");
        Object.assign(toast.style, {
            position: "absolute",
            bottom: "48px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(24,24,30,0.93)",
            color: "rgba(244,244,245,0.96)",
            border: "1px solid rgba(255,255,255,0.14)",
            borderRadius: "8px",
            padding: "7px 16px",
            fontSize: "12px",
            fontWeight: "500",
            zIndex: "9999",
            pointerEvents: "none",
            whiteSpace: "nowrap",
            opacity: "1",
            transition: "opacity 0.35s ease",
        });
        toast.textContent = message;
        if (!this.host.style.position || this.host.style.position === "static") {
            this.host.style.position = "relative";
        }
        this.host.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            setTimeout(() => toast.remove(), 400);
        }, durationMs);
    }

    private injectGlobalStyles(): void {
        if (document.getElementById("molsysviewer-global-styles")) return;
        const style = document.createElement("style");
        style.id = "molsysviewer-global-styles";
        style.textContent = `
            [data-molsysviewer-group-panel-body]::-webkit-scrollbar,
            [data-molsysviewer-group-panel-section]::-webkit-scrollbar,
            [data-molsysviewer-group-strip]::-webkit-scrollbar,
            [data-molsysviewer-group-strip-row]::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            [data-molsysviewer-group-panel-body]::-webkit-scrollbar-track,
            [data-molsysviewer-group-panel-section]::-webkit-scrollbar-track,
            [data-molsysviewer-group-strip]::-webkit-scrollbar-track,
            [data-molsysviewer-group-strip-row]::-webkit-scrollbar-track {
                background: transparent;
            }
            [data-molsysviewer-group-panel-body]::-webkit-scrollbar-thumb,
            [data-molsysviewer-group-panel-section]::-webkit-scrollbar-thumb,
            [data-molsysviewer-group-strip]::-webkit-scrollbar-thumb,
            [data-molsysviewer-group-strip-row]::-webkit-scrollbar-thumb {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
            }
            [data-molsysviewer-group-panel-body]::-webkit-scrollbar-thumb:hover,
            [data-molsysviewer-group-panel-section]::-webkit-scrollbar-thumb:hover,
            [data-molsysviewer-group-strip]::-webkit-scrollbar-thumb:hover,
            [data-molsysviewer-group-strip-row]::-webkit-scrollbar-thumb:hover {
                background: rgba(255, 255, 255, 0.35);
            }
            @keyframes molsysviewer-fade-in-up {
                from {
                    opacity: 0;
                    transform: translate(-50%, -46%);
                }
                to {
                    opacity: 1;
                    transform: translate(-50%, -50%);
                }
            }
        `;
        document.head.appendChild(style);
    }

    private updateWelcomeState(): void {
        const hasStructure = !!this.currentStructure || !!this.loadedStructure;
        if (hasStructure) {
            this.hideWelcomeCard();
        } else {
            this.showWelcomeCard();
        }
    }

    private showWelcomeCard(): void {
        if (this.welcomeCard) return;

        const card = document.createElement("div");
        card.setAttribute("data-molsysviewer-welcome-card", "true");
        
        Object.assign(card.style, {
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "360px",
            background: "rgba(20, 20, 25, 0.75)",
            backdropFilter: "blur(16px)",
            webkitBackdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "16px",
            padding: "24px",
            color: "#f4f4f5",
            fontFamily: "'Outfit', 'Inter', system-ui, -apple-system, sans-serif",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1)",
            zIndex: "100",
            animation: "molsysviewer-fade-in-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
            pointerEvents: "auto",
        });

        const titleEl = document.createElement("div");
        Object.assign(titleEl.style, {
            fontSize: "18px",
            fontWeight: "700",
            background: "linear-gradient(135deg, #a78bfa 0%, #22d3ee 100%)",
            webkitBackgroundClip: "text",
            webkitTextFillColor: "transparent",
            letterSpacing: "-0.02em",
            textAlign: "center",
        });
        titleEl.textContent = "Welcome to MolSysViewer";
        card.appendChild(titleEl);

        const descEl = document.createElement("div");
        Object.assign(descEl.style, {
            fontSize: "12px",
            lineHeight: "1.5",
            color: "rgba(244, 244, 245, 0.7)",
            textAlign: "center",
            marginBottom: "8px",
        });
        descEl.textContent = "An interactive, high-performance molecular visualization workbench integrated directly into your notebook.";
        card.appendChild(descEl);

        const codeBox = document.createElement("div");
        Object.assign(codeBox.style, {
            background: "rgba(0, 0, 0, 0.25)",
            border: "1px solid rgba(255, 255, 255, 0.05)",
            borderRadius: "8px",
            padding: "12px",
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#38bdf8",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
        });

        const guideTitle = document.createElement("span");
        Object.assign(guideTitle.style, {
            color: "rgba(244, 244, 245, 0.4)",
            fontWeight: "600",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            marginBottom: "4px",
            fontSize: "9px",
        });
        guideTitle.textContent = "Jupyter Quick Start";
        codeBox.appendChild(guideTitle);

        const line1 = document.createElement("span");
        line1.textContent = "import molsysviewer as msv";
        codeBox.appendChild(line1);

        const line2 = document.createElement("span");
        line2.textContent = "view = msv.new_view('1CRN')";
        line2.style.color = "#a78bfa";
        codeBox.appendChild(line2);

        const line3 = document.createElement("span");
        line3.textContent = "view.show()";
        codeBox.appendChild(line3);

        card.appendChild(codeBox);

        const btn = document.createElement("button");
        Object.assign(btn.style, {
            background: "linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%)",
            color: "#ffffff",
            border: "none",
            borderRadius: "8px",
            padding: "10px 16px",
            fontSize: "13px",
            fontWeight: "600",
            cursor: "pointer",
            transition: "transform 0.2s ease, opacity 0.2s ease, box-shadow 0.2s ease",
            textAlign: "center",
            marginTop: "4px",
            boxShadow: "0 4px 12px rgba(139, 92, 246, 0.3)",
        });
        btn.textContent = "Load Trial Structure (1CRN)";

        btn.onmouseover = () => {
            btn.style.transform = "scale(1.02)";
            btn.style.boxShadow = "0 6px 16px rgba(139, 92, 246, 0.4)";
        };
        btn.onmouseout = () => {
            btn.style.transform = "none";
            btn.style.boxShadow = "0 4px 12px rgba(139, 92, 246, 0.3)";
        };
        btn.onclick = () => {
            btn.style.opacity = "0.7";
            btn.textContent = "Loading Crambin...";
            void this.handleMessage({ op: "load_pdb_id", pdb_id: "1CRN" });
        };
        card.appendChild(btn);

        if (!this.host.style.position || this.host.style.position === "static") {
            this.host.style.position = "relative";
        }
        this.host.appendChild(card);
        this.welcomeCard = card;
    }

    private hideWelcomeCard(): void {
        if (this.welcomeCard) {
            this.welcomeCard.remove();
            this.welcomeCard = null;
        }
    }

    private selectWorkspace(workspaceId: string): void {
        const prevWorkspace = this.currentWorkspace;
        const available = new Set(this.getWorkspaceOptions().map((item) => item.id));
        this.currentWorkspace = available.has(workspaceId) ? workspaceId : "core";

        // Unmount widget panel from the previous workspace if navigating away
        if (prevWorkspace !== this.currentWorkspace && prevWorkspace !== "core") {
            const prevPanelId = this.currentWorkspacePanelByWorkspace.get(prevWorkspace);
            if (prevPanelId) {
                const prevPanel = this.getWorkspacePanels(prevWorkspace).find((item) => item.id === prevPanelId);
                if (prevPanel?.widget_class) {
                    this.notify?.({ event: "panel_unmount", addon: prevPanel.addon, panel: prevPanelId });
                    this.cleanupActivePanelWidget();
                }
            }
        }

        if (this.currentWorkspace !== prevWorkspace) {
            if (this.currentWorkspace !== "core") {
                const title = this.getWorkspaceOptions().find((item) => item.id === this.currentWorkspace)?.title ?? this.currentWorkspace;
                this.showToast(`Switching to workspace: ${title}`);
            } else if (prevWorkspace !== "core") {
                this.showToast("Returning to default workspace");
            }
        }

        this.refreshPanelWorkspaceChrome();
        if (this.currentWorkspace !== "core") {
            // If the active panel of the new workspace has a widget_class, request mount
            const selectedPanelId = this.ensureWorkspacePanelSelection(this.currentWorkspace);
            if (selectedPanelId) {
                const selectedPanel = this.getWorkspacePanels(this.currentWorkspace).find((item) => item.id === selectedPanelId);
                const newKey = `${this.currentWorkspace}:${selectedPanelId}`;
                if (selectedPanel?.widget_class && this.activePanelWidgetKey !== newKey) {
                    this.notify?.({ event: "panel_navigate", addon: selectedPanel.addon, panel: selectedPanelId });
                }
            }
            this.setPanelMode("workbench", true);
            this.emitPanelModeState();
            return;
        }
        this.setPanelMode(this.lastCorePanelMode, true);
        this.refreshNavigatePanel();
        this.refreshWorkbenchPanel();
        this.emitPanelModeState();
    }

    private emitPanelModeState(): void {
        const navigateExpanded = this.groupPanel.isVisible() && this.groupPanel.isExpanded();
        const workbenchExpanded = this.workbenchPanel.isVisible() && this.workbenchPanel.isExpanded();
        const expanded = navigateExpanded || workbenchExpanded;
        const panel = navigateExpanded
            ? "navigate"
            : workbenchExpanded
                ? "workbench"
                : null;
        const workspacePanel =
            this.currentWorkspace === "core"
                ? panel
                : this.ensureWorkspacePanelSelection(this.currentWorkspace);
        this.notify?.({
            event: "panel_mode_state",
            panel,
            expanded,
            workspace: this.currentWorkspace,
            workspace_panel: workspacePanel ?? null,
        });
    }

    // Facades for external access (e.g. from Index or Popout)
    
    async resetView() { await this.scene.resetView(); }
    async toggleFullscreen() { await this.scene.toggleFullscreen(true); } // default true for direct call
    async toggleBackground(mode?: "light" | "dark") { await this.scene.toggleBackground(mode); } // Pass mode directly (undefined triggers toggle)
    // Actually, direct calls from UI buttons might not pass msg. Scene handler handles boolean or msg.
    async toggleSpin(enable?: boolean) { await this.scene.toggleSpin(enable ?? !this.scene.isSpinActive); }
    async toggleSwing(enable?: boolean) { await this.scene.toggleSwing(enable ?? !this.scene.isSwingActive); }
    
    stepTrajectory(by: number) { return this.trajectory.stepTrajectory(by); }
    playTrajectory(opts: any) { return this.trajectory.playTrajectory(opts); }
    stopTrajectoryPlayback() { return this.trajectory.stopTrajectoryPlayback(); }
    setTrajectoryFrame(index: number) { return this.trajectory.setTrajectoryFrame(index); }
    
    onTrajectoryState(cb: (state: TrajectoryState) => void, opts?: { immediate?: boolean }) { 
        return this.trajectory.onTrajectoryState(cb, opts); 
    }
    
    getCameraSnapshot(): Camera.Snapshot | undefined {
        return this.plugin.canvas3d?.camera.getSnapshot?.();
    }

    async getImageDataUri(options?: {
        width?: number;
        height?: number;
        scale?: number;
        transparent?: boolean;
        preset?: string;
        cameraSnapshot?: Camera.Snapshot;
    }): Promise<string | undefined> {
        const helper = this.plugin.helpers.viewportScreenshot;
        if (!helper) return void 0;

        const width = Number(options?.width);
        const height = Number(options?.height);
        const scale = Number(options?.scale);
        const validScale = Number.isFinite(scale) && scale > 0 ? scale : 1;
        const useCustomResolution = Number.isFinite(width) && width > 0 && Number.isFinite(height) && height > 0;
        const viewportWidth = this.plugin.canvas3d?.webgl.gl.drawingBufferWidth ?? 0;
        const viewportHeight = this.plugin.canvas3d?.webgl.gl.drawingBufferHeight ?? 0;
        const targetWidth = useCustomResolution ? width : viewportWidth;
        const targetHeight = useCustomResolution ? height : viewportHeight;
        const scaledWidth = Math.max(1, Math.round(targetWidth * validScale));
        const scaledHeight = Math.max(1, Math.round(targetHeight * validScale));
        const currentSnapshot = options?.cameraSnapshot ? this.getCameraSnapshot() : void 0;
        const preset = typeof options?.preset === "string" ? options.preset : "current";
        const targetBackgroundMode =
            !options?.transparent && preset === "publication-light"
                ? "light"
                : !options?.transparent && preset === "publication-dark"
                    ? "dark"
                    : void 0;
        const shouldRestoreBackground = targetBackgroundMode
            ? (targetBackgroundMode === "dark" && !this.scene.isDarkMode)
                || (targetBackgroundMode === "light" && this.scene.isDarkMode)
            : false;

        try {
            if (targetBackgroundMode && shouldRestoreBackground) {
                await this.scene.toggleBackground(targetBackgroundMode);
            }
            if (options?.cameraSnapshot) {
                await this.setCameraSnapshot(options.cameraSnapshot, 0);
            }
            helper.behaviors.values.next({
                ...helper.values,
                transparent: !!options?.transparent,
                format: { name: "png", params: {} },
                resolution: { name: "custom", params: { width: scaledWidth, height: scaledHeight } },
            });
            return await helper.getImageDataUri();
        } finally {
            if (options?.cameraSnapshot && currentSnapshot) {
                await this.setCameraSnapshot(currentSnapshot, 0);
            }
            if (targetBackgroundMode && shouldRestoreBackground) {
                await this.scene.toggleBackground(this.scene.isDarkMode ? "light" : "dark");
            }
        }
    }

    async setCameraSnapshot(snapshot?: Camera.Snapshot, durationMs?: number) {
        if (!snapshot) return;
        try {
            await PluginCommands.Camera.SetSnapshot(this.plugin, {
                snapshot,
                durationMs: Math.max(0, Number(durationMs ?? 0)),
            });
        } catch (err) {
            console.warn("[MolSysViewer] setCameraSnapshot failed", err);
        }
    }

    private notifyTrajectoryState() {
        // Just a bridge if needed, but handlers can notify directly via callbacks or listeners
        // TrajectoryHandler handles its own listeners
    }

    private syncStripOverlaysForMessage(msg: ViewerMessage) {
        switch ((msg as any).op) {
            case "add_label":
                this.groupPanel.addLabelOverlay(msg as any);
                break;
            case "clear_scene":
                if ((msg as any).options?.labels) this.groupPanel.clearAnnotationOverlays();
                break;
            case "delete_layer":
                this.groupPanel.clearAnnotationOverlaysByTag((msg as any).tag);
                break;
            case "set_layer_tag":
                if (typeof (msg as any).tag === "string" && typeof (msg as any).new_tag === "string") {
                    this.groupPanel.retagAnnotationOverlays((msg as any).tag, (msg as any).new_tag);
                }
                break;
            case "clear_all":
                this.groupPanel.clearAnnotationOverlays();
                break;
        }
    }
}
