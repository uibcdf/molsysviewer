import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef } from "molstar/lib/mol-state";
import { clearStructureTransparency } from "molstar/lib/mol-plugin-state/helpers/structure-transparency";
import { StructureComponentRef } from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";
import { Sphere3D } from "molstar/lib/mol-math/geometry/primitives/sphere3d";
import { Vec3 } from "molstar/lib/mol-math/linear-algebra/3d/vec3";
import { Vec4 } from "molstar/lib/mol-math/linear-algebra/3d/vec4";
import { Mat4 } from "molstar/lib/mol-math/linear-algebra/3d/mat4";
import { Clip } from "molstar/lib/mol-util/clip";
import { addTriangleFacesFromPython } from "../../shapes";
import { clearPerAtomColors } from "../../themes/per-atom-color";
import {
    ClearByTagMessage,
    ClearSceneMessage,
    SectionEntry,
    SetBackgroundColorMessage,
    SetClipPlanesMessage,
    SetFogMessage,
    SetLightingMessage,
    SetSectionDragMessage,
    SetSectionsMessage,
    ToggleBackgroundMessage,
    ToggleFullscreenMessage,
    ToggleSpinMessage,
    ToggleSwingMessage,
    ZoomToPositionMessage,
} from "../../messages/viewer-messages";

export interface SceneCallbacks {
    clearShapes: () => Promise<void>;
    clearLabels: () => Promise<void>;
    getComponents: () => StructureComponentRef[];
    clearShapesByTag: (tag?: string) => Promise<void>;
    registerShapeRef: (ref: StateObjectRef | undefined, tag: string) => void;
    removeLoadedStructure: () => Promise<void>;
    notify: (msg: any) => void;
}

export class SceneHandlers {
    private swingActive = false;
    private spinActive = false;
    private darkMode = false;
    private savedLightRenderer?: any;
    private savedDarkRenderer?: any;
    private savedLightCamera?: any;
    private savedDarkCamera?: any;

    // ── Section gizmo state ────────────────────────────────────────────────
    private _activeSections: SectionEntry[] = [];
    private _sectionGizmoTags = new Set<string>();
    private _sectionHandles = new Map<string, HTMLElement>();
    private _sectionRimHandles = new Map<string, HTMLElement>();
    private _dragDisabledTags = new Set<string>();
    private _cameraStateSub?: { unsubscribe: () => void };

    constructor(
        private plugin: PluginContext,
        private host: HTMLElement,
        private callbacks: SceneCallbacks
    ) {}

    get isSpinActive() { return this.spinActive; }
    get isSwingActive() { return this.swingActive; }
    get isDarkMode() { return this.darkMode; }

    async resetView() {
        await PluginCommands.Camera.Reset(this.plugin, { durationMs: 250 });
    }

    async toggleFullscreen(msg: ToggleFullscreenMessage | boolean) {
        const enable = typeof msg === 'boolean' ? msg : msg.enable;
        const canvas = this.plugin.canvas3dContext?.canvas;
        const target =
            this.host ??
            canvas?.parentElement ??
            canvas ??
            document.documentElement;
        if (!target || !(target as any).requestFullscreen) return;
        const shouldEnable = enable ?? !document.fullscreenElement;
        try {
            if (shouldEnable) {
                if (!document.fullscreenElement) await target.requestFullscreen();
            } else if (document.fullscreenElement) {
                await document.exitFullscreen();
            }
        } catch (err) {
            console.warn("[MolSysViewer] fullscreen toggle failed", err);
        }
    }

