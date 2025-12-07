import { PluginContext } from "molstar/lib/mol-plugin/context";
import { PluginCommands } from "molstar/lib/mol-plugin/commands";
import { StateObjectRef } from "molstar/lib/mol-state";
import { clearStructureTransparency } from "molstar/lib/mol-plugin-state/helpers/structure-transparency";
import { StructureComponentRef } from "molstar/lib/mol-plugin-state/manager/structure/hierarchy-state";
import {
    ClearByTagMessage,
    ClearSceneMessage,
    ToggleBackgroundMessage,
    ToggleFullscreenMessage,
    ToggleSpinMessage,
    ToggleSwingMessage,
} from "../../messages/viewer-messages";

export interface SceneCallbacks {
    clearShapes: () => Promise<void>;
    clearLabels: () => Promise<void>;
    getComponents: () => StructureComponentRef[];
    clearShapesByTag: (tag?: string) => Promise<void>;
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
        const root = this.plugin.canvas3d?.props.parent;
        const canvas = this.plugin.canvas3d?.props.canvas ?? this.plugin.canvas3d?.getCanvas?.();
        const target =
            this.host ??
            root?.parentElement ??
            root ??
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
                    lightColor: 0xffffff,
                    ambientColor: 0xffffff,
                    exposure: renderer.exposure ?? 1,
                    lightIntensity: renderer.lightIntensity ?? 1,
                    ambientIntensity: renderer.ambientIntensity ?? 1,
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
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const shouldEnable = enable ?? !this.swingActive;
        this.swingActive = shouldEnable;
        this.spinActive = false;
        canvas3d.setProps({
            trackball: {
                ...(canvas3d.props?.trackball || {}),
                animate: shouldEnable
                    ? { name: "rock", params: { speed: 0.25, angle: 20 } }
                    : { name: "off", params: {} },
            },
        });
    }

    async toggleSpin(msg: ToggleSpinMessage | boolean) {
        const enable = typeof msg === 'boolean' ? msg : msg.enable;
        const canvas3d = this.plugin.canvas3d;
        if (!canvas3d) return;
        const shouldEnable = enable ?? !this.spinActive;
        this.spinActive = shouldEnable;
        this.swingActive = false;
        canvas3d.setProps({
            trackball: {
                ...(canvas3d.props?.trackball || {}),
                animate: shouldEnable ? { name: "spin", params: { speed: 0.1 } } : { name: "off", params: {} },
            },
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
