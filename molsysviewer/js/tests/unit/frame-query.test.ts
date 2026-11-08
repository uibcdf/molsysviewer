import assert from "node:assert/strict";
import test from "node:test";
import { ownFrameQuery, dynamicRegionReplyAction } from "../../src/messages/frame-query";
import { InteractionHandlers, type InteractionSummary } from "../../src/managers/handlers/interaction-handlers";

test("frame query owners are stamped by the authenticated host", () => {
    for (const event of ["request_interaction_frame", "request_dynamic_region_evaluation"]) {
        const query = { event, request_id: 1, frame: 2, _query_endpoint_id: "foreign" };
        for (const endpoint of ["widget-host:session", "canvas-popup:session"]) {
            const owned = ownFrameQuery(query, endpoint);
            assert.equal(owned._query_endpoint_id, endpoint);
            assert.equal(owned.request_id, 1);
            assert.equal(owned.frame, 2);
        }
        assert.equal(query._query_endpoint_id, "foreign");
    }
    const scene = { event: "interaction_context_action", action: "create_interaction" };
    assert.equal(ownFrameQuery(scene, "canvas-popup:session"), scene);
});

test("dynamic replies reject foreign IDs and distinguish obsolete frames from current geometry", () => {
    assert.equal(dynamicRegionReplyAction({ frame: 2, request_id: 9 }, 2, 2, 9), "apply");
    assert.equal(dynamicRegionReplyAction({ frame: 2, request_id: 9 }, 1, 2, 9), "complete");
    assert.equal(dynamicRegionReplyAction({ frame: 2, request_id: 8 }, 2, 2, 9), "ignore");
    assert.equal(dynamicRegionReplyAction({ frame: 1, request_id: 9 }, 1, 2, 9), "ignore");
    assert.equal(dynamicRegionReplyAction({ frame: 2, request_id: 9 }, 2, null, null), "ignore");
});

test("uncorrelated dynamic scene edits apply only to their actual current frame", () => {
    assert.equal(dynamicRegionReplyAction({ frame: 2 }, 2, 2, 9), "project");
    assert.equal(dynamicRegionReplyAction({ frame: 1 }, 2, 2, 9), "ignore");
    for (const frame of [undefined, -1, 0.5, Number.NaN, Number.POSITIVE_INFINITY]) {
        assert.equal(dynamicRegionReplyAction({ frame }, 2, null, null), "ignore");
    }
});

test("panel summaries retain revision guards without requesting invisible geometry", () => {
    const sent: unknown[] = [];
    const handler = new InteractionHandlers({} as any, {
        register() {}, unregister() {}, notify: message => sent.push(message),
        summaries() {}, layerHidden: () => false,
    });
    // Only the protocol fields consulted by setSummaries are needed here;
    // native scientific geometry is checked by the real browser receiving.
    const items = [{ tag: "hb", frame: 2, projection_revision: 7 }] as InteractionSummary[];
    assert.equal(handler.setSummaries(items, 7, false), true);
    assert.equal(handler.setSummaries(items, 6, false), false);
    assert.deepEqual(sent, []);
    assert.equal(handler.setSummaries(items, 7), true);
    assert.deepEqual(sent, [{ event: "request_interaction_frame", frame: 0, request_id: 1 }]);
    handler.clear();
});

test("interaction queries overlap one old frame without building an unbounded request queue", () => {
    const sent: any[] = [];
    const handler = new InteractionHandlers({} as any, {
        register() {}, unregister() {}, notify: message => sent.push(message),
        summaries() {}, layerHidden: () => false,
    });
    try {
        handler.setSummaries([{ tag: "hb", frame: 0, projection_revision: 7 }] as InteractionSummary[], 7);
        handler.onFrame(1); handler.onFrame(2); handler.onFrame(0);
        assert.deepEqual(sent.map(message => message.frame), [1, 2]);
        handler.finishResponse(999);
        assert.equal(sent.length, 2);
        handler.finishResponse(1);
        assert.deepEqual(sent.map(message => message.frame), [1, 2, 0]);
        handler.finishResponse(2);
        assert.equal(sent.length, 3, "an old completion cannot restart the current request");
    } finally { handler.clear(); }
});

test("a replacement interaction revision invalidates old queries without reusing their identities", () => {
    const sent: any[] = [];
    const handler = new InteractionHandlers({} as any, {
        register() {}, unregister() {}, notify: message => sent.push(message),
        summaries() {}, layerHidden: () => false,
    });
    try {
        handler.setSummaries([{ tag: "hb", frame: 2, projection_revision: 7 }] as InteractionSummary[], 7);
        handler.setSummaries([{ tag: "hb", frame: 2, projection_revision: 8 }] as InteractionSummary[], 8);
        assert.deepEqual(sent.map(message => message.request_id), [1, 2]);
        handler.finishResponse(1);
        assert.equal((handler as any).pending, 2);
        assert.equal(sent.length, 2);
        handler.clear();
        handler.setSummaries([{ tag: "hb", frame: 2, projection_revision: 8 }] as InteractionSummary[], 8);
        assert.equal(sent.at(-1).request_id, 3);
    } finally { handler.clear(); }
});