    async toggleBackground(msg?: ToggleBackgroundMessage | "light" | "dark") {
        const mode = typeof msg === 'string' ? msg : msg?.mode;
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;

        const renderer = canvas3d.props?.renderer ?? {};
        const camera = canvas3d.props?.camera ?? {};

        // Snapshot the initial light mode once.
        if (!this.savedLightRenderer) this.savedLightRenderer = { ...renderer };
        if (!this.savedLightCamera) this.savedLightCamera = { ...camera };

        const makeDark = mode ? mode === "dark" : !this.darkMode;

        if (makeDark) {
            if (!this.savedDarkRenderer) {
                this.savedDarkRenderer = {
                    ...renderer,
                    backgroundColor: 0x101010,
                    ambientColor: 0xffffff,
                    exposure: renderer.exposure ?? 1,
                    ambientIntensity: renderer.ambientIntensity ?? 1,
                    // Dark mode uses a white key light. Mol* models directional lights
                    // in renderer.light[]; recolor the primary light to white.
                    light: (Array.isArray(renderer.light) && renderer.light.length > 0
                        ? renderer.light
                        : [{ inclination: 150, azimuth: 320, color: 0xffffff, intensity: 1 }]
                    ).map((l, i) => (i === 0 ? { ...l, color: 0xffffff } : l)),
                };
            }
            if (!this.savedDarkCamera) {
                this.savedDarkCamera = { ...camera };
            }
            canvas3d.setProps({
                renderer: { ...this.savedDarkRenderer },
                camera: { ...this.savedDarkCamera },
            });
            this.darkMode = true;
        } else {
            const lightRenderer = this.savedLightRenderer ?? renderer;
            const lightCamera = this.savedLightCamera ?? camera;
            canvas3d.setProps({
                renderer: { ...lightRenderer },
                camera: { ...lightCamera },
            });
            this.darkMode = false;
        }
    }

    async toggleSwing(msg: ToggleSwingMessage | boolean) {
        const enable = typeof msg === 'boolean' ? msg : msg.enable;
        const speed = typeof msg === 'object' && msg.speed != null ? msg.speed : 0.25;
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const shouldEnable = enable ?? !this.swingActive;
        this.swingActive = shouldEnable;
        this.spinActive = false;
        canvas3d.setProps({
            trackball: {
                ...(canvas3d.props?.trackball || {}),
                animate: shouldEnable
                    ? { name: "rock", params: { speed, angle: 20 } }
                    : { name: "off", params: {} },
            },
        });
    }

    async toggleSpin(msg: ToggleSpinMessage | boolean) {
        const enable = typeof msg === 'boolean' ? msg : msg.enable;
        const speed = typeof msg === 'object' && msg.speed != null ? msg.speed : 0.1;
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const shouldEnable = enable ?? !this.spinActive;
        this.spinActive = shouldEnable;
        this.swingActive = false;
        canvas3d.setProps({
            trackball: {
                ...(canvas3d.props?.trackball || {}),
                animate: shouldEnable ? { name: "spin", params: { speed } } : { name: "off", params: {} },
            },
        });
    }

    // ── Section helpers ────────────────────────────────────────────────────

    /**
     * Convert a unit-normal vector to a {axis, angle(deg)} rotation that brings
     * the Mol* plane default normal [0,1,0] to the desired normal.
     */
    private _normalToAxisAngle(normal: [number, number, number]): { axis: Vec3; angle: number } {
        const DEFAULT = Vec3.create(0, 1, 0);
        const n = Vec3.normalize(Vec3(), Vec3.create(...normal));
        const dot = Vec3.dot(DEFAULT, n);

        // Already aligned
        if (dot > 0.9999) return { axis: Vec3.create(0, 0, 1), angle: 0 };
        // Anti-aligned — rotate 180° around any perpendicular axis
        if (dot < -0.9999) return { axis: Vec3.create(1, 0, 0), angle: 180 };

        const axis = Vec3.normalize(Vec3(), Vec3.cross(Vec3(), DEFAULT, n));
        const angle = (Math.acos(Math.max(-1, Math.min(1, dot))) * 180) / Math.PI;
        return { axis, angle };
    }

    async setSections(msg: SetSectionsMessage) {
        const sections = msg.sections ?? [];
        this._activeSections = sections.map(s => ({ ...s, point: [...s.point] as [number,number,number] }));

        await this._applyClipFromSections(sections);
        await this._updateSectionGizmos(sections);
        this._syncHandles(sections);
        this._ensureCameraSubscription();
        this._repositionHandles();
    }

