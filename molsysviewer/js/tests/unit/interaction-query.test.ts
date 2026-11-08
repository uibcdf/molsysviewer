import assert from "node:assert/strict";
import test from "node:test";
import { ownInteractionQuery } from "../../src/messages/interaction-query";
import { InteractionHandlers, type InteractionSummary } from "../../src/managers/handlers/interaction-handlers";

test("interaction query owners are stamped by the authenticated host", () => {
    const query = { event: "request_interaction_frame", request_id: 1, frame: 2, _query_endpoint_id: "foreign" };
    for (const endpoint of ["widget-host:session", "canvas-popup:session"]) {
        const owned = ownInteractionQuery(query, endpoint);
        assert.equal(owned._query_endpoint_id, endpoint);
        assert.equal(owned.request_id, 1);
        assert.equal(owned.frame, 2);
    }
    assert.equal(query._query_endpoint_id, "foreign");
    const scene = { event: "interaction_context_action", action: "create_interaction" };
    assert.equal(ownInteractionQuery(scene, "canvas-popup:session"), scene);
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
