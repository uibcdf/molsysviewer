import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";
import { PluginBehaviors } from "molstar/lib/mol-plugin/behavior";
import { StateObjectRef } from "molstar/lib/mol-state";
import { Structure, StructureElement } from "molstar/lib/mol-model/structure";
import { Shape, ShapeGroup } from "molstar/lib/mol-model/shape";
import { Loci } from "molstar/lib/mol-model/loci";
import { StructureComponentRef } from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";
import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
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
import { LastMeasurementSummary, ViewerContextMenu } from "../ui/context-menu";
import { MeasurementToolAction, MeasurementToolController } from "./measurement-tools";
import { ToolStatusOverlay } from "../ui/tool-status";
import { ActiveSelectionController, ActiveSelectionItem, lociToGroupItems } from "./active-selection";
import type { ActiveSelectionPayload } from "./active-selection";
import { GroupStrip } from "../ui/group-strip";

type InteractionKind = "hover" | "click" | "context";

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
    }
    | { event: "interaction_hover" | "interaction_click"; kind: "shape"; atom_indices: number[]; tag?: string; shape_name?: string };

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
    }
    | { event: "interaction_context_menu"; kind: "shape"; atom_indices: number[]; tag?: string; shape_name?: string; page_x?: number; page_y?: number }
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
    return {
        atom_indices: atomIndices,
        tag: typeof sourceData.tag === "string" ? sourceData.tag : undefined,
        shape_name: shape.name,
    };
}