    async syncSectionPosition(msg: { tag: string; point: [number, number, number]; normal?: [number, number, number] }) {
        const entry = this._activeSections.find(s => s.tag === msg.tag);
        if (!entry) return;
        entry.point = [...msg.point] as [number, number, number];
        if (msg.normal) entry.normal = [...msg.normal] as [number, number, number];
        await this._applyClipFromSections(this._activeSections);
        this._repositionHandles();
        await this._updateSectionGizmos(this._activeSections);
    }

    // Apply only the Mol* clip plane (fast path used during drag).
    private async _applyClipFromSections(sections: SectionEntry[]) {
        const NM_TO_ANGSTROM = 10.0;
        const visibleSections = sections.filter(section => !section.hidden);

        if (visibleSections.length === 0) {
            const currentOptions = this.plugin.managers.structure.component.state.options;
            await this.plugin.managers.structure.component.setOptions({
                ...currentOptions,
                clipObjects: { variant: "pixel" as Clip.Variant, objects: [] },
            });
            return;
        }

        const objects: Clip.Props["objects"] = visibleSections.map((s: SectionEntry) => {
            const { axis, angle } = this._normalToAxisAngle(s.normal);
            return {
                type: "plane" as const,
                invert: s.invert ?? false,
                position: Vec3.create(
                    s.point[0] * NM_TO_ANGSTROM,
                    s.point[1] * NM_TO_ANGSTROM,
                    s.point[2] * NM_TO_ANGSTROM
                ),
                rotation: { axis, angle },
                scale: Vec3.create(1, 1, 1),
                transform: Mat4.identity(),
            };
        });

        const currentOptions = this.plugin.managers.structure.component.state.options;
        await this.plugin.managers.structure.component.setOptions({
            ...currentOptions,
            clipObjects: { variant: "pixel" as Clip.Variant, objects },
        });
    }

    // ── Gizmo disc (3D triangle faces) ────────────────────────────────────

    private _buildDiscVertices(
        centerA: [number,number,number],
        normal: [number,number,number],
        radius: number,
        segments: number
    ): Array<[[number,number,number],[number,number,number],[number,number,number]]> {
        const n = Vec3.normalize(Vec3(), Vec3.create(...normal));
        const ref = Math.abs(n[0]) < 0.9 ? Vec3.create(1, 0, 0) : Vec3.create(0, 1, 0);
        const u = Vec3.normalize(Vec3(), Vec3.cross(Vec3(), ref, n));
        const v = Vec3.cross(Vec3(), n, u);
        const c = Vec3.create(...centerA);
        const tris: Array<[[number,number,number],[number,number,number],[number,number,number]]> = [];

        for (let i = 0; i < segments; i++) {
            const a0 = (2 * Math.PI * i) / segments;
            const a1 = (2 * Math.PI * (i + 1)) / segments;
            const cos0 = Math.cos(a0) * radius;
            const sin0 = Math.sin(a0) * radius;
            const cos1 = Math.cos(a1) * radius;
            const sin1 = Math.sin(a1) * radius;
            const p0: [number,number,number] = [
                c[0] + cos0 * u[0] + sin0 * v[0],
                c[1] + cos0 * u[1] + sin0 * v[1],
                c[2] + cos0 * u[2] + sin0 * v[2],
            ];
            const p1: [number,number,number] = [
                c[0] + cos1 * u[0] + sin1 * v[0],
                c[1] + cos1 * u[1] + sin1 * v[1],
                c[2] + cos1 * u[2] + sin1 * v[2],
            ];
            const cc: [number,number,number] = [c[0], c[1], c[2]];
            // Front and back faces for double-sided rendering
            tris.push([cc, p0, p1]);
            tris.push([cc, p1, p0]);
        }
        return tris;
    }

    private async _updateSectionGizmos(sections: SectionEntry[]) {
        const NM_TO_A = 10.0;
        // Clear previous gizmo shapes
        for (const tag of this._sectionGizmoTags) {
            await this.callbacks.clearShapesByTag(tag);
        }
        this._sectionGizmoTags.clear();

        const visibleSections = sections.filter(section => !section.hidden);
        if (visibleSections.length === 0) return;

        const camera = this.plugin.canvas3d?.camera;
        const discRadius = camera
            ? Math.max(15, camera.state.radius * 0.3)
            : 20;

        for (const section of visibleSections) {
            const gizmoTag = `__msv_sgizmo_${section.tag}`;
            const centerA: [number,number,number] = [
                section.point[0] * NM_TO_A,
                section.point[1] * NM_TO_A,
                section.point[2] * NM_TO_A,
            ];
            const vertices = this._buildDiscVertices(centerA, section.normal, discRadius, 32);
            const ref = await addTriangleFacesFromPython(this.plugin, {
                vertices,
                colors: 0x00e5ff,
                alpha: 0.30,
            });
            this.callbacks.registerShapeRef(ref, gizmoTag);
            this._sectionGizmoTags.add(gizmoTag);
        }
    }

