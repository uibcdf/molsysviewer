import assert from "node:assert/strict";
import test from "node:test";
import { CapturePresentationFence } from "../../src/managers/capture-presentation";

test("native presentation retains a ready prefix while incomplete scientific replies remain runnable", async () => {
    const fence = new CapturePresentationFence();
    let drawn!: () => void;
    const nativeDraw = new Promise<void>(resolve => { drawn = resolve; });
    assert.equal(fence.isPending, false);
    fence.retain(nativeDraw);
    assert.equal(fence.isPending, true);
    await fence.afterSceneMessage(() => false);
    let presented = false;
    const prefix = fence.afterSceneMessage(() => true).then(() => { presented = true; });
    await Promise.resolve();
    assert.equal(presented, false);
    drawn(); await prefix;
    assert.equal(presented, true);
    assert.equal(fence.isPending, false);
});

test("failed, cancelled and disposed captures release only their own presentation reservations", async () => {
    const fence = new CapturePresentationFence();
    let fail!: (reason: Error) => void;
    const first = new Promise<void>((_resolve, reject) => { fail = reject; });
    const second = new Promise<void>(() => {});
    fence.retain(first);
    const cancel = fence.retain(second);
    fail(new Error("native capture expired"));
    await first.catch(() => {});
    assert.equal(fence.isPending, true);
    cancel(); cancel();
    assert.equal(fence.isPending, false);
    fence.retain(second);
    const waiting = fence.afterSceneMessage(() => true);
    fence.dispose(); await waiting;
    assert.equal(fence.isPending, false);
    fence.retain(second);
    assert.equal(fence.isPending, false, "A disposed owner cannot resume playback retention.");
});
