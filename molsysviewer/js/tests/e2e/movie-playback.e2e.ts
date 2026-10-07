import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_TEXT = `
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
`;

/**
 * Browser observation for movie playback (uibcdf/molsysviewer#65).
 *
 * Playback only, and deliberately: export depends on an external encoder and the
 * capability audit already records that it is not exercised in CI.
 *
 * What makes this worth a browser is that playback is a `requestAnimationFrame`
 * loop. Nothing in a headless harness that draws once when idle can tell a moving
 * camera from a stationary one, and `play_movie` returns immediately either way --
 * so the assertions here are about the camera having actually been somewhere else,
 * and about the run having ended where the last keyframe said.
 */
async function run() {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1280, height: 900 });

    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));
    page.on("console", msg => {
        if (msg.type() === "error") errors.push(msg.text());
    });

    const harnessPath = resolve(__dirname, "harness.bundle.js");
    await page.setContent(
        `<!doctype html><html><body><div id="root" style="width: 800px; height: 600px;"></div></body></html>`,
        { waitUntil: "networkidle" },
    );
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => !!(window as any).Harness, { timeout: 30000 });

    const result = await page.evaluate(async pdb => {
        const w = window as any;
        let atCompletion: number[] | null = null;
        const controller = await w.Harness.createController("root", undefined, (message: any) => {
            if (message?.event === "movie_playback_done" && !atCompletion) atCompletion = pos();
        });
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "movie",
        });

        const pos = (): number[] | null => {
            const snap = controller.getCameraSnapshot();
            return snap?.position ? Array.from(snap.position as ArrayLike<number>) : null;
        };
        const key = () => JSON.stringify(pos());

        // Wait for Mol*'s own post-load framing to finish before touching the camera.
        // It lands asynchronously and *overwrites* whatever the movie has set: without
        // this wait the suite reads the auto-focus position and reports that playback
        // never moved anything, which is a race in the test rather than a defect.
        let previous = "";
        let stable = 0;
        for (let i = 0; i < 120 && stable < 5; i++) {
            await new Promise(r => setTimeout(r, 50));
            const current = key();
            stable = current === previous ? stable + 1 : 0;
            previous = current;
        }
        const settled = pos();

        const keyframes = [
            { time_ms: 0, camera: { position: [0, 0, 60], target: [0, 0, 0], up: [0, 1, 0] } },
            { time_ms: 900, camera: { position: [60, 0, 0], target: [0, 0, 0], up: [0, 1, 0] } },
        ];

        const sample = async (ms: number, every: number) => {
            const seen: number[][] = [];
            for (let elapsed = 0; elapsed < ms; elapsed += every) {
                await new Promise(r => setTimeout(r, every));
                const p = pos();
                if (!p) continue;
                if (!seen.length || JSON.stringify(p) !== JSON.stringify(seen[seen.length - 1])) seen.push(p);
            }
            return seen;
        };

        await controller.handleMessage({ op: "play_movie", keyframes, loop: false });
        const during = await sample(1200, 30);

        // Mol* applies camera snapshots asynchronously. Playback completion is
        // signalled only once its final snapshot has landed, not at a fixed wall time.
        const hasDone = () => ((w.__messages ?? []) as any[]).some(m => m?.event === "movie_playback_done");
        for (let i = 0; i < 200 && !hasDone(); i++) {
            await new Promise(r => setTimeout(r, 50));
        }
        const done = hasDone();
        const after = pos();

        // A second run, interrupted: it must stop where it was, short of the end.
        await controller.handleMessage({ op: "play_movie", keyframes, loop: false });
        // Observe an applied intermediate camera, rather than assuming that 300 ms
        // of wall time implies a draw on a busy native/software renderer.
        let observedPlayback = false;
        for (let i = 0; i < 200; i++) {
            const current = pos();
            if (current && current[0] > 5 && current[0] < 55 && current[2] > 5) {
                observedPlayback = true;
                break;
            }
            await new Promise(r => requestAnimationFrame(r));
        }
        if (!observedPlayback) throw new Error("Interrupted movie never displayed an intermediate camera.");
        await controller.handleMessage({ op: "stop_movie" });
        const atStop = pos();
        await new Promise(r => setTimeout(r, 700));
        const afterStop = pos();

        // Reproduce the command/draw boundary deterministically with real Mol*:
        // its animation loop is paused while the movie's own rAF submits a reset.
        const beforePausedPlayback = pos();
        controller.plugin.animationLoop.stop({ noDraw: true });
        await controller.handleMessage({ op: "play_movie", keyframes: [
            keyframes[0], { ...keyframes[1], time_ms: 10000 },
        ], loop: false });
        await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
        await Promise.resolve();
        const submittedTime = controller.movie.lastMovieTime;
        const pendingPromises = controller.movie.cameraWrites.size;
        let stoppedWhilePaused = false;
        const stopping = controller.handleMessage({ op: "stop_movie" }).then(() => { stoppedWhilePaused = true; });
        // Observe settlement before restarting Mol*; a resolved camera command
        // alone must not let stop finish while its applied draw is still blocked.
        await new Promise(r => setTimeout(r, 50));
        const earlyStop = stoppedWhilePaused;
        controller.plugin.animationLoop.start();
        await stopping;
        const pausedAtStop = pos();
        await new Promise(r => setTimeout(r, 200));
        const pausedAfterStop = pos();

        return { settled, during, after, done, atCompletion, atStop, afterStop,
            beforePausedPlayback, submittedTime, pendingPromises, earlyStop, pausedAtStop, pausedAfterStop };
    }, PDB_TEXT);

    const dist = (a: number[] | null, b: number[] | null) => {
        assert.ok(a && b, "Expected a camera snapshot at every sample point");
        return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    };

    assert.ok(result.done, "play_movie never reported movie_playback_done");

    const end = [60, 0, 0];
    assert.ok(
        dist(result.atCompletion, end) < 1e-6,
        `Completion preceded the final camera draw: ${JSON.stringify(result.atCompletion)}`,
    );

    // Interpolation is the thing only a browser can see. A runtime that jumped
    // straight to the last keyframe, or that applied nothing until the final tick,
    // still ends in the right place and still reports done -- so the count of
    // distinct positions is the assertion that separates playing from arriving.
    assert.ok(
        result.during.length >= 3,
        `Expected the camera to pass through intermediate positions, saw ${result.during.length}: ` +
            JSON.stringify(result.during),
    );
    assert.ok(
        dist(result.during[0], result.settled) < 1e-6 || dist(result.during[0], end) > 1,
        "The first sample was already the last keyframe, so nothing was interpolated",
    );

    // And it landed exactly where the last keyframe said.
    assert.ok(
        dist(result.after, end) < 1,
        `Playback did not finish on the last keyframe: ${JSON.stringify(result.after)}`,
    );

    // stop_movie stops it: short of the end, and not still travelling afterwards.
    assert.ok(
        dist(result.afterStop, end) > 1,
        "stop_movie left the camera on the final keyframe, so nothing was interrupted",
    );
    const drift = dist(result.atStop, result.afterStop);
    assert.ok(
        drift < 1e-6,
        `Camera kept travelling after stop_movie: moved ${drift}, ${JSON.stringify(result.atStop)} -> ` +
            JSON.stringify(result.afterStop),
    );
    assert.ok(result.submittedTime > 0 && result.submittedTime < 10000, "paused scenario submitted no movie frame");
    assert.equal(result.pendingPromises, 0, "scenario did not reach the resolved-command boundary");
    assert.equal(result.earlyStop, false, "stop_movie returned with an undrawn camera reset");
    assert.ok(dist(result.beforePausedPlayback, result.pausedAtStop) < 1e-6, "stop did not preserve the observed camera");
    assert.ok(dist(result.pausedAtStop, result.pausedAfterStop) < 1e-6, "a queued reset landed after stop returned");

    await browser.close();

    assert.strictEqual(errors.length, 0, `Console errors detected: ${errors.join("; ")}`);
    console.log("[E2E] passed");
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
