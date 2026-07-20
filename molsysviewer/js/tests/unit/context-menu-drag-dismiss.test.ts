import assert from "node:assert";
import test from "node:test";

import { MolSysViewerController } from "../../src/managers/viewer-controller";

// The gesture decision is pure geometry, so it can be exercised without a
// browser. Right-dragging pans the structure in Mol*, but the browser fires
// `contextmenu` on button press, so the menu opens before a click can be told
// apart from a drag; the menu is dismissed once this threshold is crossed.
const controller: any = Object.create(MolSysViewerController.prototype);
const exceeds = (anchor: { x: number; y: number }, x: number, y: number) =>
    controller.exceedsContextMenuDragThreshold(anchor, x, y);

const ANCHOR = { x: 100, y: 100 };

test("a still right-click does not count as a drag", () => {
    assert.strictEqual(exceeds(ANCHOR, 100, 100), false);
});

test("small jitter still counts as a click, not a drag", () => {
    // a shaky hand must not dismiss the menu
    assert.strictEqual(exceeds(ANCHOR, 103, 100), false);
    assert.strictEqual(exceeds(ANCHOR, 100, 104), false);
    assert.strictEqual(exceeds(ANCHOR, 103, 103), false);
});

test("clear movement counts as a drag and dismisses the menu", () => {
    assert.strictEqual(exceeds(ANCHOR, 120, 100), true);
    assert.strictEqual(exceeds(ANCHOR, 100, 80), true);
    assert.strictEqual(exceeds(ANCHOR, 90, 90), true);
});

test("the threshold is measured radially, not per axis", () => {
    // 4px on each axis is ~5.66px of travel: a drag, even though neither axis
    // alone crosses the threshold
    assert.strictEqual(exceeds(ANCHOR, 104, 104), true);
});
