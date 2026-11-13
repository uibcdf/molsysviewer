import assert from "node:assert/strict";
import test from "node:test";
import { movieWebVisibility } from "../../src/managers/movie-web-player";

const scene = { whole: { visible: false }, layers: [{ tag: "gate", hidden: false }],
    shapes: [{ tag: "visible", layer_tag: "gate", hidden: false }, { tag: "hidden", options: { layer_tag: "gate" }, hidden: true }],
    regions: [{ tag: "region", layer: "gate", hidden: false }] };
const sample = (visible: boolean): any => ({ visibility: [{ domain: "layer", tag: "gate", visible }] });
test("web layer gates preserve baseline member intent at repeated and reversed times", () => {
    for (const visible of [false, true, false, true]) {
        assert.deepEqual(movieWebVisibility(scene, sample(visible)), [
            { domain: "region", tag: "region", visible }, { domain: "shape", tag: "visible", visible },
            { domain: "shape", tag: "hidden", visible: false }]);
    }
});
test("member tracks remain independent of a gate and closed gates win", () => {
    const row: any = sample(false); row.visibility.push({ domain: "shape", tag: "hidden", visible: true });
    assert.equal(movieWebVisibility(scene, row).find(item => item.tag === "hidden")!.visible, false);
    row.visibility[0].visible = true;
    assert.equal(movieWebVisibility(scene, row).find(item => item.tag === "hidden")!.visible, true);
});
test("an initially hidden layer admits its untracked members when explicitly opened", () => {
    assert.ok(movieWebVisibility({ ...scene, layers: [{ tag: "gate", hidden: true }] }, sample(true)).every(row => row.visible));
});
test("appearance rebuilds retain untracked hidden targets including Whole", () => {
    const row: any = { visibility: [], appearance: [{ domain: "whole", tag: null, property: "color", value: 0 },
        { domain: "shape", tag: "hidden", property: "color", value: 0 }] };
    assert.deepEqual(movieWebVisibility(scene, row), [
        { domain: "whole", tag: null, visible: false }, { domain: "shape", tag: "hidden", visible: false }]);
});
