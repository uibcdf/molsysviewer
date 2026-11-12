import assert from "node:assert/strict";
import test from "node:test";
import { compileMovieTimeline } from "../../src/managers/movie-timeline";
import { MoviePreviewClock } from "../../src/managers/movie-preview-clock";
import oracle from "../fixtures/movie-timeline-oracle.json";
import cartesian from "../fixtures/movie-cartesian-oracle.json";

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

test("explicit Cartesian camera chords match independent affine controls and Python", () => {
    for (const entry of cartesian.valid) {
        const recipe = { ...oracle.recipe, camera_interpolation: "cartesian-constant-up@1",
            baseline: { ...oracle.recipe.baseline, camera: entry.begin },
            tracks: [{ tag: "camera", target: { domain: "camera" }, property: "pose", keys: entry.keys }] };
        const compiled = compileMovieTimeline(recipe);
        for (const expected of entry.samples) {
            const observed = compiled.evaluate(expected.time_ms);
            observed.camera.position.forEach((value, i) =>
                assert.ok(Math.abs(value - expected.position[i]) <= 1e-12));
            const expectedTarget = ("target" in expected ? expected.target : undefined) ?? entry.begin.target;
            observed.camera.target.forEach((value, i) =>
                assert.ok(Math.abs(value - expectedTarget[i]) <= 1e-12));
            observed.camera.up.forEach((value, i) =>
                assert.ok(Math.abs(value - [0, 1, 0][i]) <= 4 * Number.EPSILON));
        }
        const before = compiled.evaluate(500);
        recipe.tracks.length = 0;
        before.camera.position[0] = 999;
        assert.notEqual(compiled.evaluate(500).camera.position[0], 999);
    }
});

test("Cartesian admission checks the entire segment, including unsampled degeneracy", () => {
    const begin = cartesian.valid[0].begin;
    const recipe = { ...oracle.recipe, camera_interpolation: "cartesian-constant-up@1",
        baseline: { ...oracle.recipe.baseline, camera: begin }, tracks: [] as unknown[] };
    for (const [end, message] of [
        [{ ...begin, position: [0, 0, -22] }, /unsafe viewing direction/],
        [{ ...begin, position: [0, 4, -22] }, /unsafe viewing direction/],
        [{ ...begin, position: [10, 0, 0], up: [0, 0, 1] }, /constant up vector/],
    ] as const) {
        recipe.tracks = [{ tag: "camera", target: { domain: "camera" }, property: "pose",
            keys: [{ time_ms: 1000, value: end }] }];
        assert.throws(() => compileMovieTimeline(recipe), message);
    }
    for (const mode of [null, true, 1, "cartesian", "unknown", {}]) {
        assert.throws(() => compileMovieTimeline({ ...recipe, camera_interpolation: mode }), /camera interpolation/);
    }
});

test("Cartesian zero keys override the baseline and subnormal chords remain finite", () => {
    const begin = cartesian.valid[0].begin;
    const end = { ...begin, position: [10, 0, 0] };
    const recipe = { ...oracle.recipe, camera_interpolation: "cartesian-constant-up@1",
        baseline: { ...oracle.recipe.baseline, camera: { ...begin, up: [1, 0, 0] } },
        tracks: [{ tag: "camera", target: { domain: "camera" }, property: "pose",
            keys: [{ time_ms: 0, value: begin }, { time_ms: 1000, value: end }] }] };
    assert.deepEqual(compileMovieTimeline(recipe).evaluate(500).camera.position, [5, 0, 5]);
    recipe.tracks[0].keys = [{ time_ms: 1000, value: end }];
    assert.throws(() => compileMovieTimeline(recipe), /constant up vector/);
    recipe.baseline.camera = { ...begin, position: [0, 0, 1e-320] };
    recipe.tracks[0].keys = [{ time_ms: 1000, value: { ...begin, position: [1e-320, 0, 0] } }];
    assert.deepEqual(compileMovieTimeline(recipe).evaluate(500).camera.position, [5e-321, 0, 5e-321]);
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

test("Movie import provenance is checked, detached and has no effect on evaluation", () => {
    const recipe = structuredClone(oracle.recipe);
    const reference = { domain: "region", tag: "site" };
    const provenance = {
        schema: "molsysviewer.movie_import@1", source_sha256: "sha256:" + "0".repeat(64), source_version: 2,
        source_binding: recipe.baseline.binding,
        target_map: [{ source: reference, target: reference }], structure_index_map: [2, 0, 1],
        warnings: ["molecular_binding_rebound"], targets: [{ track: "show-site", source: reference, target: reference,
            source_identity: { uid: "old" }, target_identity: { uid: "new" } }],
    };
    const withHistory = { ...recipe, provenance };
    const compiled = compileMovieTimeline(withHistory);
    assert.deepEqual(compiled.evaluate(550), compileMovieTimeline(recipe).evaluate(550));
    provenance.targets[0].source_identity.uid = "user-edit";
    assert.deepEqual(compiled.evaluate(550), compileMovieTimeline(recipe).evaluate(550));
    for (const [field, value] of [
        ["schema", "unknown"], ["source_sha256", "sha256:bad"], ["source_version", true],
        ["source_binding", { ...provenance.source_binding, n_atoms: true }], ["target_map", {}],
        ["target_map", [provenance.target_map[0], provenance.target_map[0]]],
        ["structure_index_map", [0]], ["structure_index_map", [0, true, 2]],
        ["warnings", [true]], ["targets", [{ command: "untrusted" }]],
        ["targets", [{ ...provenance.targets[0], target_identity: { op: 2 } }]],
        ["targets", [provenance.targets[0], provenance.targets[0]]],
    ]) {
        assert.throws(() => compileMovieTimeline({ ...recipe, provenance: { ...provenance, [field as string]: value } }),
            /Movie|movie/);
    }
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

test("Movie preview samples renderer time, wraps or finishes, and retires the old clock", () => {
    const clock = new MoviePreviewClock();
    const loop = clock.prepare({ id: "loop", recipe: oracle.recipe, start_time_ms: 700, loop: true }, 1000);
    assert.equal(loop(1100).time_ms, 800);
    assert.equal(clock.prepare({ id: "loop" })(1700).time_ms, 200);
    assert.equal(loop(1700).visibility.length, 2);
    const once = clock.prepare({ id: "once", recipe: oracle.recipe, start_time_ms: 1000, loop: false }, 2000);
    assert.throws(() => loop(2200), /replaced before its draw/);
    assert.equal(once(2600).time_ms, oracle.recipe.duration_ms);
    clock.release("loop");
    assert.equal(once(2600).time_ms, oracle.recipe.duration_ms);
    clock.release("once");
    assert.throws(() => clock.prepare({ id: "once" }), /no longer current/);
});
