import assert from "node:assert/strict";
import test from "node:test";
import { StudioImageExports, isStudioImageRequest } from "../../src/managers/studio-image-exports";

const png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB";
const request = (id = "ui-image") => ({ event: "interaction_context_action", action: "download_image",
    request_id: id, scale: 2, transparent: true, preset: "publication-light" });

function fixture(timeout = 180000) {
    const owners = new Set(["panel-a", "panel-b"]), renderers = new Set(["primary", "canvas-popup"]);
    const dispatched: { renderer: string; message: any }[] = [], delivered: { owner: string; result: any }[] = [];
    const broker = new StudioImageExports({
        ownerIsLive: owner => owners.has(owner), rendererIsLive: renderer => renderers.has(renderer),
        dispatch: (renderer, message) => { dispatched.push({ renderer, message }); return renderers.has(renderer); },
        deliver: (owner, result) => { delivered.push({ owner, result }); },
    }, timeout);
    const reply = (index = 0) => ({ ...dispatched[index].message, event: "image_export", data_uri: png });
    return { broker, owners, renderers, dispatched, delivered, reply };
}

test("Studio PNG belongs to its transport owner and associated canvas, with exact settings", () => {
    const f = fixture();
    try {
        assert.equal(f.broker.handle("panel-a", "canvas-popup", { ...request(), renderer: "primary", target_endpoint_id: "panel-b" }), true);
        assert.equal(f.dispatched[0].renderer, "canvas-popup");
        const message = f.dispatched[0].message;
        assert.equal(isStudioImageRequest(message), true);
        assert.equal(message.scale, 2); assert.equal(message.transparent, true); assert.equal(message.preset, "publication-light");
        assert.notEqual(message.request_id, "ui-image");
        assert.equal(f.broker.receive("canvas-popup", f.reply()), true);
        assert.deepEqual(f.delivered, [{ owner: "panel-a", result: { op: "studio_action_result", domain: "export",
            action: "download_image", request_id: "ui-image", target_endpoint_id: "panel-a", ok: true, image_data_uri: png } }]);
        f.broker.receive("canvas-popup", f.reply());
        assert.equal(f.delivered.length, 1, "late duplicate must never download again");
    } finally { f.broker.dispose(); }
});

test("foreign renderers and revisions cannot consume another pending PNG", () => {
    const f = fixture();
    try {
        f.broker.handle("panel-a", "primary", request());
        assert.equal(f.broker.receive("canvas-popup", f.reply()), true);
        assert.equal(f.broker.receive("primary", { ...f.reply(), capture_revision: "foreign" }), true);
        assert.equal(f.broker.receive("primary", { ...f.reply(), request_id: "foreign" }), true);
        assert.equal(f.delivered.length, 0);
        f.broker.receive("primary", f.reply()); assert.equal(f.delivered[0].result.ok, true);
        assert.equal(f.broker.receive("primary", { event: "image_export", data_uri: png }), false, "legacy Python reply stays independent");
    } finally { f.broker.dispose(); }
});

test("same UI ids in separate owners and Views remain independent; cancellation is owner-bound", () => {
    const f = fixture(), other = fixture();
    try {
        f.broker.handle("panel-a", "primary", request());
        f.broker.handle("panel-b", "canvas-popup", request());
        other.broker.handle("panel-a", "primary", request());
        const cancel = { ...request(), action: "cancel_image_download" };
        f.broker.handle("panel-b", "primary", cancel);
        assert.equal(f.dispatched[2].renderer, "canvas-popup");
        assert.equal(f.dispatched[2].message.op, "cancel_visual_state");
        assert.equal(f.delivered[0].owner, "panel-b"); assert.equal(f.delivered[0].result.ok, false);
        f.broker.receive("canvas-popup", f.reply(1)); assert.equal(f.delivered.length, 1);
        f.broker.receive("primary", f.reply()); assert.equal(f.delivered[1].owner, "panel-a");
        other.broker.receive("primary", other.reply()); assert.equal(other.delivered[0].result.ok, true);
    } finally { f.broker.dispose(); other.broker.dispose(); }
});

test("closing either endpoint cancels only related PNGs and never substitutes another canvas", () => {
    const f = fixture();
    try {
        f.broker.handle("panel-a", "canvas-popup", request());
        f.broker.handle("panel-b", "primary", request());
        f.renderers.delete("canvas-popup"); f.broker.closeEndpoint("canvas-popup");
        assert.equal(f.delivered[0].owner, "panel-a"); assert.equal(f.delivered[0].result.ok, false);
        assert.equal(f.dispatched.filter(d => d.message.op === "request_image_export").length, 2);
        f.broker.receive("canvas-popup", f.reply()); assert.equal(f.delivered.length, 1);
        f.broker.receive("primary", f.reply(1)); assert.equal(f.delivered[1].result.ok, true);
        f.broker.handle("panel-b", "primary", request("second"));
        f.owners.delete("panel-b"); f.broker.closeEndpoint("panel-b");
        assert.equal(f.dispatched.at(-1)?.message.op, "cancel_visual_state");
        assert.equal(f.delivered.length, 2, "closed requester must not receive an image/verdict");
    } finally { f.broker.dispose(); }
});

test("PNG deadline cancels the renderer, ignores late output and permits retry", async () => {
    const f = fixture(10);
    try {
        f.broker.handle("panel-a", "primary", request());
        await new Promise(resolve => setTimeout(resolve, 30));
        assert.match(f.delivered[0].result.error_message, /timed out/);
        assert.equal(f.dispatched[1].message.op, "cancel_visual_state");
        f.broker.receive("primary", f.reply()); assert.equal(f.delivered.length, 1);
        f.broker.handle("panel-a", "primary", request("retry"));
        f.broker.receive("primary", f.reply(2)); assert.equal(f.delivered[1].result.ok, true);
    } finally { f.broker.dispose(); }
});

test("unavailable origins, invalid options, busy owners and non-PNG output are explicit failures", () => {
    const f = fixture();
    try {
        f.broker.handle("panel-a", "missing", request());
        assert.match(f.delivered.at(-1)?.result.error_message, /originating canvas/);
        for (const patch of [{ scale: NaN }, { scale: 0 }, { transparent: "true" }, { preset: null }]) {
            f.broker.handle("panel-a", "primary", { ...request(), ...patch });
            assert.equal(f.delivered.at(-1)?.result.ok, false);
        }
        assert.equal(f.dispatched.length, 0);
        f.broker.handle("panel-a", "primary", request());
        f.broker.handle("panel-a", "primary", request("another"));
        assert.match(f.delivered.at(-1)?.result.error_message, /already running/);
        f.broker.receive("primary", { ...f.reply(), data_uri: "data:text/html,invalid" });
        assert.equal(f.delivered.at(-1)?.result.ok, false);
        f.broker.handle("panel-a", "primary", request("recovered"));
        f.broker.receive("primary", { ...f.reply(1), data_uri: undefined, message: "GPU limit exceeded" });
        assert.equal(f.delivered.at(-1)?.result.error_message, "GPU limit exceeded");
    } finally { f.broker.dispose(); }
});

test("disposing the widget aborts pending PNGs without a download or further work", () => {
    const f = fixture();
    f.broker.handle("panel-a", "primary", request()); f.broker.dispose(); f.broker.dispose();
    assert.equal(f.dispatched[1].message.op, "cancel_visual_state");
    f.broker.receive("primary", f.reply()); f.broker.handle("panel-a", "primary", request());
    assert.equal(f.dispatched.length, 2); assert.equal(f.delivered.length, 0);
});
