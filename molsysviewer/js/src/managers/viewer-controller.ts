import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";
import { StateObjectRef } from "molstar/lib/mol-state";
import { Structure, StructureElement } from "molstar/lib/mol-model/structure";
import { StructureComponentRef } from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";
import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { OrderedSet } from "molstar/lib/mol-data/int/ordered-set";
import { ButtonsType } from "molstar/lib/mol-util/input/input-observer";

import { ViewerMessage } from "../messages/viewer-messages";
import { LoadedStructure } from "../plugin/structure";
import { LoaderHandlers } from "./handlers/loader-handlers";
import { AnnotationHandlers } from "./handlers/annotation-handlers";
import { ShapeHandlers } from "./handlers/shape-handlers";
import { SceneHandlers } from "./handlers/scene-handlers";
import { StateHandlers } from "./handlers/state-handlers";
import { TrajectoryHandlers, TrajectoryState } from "./handlers/trajectory-handlers";
import { ViewerContextMenu } from "../ui/context-menu";
import { MeasurementToolAction, MeasurementToolController } from "./measurement-tools";
import { ToolStatusOverlay } from "../ui/tool-status";
import { ActiveSelectionController, ActiveSelectionItem } from "./active-selection";
import { GroupStrip } from "../ui/group-strip";

type InteractionKind = "hover" | "click" | "context";

type InteractionPayload =
    | { event: "interaction_hover" | "interaction_click"; kind: "empty" }
    | { event: "interaction_hover" | "interaction_click"; kind: "structure"; atom_indices: number[] };

type ContextInteractionPayload =
    | { event: "interaction_context_menu"; kind: "empty"; page_x?: number; page_y?: number }
    | { event: "interaction_context_menu"; kind: "structure"; atom_indices: number[]; page_x?: number; page_y?: number };

function lociToAtomIndices(loci: any): number[] {
    if (!StructureElement.Loci.is(loci)) return [];
    const atomIndices: number[] = [];
    const seen = new Set<number>();
    for (const element of loci.elements) {
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

export function normalizeInteractionEvent(kind: InteractionKind, ev: any): InteractionPayload {
    if (kind === "context") {
        throw new Error("Use normalizeContextInteractionEvent for context interactions");
    }
    const event = kind === "hover" ? "interaction_hover" : "interaction_click";
    const atomIndices = lociToAtomIndices(ev?.current?.loci);
    if (atomIndices.length === 0) {
        return { event, kind: "empty" };
    }
    return { event, kind: "structure", atom_indices: atomIndices };
}

export function normalizeContextInteractionEvent(ev: any): ContextInteractionPayload {
    const atomIndices = lociToAtomIndices(ev?.current?.loci);
    const page = ev?.page;
    const page_x = typeof page?.[0] === "number" ? page[0] : undefined;
    const page_y = typeof page?.[1] === "number" ? page[1] : undefined;
    if (atomIndices.length === 0) {
        return { event: "interaction_context_menu", kind: "empty", page_x, page_y };
    }
    return { event: "interaction_context_menu", kind: "structure", atom_indices: atomIndices, page_x, page_y };
}

function isSecondaryButton(ev: any): boolean {
    return ev?.button === ButtonsType.Flag.Secondary;
}

export function suppressCanvasContextMenu(canvas: Pick<HTMLElement, "addEventListener">): () => void {
    const onContextMenu = (event: Event) => {
        event.preventDefault();
        event.stopPropagation();
    };
    canvas.addEventListener("contextmenu", onContextMenu);
    return () => {
        (canvas as HTMLElement).removeEventListener?.("contextmenu", onContextMenu);
    };
}

export function registerInteractionObservers(
    plugin: any,
    notify?: (msg: any) => void,
    openContextMenu?: (payload: ContextInteractionPayload) => void,
    onPrimaryClick?: (ev: any) => void,
    onSecondaryClick?: (ev: any) => void,
): void {
    const hover = plugin?.behaviors?.interaction?.hover;
    const click = plugin?.behaviors?.interaction?.click;
    if (typeof hover?.subscribe === "function") {
        hover.subscribe((ev: any) => notify?.(normalizeInteractionEvent("hover", ev)));
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
    private lastContextLoci: any = null;
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

        const plugin = new PluginContext(DefaultPluginSpec());
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
    public readonly shapes: ShapeHandlers;
    public readonly scene: SceneHandlers;
    public readonly state: StateHandlers;
    public readonly trajectory: TrajectoryHandlers;

    private currentStructure?: StateObjectRef; // Ref to structure root
    private loadedStructure?: LoadedStructure; // Loaded structure bundle

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
                this.groupStrip.updateSelection(msg);
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
        });
        this.contextMenu = new ViewerContextMenu(host, emitInteractionEvent, (action, _target) => {
            this.startMeasurementTool(action);
        });
        const canvas = this.plugin.canvas3d?.props?.canvas ?? this.plugin.canvas3d?.getCanvas?.();
        if (canvas) {
            this.releaseContextMenuSuppression = suppressCanvasContextMenu(canvas as HTMLElement);
        }
        registerInteractionObservers(plugin, emitInteractionEvent, (payload) => {
            const pageX = payload.page_x ?? 0;
            const pageY = payload.page_y ?? 0;
            this.contextMenu.open(payload, pageX, pageY);
        }, (ev) => {
            if (!this.measurementTools.isActive()) {
                this.activeSelection.handlePrimaryClick(ev);
            }
            this.measurementTools.handlePrimaryClick(ev?.current?.loci);
        }, (ev) => {
            this.lastContextLoci = ev?.current?.loci ?? null;
        });

        // Initialize handlers with necessary context callbacks
        
        this.state = new StateHandlers(plugin, {
            getStructure: () => this.getStructureData(),
            getLoadedStructure: () => this.loadedStructure,
            getCurrentStructureRef: () => this.currentStructure,
            getComponents: () => this.getComponents(),
            notify: (msg) => this.notify?.(msg)
        });

        this.shapes = new ShapeHandlers(plugin, (ref, tag) => this.state.registerShapeRef(ref, tag));
        this.annotations = new AnnotationHandlers(plugin, {
            getStructure: () => this.getStructureData(),
            registerRef: (ref, tag) => this.state.registerTaggedRef(ref, tag, "annotation"),
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
        this.plugin.dispose();
    }

    private startMeasurementTool(action: MeasurementToolAction): void {
        if (!this.lastContextLoci) return;
        this.measurementTools.start(action, this.lastContextLoci);
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
        this.contextMenu.open(payload, pageX, pageY);
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
