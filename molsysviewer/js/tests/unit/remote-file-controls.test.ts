import assert from "node:assert/strict";
import test from "node:test";

import { RemoteFileControls } from "../../src/ui/remote-file-controls";

class FakeElement {
    readonly style: Record<string, string> = {};
    readonly children: FakeElement[] = [];
    readonly attributes = new Map<string, string>();
    readonly listeners = new Map<string, Array<() => void>>();
    textContent = "";
    type = "";
    accept = "";
    value = "";
    disabled = false;
    files: Array<{ name: string }> | null = null;
    append(...children: FakeElement[]) { this.children.push(...children); }
    appendChild(child: FakeElement) { this.children.push(child); return child; }
    remove() {}
    click() {}
    setAttribute(name: string, value: string) { this.attributes.set(name, value); }
    getAttribute(name: string) { return this.attributes.get(name); }
    addEventListener(name: string, callback: () => void) {
        const callbacks = this.listeners.get(name) ?? [];
        callbacks.push(callback);
        this.listeners.set(name, callbacks);
    }
    dispatch(name: string) { for (const callback of this.listeners.get(name) ?? []) callback(); }
}

const find = (root: FakeElement, name: string): FakeElement | undefined => {
    if (root.getAttribute(name) !== undefined) return root;
    for (const child of root.children) {
        const found = find(child, name);
        if (found) return found;
    }
    return undefined;
};

test("RemoteFileControls uploads one selected file and reports molecular counts", async () => {
    const previous = (globalThis as any).document;
    (globalThis as any).document = { createElement: () => new FakeElement() };
    try {
        const host = new FakeElement();
        const uploaded: string[] = [];
        new RemoteFileControls(host as unknown as HTMLElement, async file => {
            uploaded.push(file.name);
            return { filename: file.name, nAtoms: 4, nStructures: 1 };
        });
        const input = find(host, "data-molsysviewer-upload-input")!;
        input.files = [{ name: "system.pdb" }];
        input.dispatch("change");
        await new Promise(resolve => setTimeout(resolve, 0));

        assert.deepEqual(uploaded, ["system.pdb"]);
        const status = find(host, "data-molsysviewer-upload-status")!;
        assert.equal(status.getAttribute("data-molsysviewer-upload-status"), "loaded");
        assert.equal(status.textContent, "system.pdb: 4 atoms · 1 frame");
    } finally {
        (globalThis as any).document = previous;
    }
});
