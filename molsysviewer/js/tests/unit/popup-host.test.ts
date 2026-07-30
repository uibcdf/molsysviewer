import assert from "node:assert";
import test from "node:test";

import { PopupHostManager } from "../../src/managers/popup-host";
import type { PopupChannelIdentity } from "../../src/messages/popup-channel";

let popupMessageCounter = 0;

function popupWire(
    channel: PopupChannelIdentity,
    action: string,
    payload: unknown,
    direction: "command" | "event" = "event",
) {
    return {
        channel,
        envelope: {
            protocolVersion: 1,
            viewerId: channel.viewerId,
            sessionId: channel.sessionId,
            endpointId: channel.popupEndpointId,
            targetEndpointId:
                direction === "command"
                    ? channel.authorityEndpointId
                    : channel.hostEndpointId,
            messageId: `popup-test:${++popupMessageCounter}`,
            direction,
            action,
            payload,
        },
    };
}

function makePopupWindow() {
    const appended: any[] = [];
    const blobs: any[] = [];
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
                blobs.push(this);
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

    return { popup, appended, doc, blobs };
}

test("popup host resolves source provider only when opening", async () => {
    const previousWindow = (globalThis as any).window;
    const { popup, appended, blobs } = makePopupWindow();
    const order: string[] = [];

    (globalThis as any).window = {
        location: { href: "https://notebook.example.dev/lab", origin: "https://notebook.example.dev" },
        open: () => {
            order.push("open");
            return popup;
        },
        setInterval: () => 1,
        clearInterval: (_id: number) => {},
    };

    try {
        const manager = new PopupHostManager({
            sourceProvider: async () => {
                order.push("provider");
                return "export const lazy = true;";
            },
        });

        assert.deepStrictEqual(order, []);
        await manager.open();

        assert.deepStrictEqual(order, ["open", "provider"]);
        assert.strictEqual(blobs.length, 1);
        assert.deepStrictEqual(blobs[0].parts, ["export const lazy = true;"]);
        assert.strictEqual(appended.length, 1);
        assert.match(appended[0].textContent, /blob:popup-runtime/);
    } finally {
        (globalThis as any).window = previousWindow;
    }
});

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
        location: { href: "https://docs.example.dev/views/demo.html", origin: "https://docs.example.dev" },
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

test("popup host sends and accepts messages only on the bound popup channel", async () => {
    const previousWindow = (globalThis as any).window;
    const { popup } = makePopupWindow();
    (globalThis as any).window = {
        location: { href: "https://notebook.example.dev/lab", origin: "https://notebook.example.dev" },
        open: () => popup,
        setInterval: () => 1,
        clearInterval: (_id: number) => {},
    };
    const manager = new PopupHostManager({
        source: "viewer-source",
        viewerId: "view-a",
        sessionId: "session-a",
    });

    try {
        await manager.open();
        const channel = popup.molsysviewer_popup_channel;

        manager.send("molsysviewer-sync-op", { op: "dummy" });
        assert.deepStrictEqual(popup.posted, []);

        manager.isReady = true;
        manager.send("molsysviewer-sync-op", { op: "dummy" });
        assert.equal(popup.posted.length, 1);
        assert.deepStrictEqual(popup.posted[0].message.channel, channel);
        assert.deepStrictEqual(popup.posted[0].message.envelope, {
            protocolVersion: 1,
            viewerId: "view-a",
            sessionId: "session-a",
            endpointId: channel.authorityEndpointId,
            targetEndpointId: channel.popupEndpointId,
            messageId: `${channel.hostEndpointId}:1`,
            direction: "projection",
            action: "molsysviewer-sync-op",
            payload: { op: "dummy" },
        });
        assert.equal(popup.posted[0].target, "https://notebook.example.dev");

        const legitimate = {
            source: popup,
            data: popupWire(channel, "molsysviewer-pop-ready", null),
        } as MessageEvent;
        assert.equal(manager.receive(legitimate)?.type, "molsysviewer-pop-ready");
        const command = {
            source: popup,
            data: popupWire(
                channel,
                "molsysviewer-sync-op",
                { op: "reset_view" },
                "command",
            ),
        } as MessageEvent;
        assert.equal(manager.receive(command)?.type, "molsysviewer-sync-op");
        assert.equal(manager.receive(command), null);

        const impersonated = popupWire(
            channel,
            "molsysviewer-pop-ready",
            null,
        );
        impersonated.envelope.endpointId = channel.hostEndpointId;
        assert.equal(manager.receive({
            source: popup,
            data: impersonated,
        } as MessageEvent), null);
        assert.equal(manager.receive({
            ...legitimate,
            source: {},
        } as MessageEvent), null);
        assert.equal(manager.receive({
            ...legitimate,
            data: {
                ...legitimate.data,
                channel: { ...channel, token: "forged" },
            },
        } as MessageEvent), null);

        popup.closed = true;
        manager.send("molsysviewer-sync-op", { op: "ignored" });
        assert.strictEqual(popup.posted.length, 1);
    } finally {
        (globalThis as any).window = previousWindow;
    }
});