    // ── 2D drag handles ────────────────────────────────────────────────────

    private _syncHandles(sections: SectionEntry[]) {
        const activeTags = new Set(sections.filter(section => !section.hidden).map(section => section.tag));
        // Remove handles for sections that no longer exist
        for (const [tag, el] of this._sectionHandles) {
            if (!activeTags.has(tag)) {
                el.remove();
                this._sectionHandles.delete(tag);
            }
        }
        for (const [tag, el] of this._sectionRimHandles) {
            if (!activeTags.has(tag)) {
                el.remove();
                this._sectionRimHandles.delete(tag);
            }
        }
        // Create handles for new sections
        for (const section of sections.filter(item => !item.hidden)) {
            if (!this._sectionHandles.has(section.tag)) {
                this._createSectionHandle(section.tag);
            }
            if (!this._sectionRimHandles.has(section.tag)) {
                this._createSectionRimHandle(section.tag);
            }
        }
    }

    private _createSectionHandle(tag: string) {
        const handle = document.createElement("div");
        Object.assign(handle.style, {
            position: "absolute",
            width: "24px",
            height: "24px",
            borderRadius: "50%",
            background: "rgba(0, 229, 255, 0.85)",
            border: "2px solid rgba(255,255,255,0.7)",
            cursor: "grab",
            zIndex: "10",
            boxSizing: "border-box",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            userSelect: "none",
            touchAction: "none",
            transform: "translate(-50%, -50%)",
            transition: "background 0.1s",
        });
        handle.title = `Section: ${tag} — drag to move`;

        // Inner dot
        const dot = document.createElement("div");
        Object.assign(dot.style, {
            width: "6px",
            height: "6px",
            borderRadius: "50%",
            background: "rgba(255,255,255,0.9)",
            pointerEvents: "none",
        });
        handle.appendChild(dot);

        let isDragging = false;
        let lastClientX = 0;
        let lastClientY = 0;

        handle.addEventListener("pointerdown", (e) => {
            if (this._dragDisabledTags.has(tag)) return;
            e.stopPropagation();
            e.preventDefault();
            handle.setPointerCapture(e.pointerId);
            isDragging = true;
            lastClientX = e.clientX;
            lastClientY = e.clientY;
            handle.style.cursor = "grabbing";
            handle.style.background = "rgba(0, 229, 255, 1.0)";
            this.callbacks.notify({ event: "scene_history_coalescing_begin" });
        });

        handle.addEventListener("pointermove", (e) => {
            if (!isDragging) return;
            e.stopPropagation();
            const dx = e.clientX - lastClientX;
            const dy = e.clientY - lastClientY;
            lastClientX = e.clientX;
            lastClientY = e.clientY;
            if (dx !== 0 || dy !== 0) this._onHandleDrag(tag, dx, dy);
        });

        const endDrag = async (e: PointerEvent) => {
            if (!isDragging) return;
            e.stopPropagation();
            isDragging = false;
            handle.releasePointerCapture(e.pointerId);
            handle.style.cursor = "grab";
            handle.style.background = "rgba(0, 229, 255, 0.85)";
            this.callbacks.notify({ event: "scene_history_coalescing_end" });
            // Rebuild gizmo disc at final position
            await this._updateSectionGizmos(this._activeSections);
        };
        handle.addEventListener("pointerup", endDrag);
        handle.addEventListener("pointercancel", endDrag);

        this.host.appendChild(handle);
        this._sectionHandles.set(tag, handle);
    }

