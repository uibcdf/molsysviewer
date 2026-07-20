import assert from "node:assert";
import test from "node:test";

import {
    MsvPerAtomColorThemeProvider,
    clearPerAtomColors,
    setPerAtomColors,
} from "../../src/themes/per-atom-color";

// Mol*'s type guards are shape checks (`kind === 'element-location'` /
// `'bond-location'`), so locations can be built directly here.
function elementLocation(unit: any, element: number): any {
    return { kind: "element-location", unit, element };
}

function bondLocation(aUnit: any, aIndex: number): any {
    return { kind: "bond-location", aUnit, aIndex, bUnit: aUnit, bIndex: aIndex + 1 };
}

function makeTheme() {
    return MsvPerAtomColorThemeProvider.factory(
        {} as any,
        MsvPerAtomColorThemeProvider.defaultValues,
    );
}

// A unit whose element array is NOT the identity — this is the multi-chain case
// (Mol* builds one unit per chain), where a positional lookup would go wrong.
const UNIT = { elements: [5, 6, 7] };

test("per-atom theme colors an atom using the model-level element index", () => {
    clearPerAtomColors();
    setPerAtomColors([7], [0xabcdef], true);

    const theme = makeTheme();
    // `element` is a model-level ElementIndex. Treating it as a position into
    // `unit.elements` (the previous behavior) would miss and fall back to the
    // base theme, which is what broke coloring on non-first chains.
    assert.strictEqual(theme.color(elementLocation(UNIT, 7), false), 0xabcdef);
});

test("per-atom theme colors a bond from its first atom", () => {
    clearPerAtomColors();
    setPerAtomColors([7], [0xabcdef], true);

    const theme = makeTheme();
    // aIndex 2 → UNIT.elements[2] === 7. Without the Bond branch every bond
    // fell back to the base theme, making per-atom colors invisible on
    // ball-and-stick / licorice representations.
    assert.strictEqual(theme.color(bondLocation(UNIT, 2), false), 0xabcdef);
});

test("per-atom theme leaves uncolored atoms to the base theme", () => {
    clearPerAtomColors();
    setPerAtomColors([7], [0xabcdef], true);

    const theme = makeTheme();
    // element 6 has no entry, so it must not receive the mapped color
    assert.notStrictEqual(theme.color(elementLocation(UNIT, 6), false), 0xabcdef);
});