test("popup host reopening revokes the previous endpoint channel", async () => {
    const previousWindow = (globalThis as any).window;
    const first = makePopupWindow().popup;
    const second = makePopupWindow().popup;
    const popups = [first, second];
    (globalThis as any).window = {
        location: { href: "https://notebook.example.dev/lab", origin: "https://notebook.example.dev" },
        open: () => popups.shift(),
        setInterval: () => 1,
        clearInterval: (_id: number) => {},
    };
    const manager = new PopupHostManager({
        source: "viewer-source",
        viewerId: "view-a",
        sessionId: "session-a",
    });

    try {
        await manager.open();
        const staleChannel = first.molsysviewer_popup_channel;
        manager.close();
        await manager.open();
        const currentChannel = second.molsysviewer_popup_channel;
        assert.notEqual(staleChannel.token, currentChannel.token);

        assert.equal(manager.receive({
            source: second,
            data: popupWire(staleChannel, "molsysviewer-pop-ready", null),
        } as MessageEvent), null);
        assert.equal(manager.receive({
            source: second,
            data: popupWire(currentChannel, "molsysviewer-pop-ready", null),
        } as MessageEvent)?.type, "molsysviewer-pop-ready");
    } finally {
        manager.dispose();
        (globalThis as any).window = previousWindow;
    }
});

test("popup host dispose closes canvas and panel endpoints", async () => {
    const previousWindow = (globalThis as any).window;
    const canvas = makePopupWindow().popup;
    const panel = makePopupWindow().popup;
    const popups = [canvas, panel];
    (globalThis as any).window = {
        location: { href: "https://notebook.example.dev/lab", origin: "https://notebook.example.dev" },
        open: () => popups.shift(),
        setInterval: () => 1,
        clearInterval: (_id: number) => {},
    };
    const manager = new PopupHostManager("viewer-source");

    try {
        await manager.open("canvas");
        await manager.open("panel");
        manager.dispose();

        assert.equal(canvas.closed, true);
        assert.equal(panel.closed, true);
        assert.equal(manager.isCanvasOpen, null);
        assert.equal(manager.isPanelOpen, null);
    } finally {
        manager.dispose();
        (globalThis as any).window = previousWindow;
    }
});

test("sendTo delivers to one popup endpoint, so a canvas bootstrap never reaches a panel popup", async () => {
    const previousWindow = (globalThis as any).window;
    const canvas = makePopupWindow().popup;
    const panel = makePopupWindow().popup;
    const opened: any[] = [];
    (globalThis as any).window = {
        location: { href: "https://notebook.example.dev/lab", origin: "https://notebook.example.dev" },
        // First open() is the canvas popup, second is the panel popup.
        open: () => (opened.push(1), opened.length === 1 ? canvas : panel),
        setInterval: () => 1,
        clearInterval: (_id: number) => {},
    };
    const manager = new PopupHostManager({
        source: "viewer-source",
        viewerId: "view-a",
        sessionId: "session-a",
    });

    try {
        await manager.open("canvas");
        await manager.open("panel");
        manager.isReady = true;
        manager.isPanelReady = true;
        canvas.posted.length = 0;
        panel.posted.length = 0;

        // A canvas bootstrap carries molecular data; it must not fan out.
        assert.equal(manager.sendTo("canvas", "molsysviewer-initial-sync", { messages: ["molecular"] }), true);
        assert.equal(canvas.posted.length, 1);
        assert.equal(panel.posted.length, 0, "the panel popup must not receive the canvas bootstrap");

        // And the panel's own bootstrap reaches only the panel.
        assert.equal(manager.sendTo("panel", "molsysviewer-initial-sync", { messages: ["ui-only"] }), true);
        assert.equal(panel.posted.length, 1);
        assert.equal(canvas.posted.length, 1);

        // send() remains the deliberate fan-out for shared projections.
        canvas.posted.length = 0;
        panel.posted.length = 0;
        manager.send("molsysviewer-sync-op", { op: "shared" });
        assert.equal(canvas.posted.length, 1);
        assert.equal(panel.posted.length, 1);
    } finally {
        (globalThis as any).window = previousWindow;
    }
});

test("sendTo reports failure instead of delivering when that endpoint is closed", async () => {
    const previousWindow = (globalThis as any).window;
    const { popup } = makePopupWindow();
    (globalThis as any).window = {
        location: { href: "https://notebook.example.dev/lab", origin: "https://notebook.example.dev" },
        open: () => popup,
        setInterval: () => 1,
        clearInterval: (_id: number) => {},
    };
    const manager = new PopupHostManager({
        source: "viewer-source",
        viewerId: "view-a",
        sessionId: "session-a",
    });
    try {
        await manager.open("canvas");
        manager.isReady = true;
        popup.posted.length = 0;
        // No panel popup was ever opened.
        assert.equal(manager.sendTo("panel", "molsysviewer-initial-sync", { messages: [] }), false);
        assert.equal(popup.posted.length, 0, "a panel-targeted message must not land on the canvas popup");
    } finally {
        (globalThis as any).window = previousWindow;
    }
});