    private _onHandleDrag(tag: string, screenDx: number, screenDy: number) {
        const section = this._activeSections.find(s => s.tag === tag);
        if (!section) return;

        const camera = this.plugin.canvas3d?.camera;
        if (!camera) return;

        const NM_TO_A = 10.0;
        const A_TO_NM = 0.1;
        const p = Vec3.create(
            section.point[0] * NM_TO_A,
            section.point[1] * NM_TO_A,
            section.point[2] * NM_TO_A,
        );
        const pixelSize = camera.getPixelSize(p); // world Å per pixel

        const state = camera.state;
        const forward = Vec3.normalize(Vec3(), Vec3.sub(Vec3(), state.target, state.position));
        const up = Vec3.normalize(Vec3(), state.up);
        const right = Vec3.normalize(Vec3(), Vec3.cross(Vec3(), forward, up));
        const n = Vec3.normalize(Vec3(), Vec3.create(...section.normal));

        // World-space drag vector: screen right maps to camera right, screen down to -camera up
        const dragVec = Vec3.add(Vec3(),
            Vec3.scale(Vec3(), right, screenDx * pixelSize),
            Vec3.scale(Vec3(), up, -screenDy * pixelSize),
        );
        // Only allow movement along the section normal
        const delta = Vec3.dot(dragVec, n);

        section.point = [
            section.point[0] + n[0] * delta * A_TO_NM,
            section.point[1] + n[1] * delta * A_TO_NM,
            section.point[2] + n[2] * delta * A_TO_NM,
        ];

        void this._applyClipFromSections(this._activeSections);
        this._repositionHandles();

        this.callbacks.notify({
            event: "section_moved",
            tag,
            point: [...section.point] as [number, number, number],
            normal: [...section.normal] as [number, number, number],
        });
    }

    private _repositionHandles() {
        const camera = this.plugin.canvas3d?.camera;
        if (!camera) return;
        const NM_TO_A = 10.0;
        const tmpV4 = Vec4.zero();

        for (const [tag, handle] of this._sectionHandles) {
            const section = this._activeSections.find(s => s.tag === tag);
            if (!section) continue;
            const p = Vec3.create(
                section.point[0] * NM_TO_A,
                section.point[1] * NM_TO_A,
                section.point[2] * NM_TO_A,
            );
            camera.project(tmpV4, p);
            handle.style.left = `${tmpV4[0]}px`;
            handle.style.top = `${tmpV4[1]}px`;
        }

        for (const [tag, handle] of this._sectionRimHandles) {
            const section = this._activeSections.find(s => s.tag === tag);
            if (!section) continue;
            const rimPos = this._getRimWorldPosA(section);
            camera.project(tmpV4, rimPos);
            handle.style.left = `${tmpV4[0]}px`;
            handle.style.top = `${tmpV4[1]}px`;
        }
    }

    // ── Rotation gizmo helpers ─────────────────────────────────────────────

    private _computeDiscRadius(): number {
        const camera = this.plugin.canvas3d?.camera;
        return camera ? Math.max(15, camera.state.radius * 0.3) : 20;
    }

    private _computeDiscU(normal: [number, number, number]): Vec3 {
        const n = Vec3.normalize(Vec3(), Vec3.create(...normal));
        const ref = Math.abs(n[0]) < 0.9 ? Vec3.create(1, 0, 0) : Vec3.create(0, 1, 0);
        return Vec3.normalize(Vec3(), Vec3.cross(Vec3(), ref, n));
    }

    private _getRimWorldPosA(section: SectionEntry): Vec3 {
        const NM_TO_A = 10;
        const center = Vec3.create(
            section.point[0] * NM_TO_A,
            section.point[1] * NM_TO_A,
            section.point[2] * NM_TO_A,
        );
        const u = this._computeDiscU(section.normal);
        const r = this._computeDiscRadius() * 0.75;
        return Vec3.scaleAndAdd(Vec3(), center, u, r);
    }

