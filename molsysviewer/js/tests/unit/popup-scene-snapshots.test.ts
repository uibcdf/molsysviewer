import assert from "node:assert/strict";
import test from "node:test";
import { PopupSceneSnapshots } from "../../src/messages/popup-scene-snapshots";

const begin = (generation = 1, stream_id = "stream-a") => ({ op: "structure_data_begin", generation, stream_id });
const complete = { event: "structure_data_complete", generation: 1, stream_id: "stream-a" };

test("a correlated popup scene survives a slow but bounded molecular application", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const request = requests.request("request-a", "canvas", "canvas-a");
    t.mock.timers.tick(4000);
    requests.structure("canvas-a", begin());
    t.mock.timers.tick(6000);
    assert.equal(requests.has("canvas"), true, "the old five-second response expiry cannot discard a real load");
    requests.structure("canvas-a", complete);
    const messages: any[] = [{ op: "add_sphere", options: { tag: "moving-marker" } }];
    requests.resolve("request-a", messages);
    assert.deepEqual(await request.promise, { ok: true, messages });
    assert.equal(request.isCurrent(), true);
    assert.equal(requests.has("canvas"), false);
    t.mock.timers.tick(30000);
});

test("source silence still expires at five seconds and late replies cannot revive it", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const request = requests.request("request-a", "canvas", "canvas-a");
    requests.resolve("foreign-request", []);
    t.mock.timers.tick(5000);
    requests.resolve("request-a", []);
    assert.deepEqual(await request.promise, { ok: false, reason: "request_timeout" });
    assert.equal(requests.has("canvas"), false);
});

test("a stalled molecular application expires at its own thirty-second bound", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const request = requests.request("request-a", "canvas", "canvas-a");
    requests.structure("canvas-a", begin());
    t.mock.timers.tick(29999);
    assert.equal(requests.has("canvas"), true);
    t.mock.timers.tick(1);
    assert.deepEqual(await request.promise, { ok: false, reason: "transfer_timeout" });
});

test("only progress in the exact endpoint and current generation renews the load deadline", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const request = requests.request("request-a", "canvas", "canvas-a");
    requests.structure("canvas-a", begin(2));
    t.mock.timers.tick(10000);
    requests.structure("canvas-a", { ...begin(2), op: "structure_data_chunk" });
    t.mock.timers.tick(10000);
    requests.structure("canvas-b", begin(3));
    requests.structure("canvas-a", begin(1));
    requests.structure("canvas-a", { ...complete, generation: 1 });
    requests.structure("canvas-a", { ...complete, generation: 2, stream_id: "foreign-stream" });
    t.mock.timers.tick(19999);
    assert.equal(requests.has("canvas"), true);
    t.mock.timers.tick(1);
    assert.deepEqual(await request.promise, { ok: false, reason: "transfer_timeout" });
});

test("applied molecular completion starts a fresh bounded response wait", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const request = requests.request("request-a", "canvas", "canvas-a");
    requests.structure("canvas-a", begin());
    t.mock.timers.tick(10000);
    requests.structure("canvas-a", complete);
    t.mock.timers.tick(4999);
    assert.equal(requests.has("canvas"), true);
    t.mock.timers.tick(1);
    assert.deepEqual(await request.promise, { ok: false, reason: "request_timeout" });
});

test("JSON fallback has an application deadline and completion releases its response wait", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const request = requests.request("request-a", "canvas", "canvas-a");
    requests.structure("canvas-a", begin());
    requests.structure("canvas-a", { ...begin(), op: "structure_data_cancel" });
    requests.structure("canvas-a", { op: "load_molsys_payload" });
    t.mock.timers.tick(6000);
    assert.equal(requests.has("canvas"), true);
    requests.structure("canvas-a", { event: "structure_data_json_complete" });
    requests.resolve("request-a", []);
    assert.deepEqual(await request.promise, { ok: true, messages: [] });
});

test("molecular progress never extends an independent panel's response deadline", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const canvas = requests.request("canvas-request", "canvas", "canvas-a");
    const panel = requests.request("panel-request", "panel", "panel-a");
    requests.structure("panel-a", begin());
    requests.structure("canvas-a", begin());
    t.mock.timers.tick(5000);
    assert.deepEqual(await panel.promise, { ok: false, reason: "request_timeout" });
    assert.equal(requests.has("canvas"), true);
    requests.dispose();
    assert.deepEqual(await canvas.promise, { ok: false, reason: "disposed" });
});

test("endpoint cancellation and widget disposal retire requests and all owned timers", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const canvas = requests.request("canvas-request", "canvas", "canvas-a");
    const panel = requests.request("panel-request", "panel", "panel-a");
    requests.structure("canvas-a", begin());
    requests.cancel("canvas");
    assert.deepEqual(await canvas.promise, { ok: false, reason: "cancelled" });
    assert.equal(canvas.isCurrent(), false);
    requests.dispose();
    assert.deepEqual(await panel.promise, { ok: false, reason: "disposed" });
    assert.equal(panel.isCurrent(), false);
    t.mock.timers.tick(60000);
    assert.equal(requests.has("canvas"), false);
    assert.equal(requests.has("panel"), false);
    assert.deepEqual(await requests.request("later", "canvas", "canvas-a").promise, { ok: false, reason: "disposed" });
});

test("a replaced request cannot resolve or report failure for its successor", async t => {
    t.mock.timers.enable({ apis: ["setTimeout"] });
    const requests = new PopupSceneSnapshots();
    const old = requests.request("old", "canvas", "canvas-old");
    const current = requests.request("new", "canvas", "canvas-new");
    assert.deepEqual(await old.promise, { ok: false, reason: "superseded" });
    assert.equal(old.isCurrent(), false);
    requests.resolve("old", []);
    assert.equal(requests.has("canvas"), true);
    requests.resolve("new", []);
    assert.deepEqual(await current.promise, { ok: true, messages: [] });
    assert.equal(current.isCurrent(), true);
});

test("missing send identity or malformed snapshot is a failure, never an empty success", async () => {
    const requests = new PopupSceneSnapshots();
    assert.deepEqual(await requests.request(null, "canvas", "canvas-a").promise, { ok: false, reason: "send_failed" });
    const request = requests.request("request-a", "canvas", "canvas-a");
    requests.resolve("request-a", undefined);
    assert.deepEqual(await request.promise, { ok: false, reason: "invalid_snapshot" });
    requests.dispose();
});
