import assert from "node:assert/strict";
import test from "node:test";
import { compileMovieTimeline } from "../../src/managers/movie-timeline";
import oracle from "../fixtures/movie-timeline-oracle.json";

function checkSamples(recipe: unknown, samples: typeof oracle.samples) {
    const timeline = compileMovieTimeline(recipe);
    for (const expected of samples) {
        const observed = timeline.evaluate(expected.time_ms);
        assert.equal(observed.time_ms, expected.time_ms);
        assert.equal(observed.structure_index, expected.structure_index);
        assert.deepEqual(observed.visibility, expected.visibility);
        for (const key of ["position", "target", "up"] as const) {
            observed.camera[key].forEach((component, i) => {
                assert.ok(Math.abs(component - expected.camera[key][i]) <= 1e-12,
                    `Camera ${key}[${i}] at ${expected.time_ms} ms: ${component} vs ${expected.camera[key][i]}`);
            });
        }
    }
}

test("Movie time and camera geometry agree with Python on a real three-structure recipe", () => {
    assert.equal(compileMovieTimeline(oracle.recipe).duration_ms, oracle.recipe.duration_ms);
    checkSamples(oracle.recipe, oracle.samples);
});

test("a generic half turn chooses the same arc as Python", () => {
    const { begin, end, sample } = oracle.half_turn;
    checkSamples({
        ...oracle.recipe,
        baseline: { ...oracle.recipe.baseline, camera: begin },
        tracks: [{ tag: "half-turn", target: { domain: "camera" }, property: "pose", keys: [{ time_ms: 1000, value: end }] }],
    }, [sample]);
});

test("compiled Movie owns its inputs and returns detached samples", () => {
    const recipe = structuredClone(oracle.recipe);
    const timeline = compileMovieTimeline(recipe);
    const before = timeline.evaluate(550);
    const output = timeline.evaluate(550);
    recipe.baseline.camera.position[0] = 999;
    recipe.tracks.length = 0;
    output.camera.position[0] = 777;
    output.visibility[0].visible = false;
    assert.deepEqual(timeline.evaluate(550), before);
});

test("Movie compiler rejects invalid times, ambiguous targets and inconsistent source bindings", () => {
    const recipe = structuredClone(oracle.recipe);
    const timeline = compileMovieTimeline(recipe);
    for (const at of [NaN, Infinity, -1, 1201]) assert.throws(() => timeline.evaluate(at), /Movie time/);
    const first = recipe.tracks[0];
    recipe.tracks.push({ ...first, tag: "duplicate-property" });
    assert.throws(() => compileMovieTimeline(recipe), /one track per target property/);
    recipe.tracks.pop();
    recipe.baseline.scene.regions[0].tag = "other";
    assert.throws(() => compileMovieTimeline(recipe), /Unknown Movie visibility target/);
    recipe.baseline.scene.regions[0].tag = "site";
    recipe.baseline.scene.sources.binding.n_structures = 1;
    assert.throws(() => compileMovieTimeline(recipe), /source records do not match/);
});
