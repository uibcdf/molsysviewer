import assert from "node:assert/strict";
import test from "node:test";

import { scalarColorRangeFromInput } from "../../src/ui/panels/ui-helpers";

test("scalar color controls keep automatic and unit-free ranges", () => {
    assert.equal(scalarColorRangeFromInput("  "), undefined);
    assert.deepEqual(scalarColorRangeFromInput(" 0, 1 "), [0, 1]);
});

test("scalar color controls preserve physical units for Python", () => {
    assert.equal(scalarColorRangeFromInput(" [0,100] angstrom**2 "), "[0,100] angstrom**2");
});

test("invalid scalar color input reaches validation without dropping entries", () => {
    assert.equal(scalarColorRangeFromInput("0,wrong,100"), "0,wrong,100");
    assert.equal(scalarColorRangeFromInput("0,"), "0,");
    assert.equal(scalarColorRangeFromInput("0,Infinity"), "0,Infinity");
});
