import assert from "node:assert";
import test from "node:test";

import { PopupHostManager } from "../../src/managers/popup-host";

function makePopupWindow() {
    const appended: any[] = [];
    const doc = {
        html: "",
        open() {},
        write(chunk: string) { this.html += chunk; },
        close() {},
        createElement(_tag: string) {
            return {
                type: "",
                textContent: "",
            };
        },
        body: {
            appendChild(node: any) {
                appended.push(node);
            },
        },
    };

    const popup: any = {
        closed: false,
        document: doc,
        Blob: class {
            parts: any[];
            options: any;
            constructor(parts: any[], options: any) {
                this.parts = parts;
                this.options = options;
            }
        },
        URL: {
            createObjectURL: () => "blob:popup-runtime",
            revokeObjectURL: (_url: string) => {},
        },
        posted: [] as any[],
        postMessage(message: any, target: string) {
            this.posted.push({ message, target });
        },
        close() {
            this.closed = true;
        },
    };

    return { popup, appended, doc };
}

test("popup host resolves moduleUrl and injects module bootstrap", async () => {
    const previousWindow = (globalThis as any).window;
    const previousFetch = (globalThis as any).fetch;
    const { popup, appended, doc } = makePopupWindow();
    const fetched: Array<{ url: string; options: any }> = [];

    (globalThis as any).fetch = (url: string, options: any) => {
        fetched.push({ url, options });
        return Promise.resolve({ ok: true });
    };
    (globalThis as any).window = {
        location: { href: "https://docs.example.dev/views/demo.html" },
        open: () => popup,
        setInterval: () => 1,
        clearInterval: (_id: number) => {},
    };

    try {
        const manager = new PopupHostManager({ moduleUrl: "./viewer.js" });
        await manager.open();

        assert.strictEqual(
            fetched[0]?.url,
            "https://docs.example.dev/views/viewer.js",
        );
        assert.deepStrictEqual(fetched[0]?.options, { cache: "force-cache" });
        assert.match(doc.html, /modulepreload/);
        assert.match(doc.html, /https:\/\/docs\.example\.dev\/views\/viewer\.js/);
        assert.strictEqual(appended.length, 1);
        assert.match(appended[0].textContent, /bootPopup/);
        assert.match(appended[0].textContent, /https:\/\/docs\.example\.dev\/views\/viewer\.js/);
    } finally {
        (globalThis as any).window = previousWindow;
        (globalThis as any).fetch = previousFetch;
    }
});

test("popup host send only posts when popup is ready and open", () => {
    const { popup } = makePopupWindow();
    const manager = new PopupHostManager("viewer-source");

    (manager as any).popoutWin = popup;

    manager.send("molsysviewer-sync-op", { op: "dummy" });
    assert.deepStrictEqual(popup.posted, []);

    manager.isReady = true;
    manager.send("molsysviewer-sync-op", { op: "dummy" });
    assert.deepStrictEqual(popup.posted, [
        {
            message: { type: "molsysviewer-sync-op", data: { op: "dummy" }, from: "host" },
            target: "*",
        },
    ]);

    popup.closed = true;
    manager.send("molsysviewer-sync-op", { op: "ignored" });
    assert.strictEqual(popup.posted.length, 1);
});
