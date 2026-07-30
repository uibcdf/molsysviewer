import assert from "node:assert/strict";
import test from "node:test";

import { PopupReplayLog } from "../../src/messages/popup-replay-log";
import type { ViewerMessage } from "../../src/messages/viewer-messages";

function message(op: string, extra: Record<string, unknown> = {}): ViewerMessage {
    return { op, ...extra } as ViewerMessage;
}

test("popup replay keeps only the current molecular generation", () => {
    const replay = new PopupReplayLog();
    replay.record(message("load_molsys_payload", { label: "old" }));
    replay.record(message("hide_whole", { target: "whole" }));
    replay.record(message("load_molsys_payload", { label: "current" }));
    replay.record(message("show_whole", { target: "whole" }));

    assert.deepEqual(replay.snapshot("canvas"), [
        message("load_molsys_payload", { label: "current" }),
        message("show_whole", { target: "whole" }),
    ]);
});

test("popup replay coalesces high-frequency current-state projections", () => {
    const replay = new PopupReplayLog([
        message("load_molsys_payload"),
    ]);
    for (let index = 0; index < 1000; index += 1) {
        replay.record(message("set_trajectory_frame", { index }));
        replay.record(message("set_shape_summaries", { index }));
    }

    assert.equal(replay.size, 3);
    assert.deepEqual(replay.snapshot("canvas").slice(1), [
        message("set_trajectory_frame", { index: 999 }),
        message("set_shape_summaries", { index: 999 }),
    ]);
});

test("panel popup bootstrap contains only explicit UI projections", () => {
    const replay = new PopupReplayLog([
        message("load_molsys_payload", { payload: { structures: [] } }),
        message("partial_coordinates_update", { coordinates: [1, 2, 3] }),
        message("set_whole_representation", { representation: "cartoon" }),
        message("set_region_summaries", { regions: [] }),
    ]);

    assert.deepEqual(replay.snapshot("panel"), [
        message("set_region_summaries", { regions: [] }),
    ]);
});