    private _rotateVec(v: Vec3, axis: Vec3, angleDeg: number): Vec3 {
        const θ = (angleDeg * Math.PI) / 180;
        const c = Math.cos(θ);
        const s = Math.sin(θ);
        const cross = Vec3.cross(Vec3(), axis, v);
        const dot = Vec3.dot(axis, v);
        return Vec3.normalize(Vec3(), Vec3.add(Vec3(),
            Vec3.add(Vec3(), Vec3.scale(Vec3(), v, c), Vec3.scale(Vec3(), cross, s)),
            Vec3.scale(Vec3(), axis, dot * (1 - c)),
        ));
    }

    private _onRimHandleDrag(tag: string, screenDx: number, screenDy: number) {
        const section = this._activeSections.find(s => s.tag === tag);
        if (!section) return;

        const camera = this.plugin.canvas3d?.camera;
        if (!camera) return;

        const state = camera.state;
        const forward = Vec3.normalize(Vec3(), Vec3.sub(Vec3(), state.target, state.position));
        const up = Vec3.normalize(Vec3(), state.up);
        const right = Vec3.normalize(Vec3(), Vec3.cross(Vec3(), forward, up));

        const DEG_PER_PX = 0.4;
        let n = Vec3.create(...section.normal);
        if (screenDx !== 0) n = this._rotateVec(n, up, screenDx * DEG_PER_PX);
        if (screenDy !== 0) n = this._rotateVec(n, right, screenDy * DEG_PER_PX);

        section.normal = [n[0], n[1], n[2]];

        void this._applyClipFromSections(this._activeSections);
        this._repositionHandles();

        this.callbacks.notify({
            event: "section_moved",
            tag,
            point: [...section.point] as [number, number, number],
            normal: [...section.normal] as [number, number, number],
        });
    }

    private _createSectionRimHandle(tag: string) {
        const handle = document.createElement("div");
        Object.assign(handle.style, {
            position: "absolute",
            width: "18px",
            height: "18px",
            borderRadius: "4px",
            background: "rgba(255, 200, 0, 0.85)",
            border: "2px solid rgba(255,255,255,0.7)",
            cursor: "ew-resize",
            zIndex: "10",
            boxSizing: "border-box",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            userSelect: "none",
            touchAction: "none",
            transform: "translate(-50%, -50%)",
            fontSize: "11px",
            color: "rgba(255,255,255,0.95)",
            fontFamily: "monospace",
            lineHeight: "1",
        });
        handle.textContent = "↻";
        handle.title = `Section: ${tag} — drag to rotate`;

        let isDragging = false;
        let lastClientX = 0;
        let lastClientY = 0;

        handle.addEventListener("pointerdown", (e) => {
            if (this._dragDisabledTags.has(tag)) return;
            e.stopPropagation();
            e.preventDefault();
            handle.setPointerCapture(e.pointerId);
            isDragging = true;
            lastClientX = e.clientX;
            lastClientY = e.clientY;
            handle.style.cursor = "grabbing";
            handle.style.background = "rgba(255, 200, 0, 1.0)";
            this.callbacks.notify({ event: "scene_history_coalescing_begin" });
        });

        handle.addEventListener("pointermove", (e) => {
            if (!isDragging) return;
            e.stopPropagation();
            const dx = e.clientX - lastClientX;
            const dy = e.clientY - lastClientY;
            lastClientX = e.clientX;
            lastClientY = e.clientY;
            if (dx !== 0 || dy !== 0) this._onRimHandleDrag(tag, dx, dy);
        });

        const endDrag = async (e: PointerEvent) => {
            if (!isDragging) return;
            e.stopPropagation();
            isDragging = false;
            handle.releasePointerCapture(e.pointerId);
            handle.style.cursor = "ew-resize";
            handle.style.background = "rgba(255, 200, 0, 0.85)";
            this.callbacks.notify({ event: "scene_history_coalescing_end" });
            await this._updateSectionGizmos(this._activeSections);
        };
        handle.addEventListener("pointerup", endDrag);
        handle.addEventListener("pointercancel", endDrag);

        this.host.appendChild(handle);
        this._sectionRimHandles.set(tag, handle);
    }

    private _ensureCameraSubscription() {
        if (this._cameraStateSub) return;
        const camera = this.plugin.canvas3d?.camera;
        if (!camera) return;
        this._cameraStateSub = camera.stateChanged.subscribe(() => {
            this._repositionHandles();
        });
    }