function normalizeContextPayloadFromLoci(loci: any, page_x?: number, page_y?: number): ContextInteractionPayload {
    const groupItems = lociToGroupItems(loci);
    const atomIndices = lociToAtomIndices(loci);
    if (groupItems.length === 0) {
        if (atomIndices.length > 0) {
            return { event: "interaction_context_menu", kind: "structure", atom_indices: atomIndices, page_x, page_y };
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
    };
}

export function normalizeInteractionEvent(kind: InteractionKind, ev: any): InteractionPayload {
    if (kind === "context") {
        throw new Error("Use normalizeContextInteractionEvent for context interactions");
    }
    const event = kind === "hover" ? "interaction_hover" : "interaction_click";
    const groupItems = lociToGroupItems(ev?.current?.loci);
    const atomIndices = lociToAtomIndices(ev?.current?.loci);
    if (groupItems.length === 0) {
        if (atomIndices.length > 0) {
            return { event, kind: "structure", atom_indices: atomIndices };
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

export function registerInteractionObservers(
    plugin: any,
    notify?: (msg: any) => void,
    openContextMenu?: (payload: ContextInteractionPayload) => void,
    onPrimaryClick?: (ev: any) => void,
    onSecondaryClick?: (ev: any) => void,
    onHover?: (ev: any) => void,
): void {
    const hover = plugin?.behaviors?.interaction?.hover;
    const click = plugin?.behaviors?.interaction?.click;
    if (typeof hover?.subscribe === "function") {
        hover.subscribe((ev: any) => {
            onHover?.(ev);
            notify?.(normalizeInteractionEvent("hover", ev));
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
            notify?.(normalizeInteractionEvent("click", ev));
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
    private readonly groupStrip: GroupStrip;
    private readonly releaseContextMenuSuppression?: () => void;
    private readonly releaseGlobalEscapeHandler?: () => void;
    private lastContextLoci: any = null;
    private lastHoverLoci: any = null;
    private lastHoverPayload: InteractionPayload | null = null;
    private lastPrimaryGroupClick: { key: string; time: number } | null = null;
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

    static async create(target: HTMLElement, notify?: (msg: any) => void, existingCanvas?: HTMLCanvasElement): Promise<MolSysViewerController> {
        const canvas = existingCanvas ?? document.createElement("canvas");
        if (!existingCanvas) {
            canvas.style.width = "100%";
            canvas.style.height = "100%";
            canvas.style.display = "block";
            target.appendChild(canvas);
        } else if (existingCanvas.parentElement !== target) {
            target.appendChild(existingCanvas);
        }

        const plugin = new PluginContext(createMolSysViewerPluginSpec());
        await plugin.init();

        const init = (plugin as any).initViewerAsync ?? (plugin as any).initViewer;
        let ok = false;
        if (typeof init === "function") {
            const result = init.call(plugin, canvas, target);
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

        return new MolSysViewerController(plugin, target, notify);
    }

    public readonly loader: LoaderHandlers;
    public readonly annotations: AnnotationHandlers;
    public readonly measurements: MeasurementHandlers;
    public readonly shapes: ShapeHandlers;
    public readonly scene: SceneHandlers;
    public readonly state: StateHandlers;
    public readonly trajectory: TrajectoryHandlers;

    private currentStructure?: StateObjectRef; // Ref to structure root
    private loadedStructure?: LoadedStructure; // Loaded structure bundle
    private currentActiveSelection: ActiveSelectionPayload | null = null;
    private lastMeasurementSummary: LastMeasurementSummary | null = null;

    // Getters for scene state delegated to scene handler
    get isSpinActive() { return this.scene.isSpinActive; }
    get isSwingActive() { return this.scene.isSwingActive; }
    get isDarkMode() { return this.scene.isDarkMode; }

    private constructor(public readonly plugin: PluginContext, private readonly host: HTMLElement, private readonly notify?: (msg: any) => void) {
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
                this.groupStrip.updateSelection(msg);
                this.syncVisualSelection(msg);
            } else if (msg?.event === "interaction_measurement_created") {
                this.lastMeasurementSummary = {
                    action: msg.action,
                    picked_count: msg.picked_count,
                };
            }
            this.notify?.(msg);
        };

        this.toolStatusOverlay = new ToolStatusOverlay(host);
        this.measurementTools = new MeasurementToolController(plugin, emitInteractionEvent);
        this.activeSelection = new ActiveSelectionController(emitInteractionEvent);
        this.groupStrip = new GroupStrip(host, (items, additive) => {
            this.activeSelection.setItems(items, additive);
        }, (item) => {
            const loci = this.groupStrip.focusItem(item);
            if (loci) this.plugin.managers.camera.focusLoci(loci);
        }, (item) => {
            if (!item) {
                this.plugin.managers.interactivity.lociHighlights.clearHighlights();
                emitInteractionEvent({ event: "interaction_hover", kind: "empty" });
                return;
            }
            const loci = this.groupStrip.focusItem(item);
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
        });
        this.contextMenu = new ViewerContextMenu(host, emitInteractionEvent, (action, target) => {
            if (action === "focus_target") {
                this.focusTarget(target);
                return;
            }
            if (action === "focus_selection") {
                this.focusCurrentSelection();
                return;
            }
            if (action === "clear_selection") {
                this.activeSelection.clear();
                return;
            }
            if (
                action === "create_region_from_selection"
                || action === "add_label_from_selection"
                || action === "persist_last_measurement"
            ) {
                return;
            }
            this.startMeasurementTool(action);
        });
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
            const page_x = typeof page?.[0] === "number" ? page[0] : undefined;
            const page_y = typeof page?.[1] === "number" ? page[1] : undefined;
            let payload = normalizeContextInteractionEvent(ev, this.lastHoverLoci);
            if (typeof page_x === "number" && typeof page_y === "number") {
                const pickData = this.plugin.canvas3d?.identify?.([page_x, page_y] as any);
                const pickedLoci = pickData ? this.plugin.canvas3d?.getLoci?.(pickData.id)?.loci : null;
                if (pickedLoci) {
                    payload = normalizeContextPayloadFromLoci(pickedLoci, page_x, page_y);
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
                }
            }
            const pageX = payload.page_x ?? 0;
            const pageY = payload.page_y ?? 0;
            emitInteractionEvent(payload);
            this.contextMenu.open(payload, pageX, pageY, this.currentActiveSelection, this.lastMeasurementSummary);
        }, (ev) => {
            this.lastHoverLoci = ev?.current?.loci ?? null;
            this.lastHoverPayload = normalizeInteractionEvent("hover", ev);
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

        this.shapes = new ShapeHandlers(plugin, (ref, tag) => this.state.registerShapeRef(ref, tag));
        this.annotations = new AnnotationHandlers(plugin, {
            getStructure: () => this.getStructureData(),
            registerRef: (ref, tag) => this.state.registerTaggedRef(ref, tag, "annotation"),
        });
        this.measurements = new MeasurementHandlers(plugin, {
            getStructure: () => this.getStructureData(),
            registerRef: (ref, tag) => this.state.registerTaggedRef(ref, tag, "measurement"),
        });

        this.scene = new SceneHandlers(plugin, host, {
            clearShapes: () => this.state.clearShapesByTag(), // clear all shapes
            clearLabels: async () => this.annotations.clearLabels(),
            getComponents: () => this.getComponents(),
            clearShapesByTag: (tag) => this.state.clearShapesByTag(tag),
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
            notifyTrajectoryState: () => this.notifyTrajectoryState()
        });
    }

    dispose(): void {
        this.measurementTools.dispose();
        this.toolStatusOverlay.dispose();
        this.groupStrip.dispose();
        this.contextMenu.dispose();
        this.releaseContextMenuSuppression?.();
        this.releaseGlobalEscapeHandler?.();
        this.plugin.dispose();
    }

    private startMeasurementTool(action: MeasurementToolAction): void {
        if (!this.lastContextLoci) return;
        this.measurementTools.start(action, this.lastContextLoci);
    }

    private installGlobalEscapeHandler(): () => void {
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key !== "Escape") return;
            if (this.measurementTools.isActive()) return;
            if (this.currentActiveSelection?.source_kind !== "empty") {
                event.preventDefault();
                event.stopPropagation();
                this.activeSelection.clear();
                this.contextMenu.close();
            }
        };
        window.addEventListener("keydown", onKeyDown, true);
        return () => window.removeEventListener("keydown", onKeyDown, true);
    }

    private openContextMenuForItem(
        item: ActiveSelectionItem,
        pageX: number,
        pageY: number,
        emitInteractionEvent: (msg: any) => void,
    ): void {
        const loci = this.groupStrip.focusItem(item);
        if (!loci) return;
        this.lastContextLoci = loci;
        const payload = {
            event: "interaction_context_menu" as const,
            kind: "structure" as const,
            atom_indices: item.atom_indices,
            page_x: pageX,
            page_y: pageY,
        };
        emitInteractionEvent(payload);
        this.contextMenu.open(payload, pageX, pageY, this.currentActiveSelection, this.lastMeasurementSummary);
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
        emitInteractionEvent(payload);
        this.contextMenu.open(payload, pageX, pageY, this.currentActiveSelection, this.lastMeasurementSummary);
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
        const unit = structure.units.find((candidate) => candidate.kind === 0);
        if (!unit) return null;
        const unitIndices: number[] = [];
        for (const atomIndex of atomIndices) {
            const unitIndex = unit.elements.indexOf(atomIndex as any);
            if (unitIndex >= 0) unitIndices.push(unitIndex);
        }
        if (unitIndices.length === 0) return null;
        return StructureElement.Loci(structure, [{ unit, indices: unitIndices } as any]);
    }

    private syncVisualSelection(selection: ActiveSelectionPayload): void {
        this.plugin.managers.interactivity.lociSelects.deselectAll();
        if (!selection || selection.source_kind === "empty" || selection.items.length === 0) return;
        const orderedItems = [...selection.items].sort((a, b) => {
            const left = a.group_indices[0] ?? a.atom_indices[0] ?? Number.MAX_SAFE_INTEGER;
            const right = b.group_indices[0] ?? b.atom_indices[0] ?? Number.MAX_SAFE_INTEGER;
            return left - right;
        });
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
                case "add_alpha_sphere_set": await this.shapes.addAlphaSphereSet(msg); break;
                case "add_pocket_surface": await this.shapes.addPocketSurface(msg); break;
                case "add_pocket_blob": await this.shapes.addPocketBlob(msg); break;
                case "add_channel_tube": await this.shapes.addChannelTube(msg); break;
                case "add_anisotropy_ellipsoids": await this.shapes.addAnisotropyEllipsoids(msg); break;
                case "add_pharmacophore_features": await this.shapes.addPharmacophore(msg); break;
                case "add_network_links": await this.shapes.addNetworkLinks(msg); break;
                case "add_displacement_vectors": await this.shapes.addDisplacementVectors(msg); break;
                case "add_tetrahedra": await this.shapes.addTetrahedra(msg); break;
                case "add_triangle_faces": await this.shapes.addTriangleFaces(msg); break;
                case "add_label": await this.annotations.addLabel(msg); break;
                case "update_label": await this.annotations.updateLabel(msg); break;
                case "add_distance_measurement": await this.measurements.addDistance(msg); break;
                case "add_angle_measurement": await this.measurements.addAngle(msg); break;
                case "add_dihedral_measurement": await this.measurements.addDihedral(msg); break;

                // Scene Ops
                case "reset_view":
                case "reset_camera": await this.scene.resetView(); break;
                case "toggle_fullscreen": await this.scene.toggleFullscreen(msg); break;
                case "toggle_background": await this.scene.toggleBackground(msg); break;
                case "toggle_swing": await this.scene.toggleSwing(msg); break;
                case "toggle_spin": await this.scene.toggleSpin(msg); break;
                case "clear_scene": await this.scene.clearScene(msg); break;
                case "clear_all": await this.scene.clearAll(); break;
                case "clear_shapes_by_tag": await this.scene.clearShapesByTag(msg); break;

                // State/Region Ops
                case "update_visibility": await this.state.updateVisibility(msg); break;
                case "create_region": await this.state.createRegion(msg); break;
                case "set_region_representation": await this.state.setRegionRepresentation(msg); break;
                case "show_region": await this.state.showRegion(msg); break;
                case "hide_region": await this.state.hideRegion(msg); break;
                case "delete_region": await this.state.deleteRegion(msg); break;
                case "create_layer": await this.state.createLayer(msg); break;
                case "show_layer": await this.state.showLayer(msg); break;
                case "hide_layer": await this.state.hideLayer(msg); break;
                case "delete_layer": await this.state.deleteLayer(msg); break;
                case "set_layer_tag": await this.state.setLayerTag(msg); break;
                case "set_global_representation": await this.state.setGlobalRepresentation(msg); break;
                case "show_global": await this.state.showGlobal(msg); break;
                case "hide_global": await this.state.hideGlobal(msg); break;
                case "zoom": await this.state.zoom(msg); break;
                case "set_camera_snapshot": await this.setCameraSnapshot((msg as any).snapshot, (msg as any).duration_ms); break;
                case "clear_active_selection":
                    this.activeSelection.clear();
                    break;

                // Trajectory Ops
                case "step_trajectory": await this.trajectory.stepTrajectory(msg); break;
                case "set_trajectory_frame": await this.trajectory.setTrajectoryFrame(msg); break;
                case "set_trajectory_playback": await this.trajectory.setTrajectoryPlayback(msg); break;

                default:
                    console.warn("[MolSysViewer] unknown op:", (msg as any).op, msg);
                    break;
            }
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
            this.currentStructure = last.cell.transform.ref as any;
            this.groupStrip.setStructure(last.cell.obj?.data);
            // Notify state handler that structure is ready so it can apply pending ops
            this.state.onStructureLoaded();
            this.trajectory.notifyListeners();
        } else {
            this.currentStructure = undefined;
            this.groupStrip.setStructure(undefined);
        }
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
        this.groupStrip.setStructure(undefined);
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
                this.groupStrip.addLabelOverlay(msg as any);
                break;
            case "clear_scene":
                if ((msg as any).options?.labels) this.groupStrip.clearAnnotationOverlays();
                break;
            case "delete_layer":
                this.groupStrip.clearAnnotationOverlaysByTag((msg as any).tag);
                break;
            case "set_layer_tag":
                if (typeof (msg as any).tag === "string" && typeof (msg as any).new_tag === "string") {
                    this.groupStrip.retagAnnotationOverlays((msg as any).tag, (msg as any).new_tag);
                }
                break;
            case "clear_all":
                this.groupStrip.clearAnnotationOverlays();
                break;
        }
    }
}
