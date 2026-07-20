import assert from "node:assert";
import test from "node:test";

import { nextPlaybackStep, normalizePlaybackMode } from "../../src/managers/handlers/trajectory-handlers";

// `mode` was accepted by playTrajectory and then never read: playback always
// advanced through Mol*'s wrap-around, so "loop" worked by accident while "once"
// never stopped and "palindrome" never bounced. On top of that, Python's public
// API says "ping-pong" while the frontend calls it "palindrome", so the mode was
// dropped even when supplied.

test("the public ping-pong spelling maps to the frontend's palindrome", () => {
    assert.strictEqual(normalizePlaybackMode("ping-pong"), "palindrome");
    assert.strictEqual(normalizePlaybackMode("palindrome"), "palindrome");
});

test("unknown or missing modes fall back to loop", () => {
    assert.strictEqual(normalizePlaybackMode(undefined), "loop");
    assert.strictEqual(normalizePlaybackMode(null), "loop");
    assert.strictEqual(normalizePlaybackMode("turbo"), "loop");
    assert.strictEqual(normalizePlaybackMode("loop"), "loop");
    assert.strictEqual(normalizePlaybackMode("once"), "once");
});

test("loop wraps around at either end", () => {
    assert.deepStrictEqual(nextPlaybackStep(3, 1, 10, "loop"), { index: 4, delta: 1, stop: false });
    // past the last frame it returns to the beginning
    assert.deepStrictEqual(nextPlaybackStep(9, 1, 10, "loop"), { index: 0, delta: 1, stop: false });
    // and backwards past the first frame it lands on the last
    assert.deepStrictEqual(nextPlaybackStep(0, -1, 10, "loop"), { index: 9, delta: -1, stop: false });
});

test("once stops at the end instead of running forever", () => {
    assert.deepStrictEqual(nextPlaybackStep(5, 1, 10, "once"), { index: 6, delta: 1, stop: false });
    assert.deepStrictEqual(nextPlaybackStep(9, 1, 10, "once"), { index: 9, delta: 1, stop: true });
    // playing backwards, it stops on the first frame
    assert.deepStrictEqual(nextPlaybackStep(0, -1, 10, "once"), { index: 0, delta: -1, stop: true });
});

test("palindrome bounces off both ends and reverses travel", () => {
    // mid-trajectory it just advances
    assert.deepStrictEqual(nextPlaybackStep(4, 1, 10, "palindrome"), { index: 5, delta: 1, stop: false });
    // at the last frame it turns around
    assert.deepStrictEqual(nextPlaybackStep(9, 1, 10, "palindrome"), { index: 8, delta: -1, stop: false });
    // and at the first frame it turns around again
    assert.deepStrictEqual(nextPlaybackStep(0, -1, 10, "palindrome"), { index: 1, delta: 1, stop: false });
});

test("palindrome bounce respects the step size", () => {
    // stepping by 3 from frame 8 of 10 overshoots, so it reverses by 3
    assert.deepStrictEqual(nextPlaybackStep(8, 3, 10, "palindrome"), { index: 5, delta: -3, stop: false });
});

test("a degenerate trajectory stops instead of dividing by its length", () => {
    assert.deepStrictEqual(nextPlaybackStep(0, 1, 0, "loop"), { index: 0, delta: 1, stop: true });
});
