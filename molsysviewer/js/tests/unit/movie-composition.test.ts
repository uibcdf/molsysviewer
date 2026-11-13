import assert from "node:assert/strict";
import test from "node:test";
import { overlayDescriptor, overlaySnapshot, positionOverlay } from "../../src/ui/movie-overlay-composition";

test("Movie overlay projection preserves aspect ratio on different viewport shapes", () => {
    assert.deepEqual(positionOverlay({ x: 800, y: 20, width: 100, height: 40 }, { width: 1000, height: 800 }, 1280, 720),
        { x: 1043, y: 18, width: 90, height: 36 });
    assert.deepEqual(positionOverlay({ x: 10, y: 20, width: 100, height: 40 }, { width: 1000, height: 800 }, 500, 400),
        { x: 5, y: 10, width: 50, height: 20 });
});
test("Movie composition refuses invalid bounds and excessive vector assets", () => {
    for (const x of [-2, Number.NaN, Number.POSITIVE_INFINITY, 950]) {
        assert.throws(() => positionOverlay({ x, y: 0, width: 100, height: 40 }, { width: 1000, height: 800 }, 640, 360));
    }
    const row = { kind: "colour_legend" as const, tag: "legend", bounds: { x: 0, y: 0, width: 100, height: 40 }, svg: "<svg/>",
        rendering: { opacity: 1, view_box: { width: 100, height: 40 } } };
    assert.throws(() => overlaySnapshot({ width: 1000, height: 800 }, Array(33).fill(row), 640, 360));
    const result = overlaySnapshot({ width: 1000, height: 800 }, [row], 640, 360);
    assert.equal(overlayDescriptor(result).layers.length, 1);
    assert.equal("svg" in overlayDescriptor(result).layers[0], false, "frame metadata must not copy SVG assets");
});