    async setActiveSectionDrag(msg: SetSectionDragMessage) {
        const tag = msg.tag;
        const enabled = msg.enabled ?? true;
        if (enabled) {
            this._dragDisabledTags.delete(tag);
            const handle = this._sectionHandles.get(tag);
            if (handle) handle.style.display = "";
            const rim = this._sectionRimHandles.get(tag);
            if (rim) rim.style.display = "";
        } else {
            this._dragDisabledTags.add(tag);
            const handle = this._sectionHandles.get(tag);
            if (handle) handle.style.display = "none";
            const rim = this._sectionRimHandles.get(tag);
            if (rim) rim.style.display = "none";
        }
    }

    async setBackgroundColor(msg: SetBackgroundColorMessage) {
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        canvas3d.setProps({
            renderer: { ...(canvas3d.props?.renderer ?? {}), backgroundColor: msg.color },
        } as any);
    }

    async setLighting(msg: SetLightingMessage) {
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const renderer = { ...(canvas3d.props?.renderer ?? {}) } as any;
        if (msg.ambient !== undefined) renderer.ambientIntensity = msg.ambient;
        // Mol* models directional light intensity per-light in renderer.light[].
        // diffuse maps to the primary light's intensity; specular is a fallback
        // because Mol* has no separate specular channel.
        const lightIntensity = msg.diffuse ?? msg.specular;
        if (lightIntensity !== undefined && Array.isArray(renderer.light) && renderer.light.length > 0) {
            renderer.light = renderer.light.map((l: any, i: number) => (i === 0 ? { ...l, intensity: lightIntensity } : l));
        }
        canvas3d.setProps({ renderer } as any);
    }

    async setClipPlanes(msg: SetClipPlanesMessage) {
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const clipping: any = { ...(canvas3d.props?.cameraClipping ?? {}) };
        if (msg.near !== undefined) clipping.radius = msg.near;
        if (msg.far !== undefined) clipping.far = msg.far;
        if (msg.min_near !== undefined) clipping.minNear = msg.min_near;
        canvas3d.setProps({ cameraClipping: clipping } as any);
    }

    async setCameraMode(msg: { mode: string }) {
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const mode = msg.mode === "orthographic" ? "orthographic" : "perspective";
        canvas3d.setProps({ camera: { ...(canvas3d.props?.camera ?? {}), mode } } as any);
    }

    async setFog(msg: SetFogMessage) {
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const enabled = msg.enable ?? true;
        // Python API uses 0.0–1.0; Mol* expects 1–100.
        const intensityRaw = msg.intensity ?? 0.5;
        const intensity = Math.round(Math.max(1, Math.min(100, intensityRaw * 100)));
        canvas3d.setProps({
            cameraFog: enabled
                ? { name: "on", params: { intensity } }
                : { name: "off", params: {} },
        } as any);
    }

    async zoomToPosition(msg: ZoomToPositionMessage) {
        const [cx, cy, cz] = msg.center;
        const radius = msg.radius ?? 5;
        const sphere = Sphere3D.create(Vec3.create(cx, cy, cz), radius);
        this.plugin.managers.camera.focusSphere(sphere, {
            durationMs: msg.duration_ms ?? 250,
        });
    }

    async clearScene(msg: ClearSceneMessage) {
        const options = msg.options;
        const shapes = options?.shapes ?? true;
        const styles = options?.styles ?? true;
        const labels = options?.labels ?? false;

        if (shapes) await this.callbacks.clearShapes();
        if (styles) await this.resetStructureDecorations();
        if (labels) await this.callbacks.clearLabels();
    }

    async clearShapesByTag(msg: ClearByTagMessage) {
        await this.callbacks.clearShapesByTag(msg.tag);
    }

    async clearAll() {
        clearPerAtomColors();
        await this.clearScene({ op: "clear_scene", options: { shapes: true, styles: true, labels: true } });
        await this.callbacks.removeLoadedStructure();
        this.callbacks.notify({ event: "registry_cleared" });
    }

    private async resetStructureDecorations() {
        const components = this.callbacks.getComponents();
        if (components.length === 0) return;
        await clearStructureTransparency(this.plugin, components);
    }
}
