import { PluginContext } from "molstar/lib/mol-plugin/context";
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";
import { StateObjectRef } from "molstar/lib/mol-state";
import { Structure } from "molstar/lib/mol-model/structure";
import { StructureComponentRef } from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";
import { Camera } from "molstar/lib/mol-canvas3d/camera";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";

import { ViewerMessage } from "../messages/viewer-messages";
import { LoadedStructure } from "../plugin/structure";
import { LoaderHandlers } from "./handlers/loader-handlers";
import { ShapeHandlers } from "./handlers/shape-handlers";
import { SceneHandlers } from "./handlers/scene-handlers";
import { StateHandlers } from "./handlers/state-handlers";
import { TrajectoryHandlers, TrajectoryState } from "./handlers/trajectory-handlers";

/**
 * Controller that translates Python messages into Mol* actions and manages state refs.
 * Refactored to use specialized handlers for better maintainability.
 */
export class MolSysViewerController {
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
        if (!ok) console.error("[MolSysViewer] Failed to init Mol* viewer");

        return new MolSysViewerController(plugin, target, notify);
    }

    public readonly loader: LoaderHandlers;
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
        // Initialize handlers with necessary context callbacks
        
        this.state = new StateHandlers(plugin, {
            getStructure: () => this.getStructureData(),
            getLoadedStructure: () => this.loadedStructure,
            getCurrentStructureRef: () => this.currentStructure,
            getComponents: () => this.getComponents(),
            notify: (msg) => this.notify?.(msg)
        });

        this.shapes = new ShapeHandlers(plugin, (ref, tag) => this.state.registerShapeRef(ref, tag));

        this.scene = new SceneHandlers(plugin, host, {
            clearShapes: () => this.state.clearShapesByTag(), // clear all shapes
            clearLabels: async () => { /* labels not fully implemented in handlers yet */ },
            getComponents: () => this.getComponents(),
            clearShapesByTag: (tag) => this.state.clearShapesByTag(tag),
            removeLoadedStructure: () => this.removeLoadedStructure(),
            notify: (msg) => this.notify?.(msg)
        });

        this.loader = new LoaderHandlers(plugin, {
            clearGlobalRepresentations: async () => { /* handled by state via events usually, but direct call needed? state handles globals */ },
            captureCurrentStructure: () => this.captureCurrentStructure(),
            setLoadedStructure: (ls) => { this.loadedStructure = ls; },
            getLoadedStructure: () => this.loadedStructure
        });

        this.trajectory = new TrajectoryHandlers(plugin, {
            getLoadedStructure: () => this.loadedStructure,
            notifyTrajectoryState: () => this.notifyTrajectoryState()
        });
    }

    // Message Dispatcher
    async handleMessage(msg: ViewerMessage) {
        if (!msg || typeof msg !== "object") return;
        if (!("op" in msg)) {
            console.warn("[MolSysViewer] message missing 'op'", msg);
            return;
        }

        try {
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
            // Notify state handler that structure is ready so it can apply pending ops
            this.state.onStructureLoaded();
            this.trajectory.notifyListeners();
        } else {
            this.currentStructure = undefined;
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
    
    onTrajectoryState(cb: (state: TrajectoryState) => void) { return this.trajectory.onTrajectoryState(cb); }
    
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
}
