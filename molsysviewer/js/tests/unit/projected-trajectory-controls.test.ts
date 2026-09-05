import assert from "node:assert/strict";
import test from "node:test";

import {
    ProjectedTrajectoryControls,
    type ProjectedTrajectoryIntent,
} from "../../src/ui/projected-trajectory-controls";

class FakeElement {
    readonly style: Record<string, string> = {};
    readonly children: FakeElement[] = [];
    readonly attributes = new Map<string, string>();
    readonly listeners = new Map<string, Array<() => void>>();
    textContent = "";
    title = "";
    type = "";
    min = "";
    max = "";
    value = "";
    disabled = false;

    append(...children: FakeElement[]) { this.children.push(...children); }
    appendChild(child: FakeElement) { this.children.push(child); return child; }
    remove() {}
    setAttribute(name: string, value: string) { this.attributes.set(name, value); }
    getAttribute(name: string) { return this.attributes.get(name); }
    addEventListener(name: string, handler: () => void) {
        const listeners = this.listeners.get(name) ?? [];
        listeners.push(handler);
        this.listeners.set(name, listeners);
    }
    dispatch(name: string) { for (const listener of this.listeners.get(name) ?? []) listener(); }
}

const installFakeDom = () => {
    const previous = (globalThis as any).document;
    (globalThis as any).document = { createElement: () => new FakeElement() };
    return () => { (globalThis as any).document = previous; };
};

const byAttribute = (root: FakeElement, name: string, value?: string): FakeElement | undefined => {
    if (root.getAttribute(name) !== undefined && (value === undefined || root.getAttribute(name) === value)) return root;
    for (const child of root.children) {
        const found = byAttribute(child, name, value);
        if (found) return found;
    }
    return undefined;
};

test("ProjectedTrajectoryControls renders authority state and emits only semantic intents", () => {
    const restore = installFakeDom();
    try {
        const host = new FakeElement();
        const intents: ProjectedTrajectoryIntent[] = [];
        const controls = new ProjectedTrajectoryControls(
            host as unknown as HTMLElement,
            intent => intents.push(intent),
        );
        controls.apply({
            frame: 3,
            frame_count: 12,
            is_playing: false,
            fps: 20,
            step: 2,
            mode: "once",
            direction: "backward",
        });

        assert.equal(controls.currentFrame, 3);
        assert.equal(controls.root.style.display, "flex");
        assert.equal(byAttribute(host, "data-molsysviewer-trajectory-label")?.textContent, "4 / 12");

        byAttribute(host, "data-molsysviewer-trajectory-step", "next")?.dispatch("click");
        byAttribute(host, "data-molsysviewer-trajectory-playback", "play")?.dispatch("click");
        const slider = byAttribute(host, "data-molsysviewer-trajectory-frame")!;
        slider.value = "8";
        slider.dispatch("change");

        assert.deepEqual(intents, [
            { action: "step_trajectory", by: 2 },
            {
                action: "set_trajectory_playback",
                playback_action: "play",
                fps: 20,
                step: 2,
                mode: "once",
                direction: "backward",
            },
            { action: "set_trajectory_frame", index: 8 },
        ]);

        controls.apply({ frame: 8, frame_count: 12, is_playing: true });
        byAttribute(host, "data-molsysviewer-trajectory-playback", "stop")?.dispatch("click");
        assert.deepEqual(intents.at(-1), {
            action: "set_trajectory_playback",
            playback_action: "stop",
        });
    } finally {
        restore();
    }
});
