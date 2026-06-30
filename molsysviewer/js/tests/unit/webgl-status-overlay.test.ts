import assert from "node:assert";
import test from "node:test";

import { WebGLStatusOverlay } from "../../src/ui/webgl-status-overlay";

class FakeElement {
    public readonly style: Record<string, string> = {};
    public readonly children: FakeElement[] = [];
    public textContent = "";
    public parentElement: FakeElement | null = null;
    public readonly attributes: Record<string, string> = {};

    setAttribute(name: string, value: string) {
        this.attributes[name] = value;
    }

    appendChild(child: FakeElement) {
        child.parentElement = this;
        this.children.push(child);
        return child;
    }

    remove() {
        if (!this.parentElement) return;
        const index = this.parentElement.children.indexOf(this);
        if (index >= 0) this.parentElement.children.splice(index, 1);
        this.parentElement = null;
    }
}

function withFakeDom<T>(run: () => T): T {
    const previous = (globalThis as any).document;
    (globalThis as any).document = { createElement: () => new FakeElement() };
    try {
        return run();
    } finally {
        (globalThis as any).document = previous;
    }
}

test("WebGLStatusOverlay mounts hidden and toggles on show/hide", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new WebGLStatusOverlay(host as unknown as HTMLElement);

        // Mounted into the host, hidden by default.
        assert.strictEqual(host.children.length, 1);
        const root = host.children[0];
        assert.strictEqual(root.style.display, "none");
        assert.strictEqual(root.attributes["data-molsysviewer-webgl-status"], "true");

        overlay.show("GPU connection lost. Restoring the scene…");
        assert.strictEqual(root.style.display, "block");
        assert.strictEqual(root.textContent, "GPU connection lost. Restoring the scene…");

        overlay.hide();
        assert.strictEqual(root.style.display, "none");
        assert.strictEqual(root.textContent, "");
    });
});

test("WebGLStatusOverlay dispose removes it from the host", () => {
    withFakeDom(() => {
        const host = new FakeElement();
        const overlay = new WebGLStatusOverlay(host as unknown as HTMLElement);
        assert.strictEqual(host.children.length, 1);

        overlay.dispose();
        assert.strictEqual(host.children.length, 0);
    });
});
