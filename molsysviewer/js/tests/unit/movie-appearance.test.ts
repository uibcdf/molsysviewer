import assert from "node:assert/strict";
import test from "node:test";
import { compileMovieTimeline } from "../../src/managers/movie-timeline";
import { movieRepresentationTypes } from "../../src/managers/movie-appearance";
import oracle from "../fixtures/movie-appearance-oracle.json";

test("complete Python scene recipes admit empty colour-layer records but reject nonempty ones", () => {
    const recipe: any = structuredClone(oracle.recipe);
    recipe.baseline.scene.whole.color_layer = {};
    for (const expected of oracle.samples) compare(compileMovieTimeline(recipe).evaluate(expected.time_ms), expected);
    recipe.baseline.scene.whole.color_layer = { source: "scalar" };
    assert.throws(() => compileMovieTimeline(recipe), /per-atom colour layer/);
});

test("observed environments retain declared intent without changing logical evaluation", () => {
    const recipe: any = structuredClone(oracle.recipe);
    recipe.baseline.environment_capture = { version: 1, intent: { background: { mode: "dark" } } };
    const timeline = compileMovieTimeline(recipe);
    for (const expected of oracle.samples) compare(timeline.evaluate(expected.time_ms), expected);
    for (const capture of [{ version: true, intent: {} }, { version: 2, intent: {} },
        { version: 1, intent: {}, extra: true }, { version: 1, intent: { lighting: { ambient: 2 } } }]) {
        const invalid = structuredClone(recipe); invalid.baseline.environment_capture = capture;
        assert.throws(() => compileMovieTimeline(invalid));
    }
    delete recipe.baseline.scene.environment.lighting.diffuse;
    assert.throws(() => compileMovieTimeline(recipe), /both lighting/);
});

function compare(actual: any, expected: any) {
    if (typeof expected === "number") {
        assert.ok(Number.isFinite(actual) && Math.abs(actual - expected) < 1e-12, `${actual} != ${expected}`);
    } else if (expected && typeof expected === "object") {
        assert.deepEqual(Object.keys(actual), Object.keys(expected));
        for (const key of Object.keys(expected)) compare(actual[key], expected[key]);
    } else assert.equal(actual, expected);
}

test("appearance, text and lighting agree with real Python evaluation at arbitrary/reversed times", () => {
    const timeline = compileMovieTimeline(oracle.recipe);
    for (const expected of oracle.samples) compare(timeline.evaluate(expected.time_ms), expected);
    assert.deepEqual([...movieRepresentationTypes], oracle.representation_types);
});

test("compiled appearance is detached from both recipe and output edits", () => {
    const recipe = structuredClone(oracle.recipe);
    const timeline = compileMovieTimeline(recipe);
    const expected = timeline.evaluate(500);
    recipe.baseline.scene.environment.lighting.ambient = 0.99;
    recipe.tracks.length = 0;
    const sample = timeline.evaluate(500);
    sample.appearance!.length = 0;
    assert.deepEqual(timeline.evaluate(500), expected);
});

test("ambiguous properties, unsupported geometry and implicit scene defaults are refused", () => {
    const recipe = structuredClone(oracle.recipe);
    recipe.tracks.push({ ...recipe.tracks[0], tag: "collision" });
    assert.throws(() => compileMovieTimeline(recipe), /one track/);
    recipe.tracks.pop();
    (recipe.baseline.scene.shapes[0] as any).op = "add_network_links";
    assert.throws(() => compileMovieTimeline(recipe), /sphere/);
    const implicit = structuredClone(oracle.recipe);
    delete (implicit.baseline.scene as any).environment;
    assert.throws(() => compileMovieTimeline(implicit), /baseline/);
});

test("Movie colours interpolate in linear light with independent alpha", () => {
    const sample = compileMovieTimeline(oracle.recipe).evaluate(500);
    assert.equal(sample.appearance!.find(row => row.domain === "whole")!.value, 0xBCBCBC);
    assert.equal(sample.appearance!.find(row => row.domain === "shape" && row.property === "alpha")!.value, 0.5);
});

test("uniform Movie colour refuses a per-atom colour layer on its target", () => {
    const recipe = structuredClone(oracle.recipe);
    (recipe.baseline.scene.whole as any).color_layer = {
        atom_indices: [0, 1], colors: [0xFF0000, 0x0000FF],
    };
    assert.throws(() => compileMovieTimeline(recipe), /per-atom colour layer/);
});

test("serialized appearance rejects invalid values and unknown interpolation without accepting a partial plan", () => {
    for (const [name, value] of [["whole-colour", true], ["whole-colour", -1], ["whole-colour", 0x1000000],
        ["sphere-alpha", NaN], ["sphere-alpha", Infinity], ["sphere-alpha", -0.1],
        ["site-repr", "ribbon"], ["lighting", { ambient: 0.5, specular: 0.5 }], ["caption", 3]] as const) {
        const recipe = structuredClone(oracle.recipe);
        (recipe.tracks.find(row => row.tag === name)!.keys[0] as any).value = value;
        assert.throws(() => compileMovieTimeline(recipe));
    }
    for (const marker of [undefined, "encoded-rgb"]) {
        const recipe: any = structuredClone(oracle.recipe);
        if (marker === undefined) delete recipe.color_interpolation; else recipe.color_interpolation = marker;
        assert.throws(() => compileMovieTimeline(recipe), /interpolation/);
    }
});
