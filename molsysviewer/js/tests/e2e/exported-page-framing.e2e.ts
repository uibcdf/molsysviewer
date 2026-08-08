/**
 * An exported page has to frame its own scene.
 *
 * Contract S9 sets `manualReset`, which removes Mol*'s own camera reset —
 * including the rescue that used to hide an unframed viewer. In a notebook
 * Python is there to ask again. An exported page has nobody: if
 * `frameLoadedStructure` does not run here, the reader opens the file and finds
 * the structure a speck at the camera's default distance, with no way back but
 * "Reset view".
 *
 * Nothing had ever opened a real exported page in a browser and looked at its
 * camera. `export-replay.e2e.ts` replays the export *sequence* through the test
 * harness, which is a different thing: the harness builds the controller itself,
 * so it cannot show what `bootDocsView` does.
 *
 * **Why this lives here and not in the Python suite.** The framing loop measures
 * its own deadline with `Date.now()`, and Chrome's `--virtual-time-budget` — the
 * only way a `--dump-dom` run can wait for anything — fast-forwards that clock
 * without running the frames that resolve a camera reset. Measured under it, the
 * same page reported framed in one run and unframed in the next, purely from
 * where the virtual clock landed. Playwright waits in real time, so the number
 * means what it says.
 *
 * Mutation-verified by commenting out the `frameLoadedStructure` call in
 * `captureCurrentStructure` and rebuilding the runtime. It fails — but at the
 * *content* assertion, not the radius one: `frameLoadedStructure` is also the
 * only thing that calls `requestDraw`, so an idle headless canvas never commits
 * and the scene never reports a bounding sphere at all. Expect that message
 * rather than "never framed its scene" if this ever turns red for that reason.
 */
import assert from "node:assert";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, resolve } from "node:path";
import { chromium } from "./e2e-browser";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/** Mol*'s own default. A camera that has never framed anything reports this. */
const MOLSTAR_DEFAULT_RADIUS_MAX = 10;

async function run() {
    console.log("[E2E exported-page-framing] Scenario: an exported page frames its scene");

    const python = spawnSync(
        process.env.PYTHON_BIN || "python",
        [resolve(__dirname, "exported-page-framing-bridge.py")],
        { encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
    );
    assert.strictEqual(python.status, 0, python.stderr || python.stdout);
    const exported = JSON.parse(python.stdout);
    console.log(`[E2E exported-page-framing]   exported ${exported.n_atoms} atoms to ${exported.page}`);

    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        chromiumSandbox: false,
        args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"],
    } as any);
    const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));

    try {
        // Opened as a file, deliberately: that is how a reader opens it.
        await page.goto(pathToFileURL(exported.page).href);

        await page.waitForFunction(
            () => !!(window as any).__molsysviewerDocsController,
            { timeout: 60000 },
        );

        const measured = await page.evaluate(async () => {
            const controller = (window as any).__molsysviewerDocsController;
            const canvas3d: any = controller?.plugin?.canvas3d;
            const wait = (ms: number) => new Promise(r => setTimeout(r, ms));

            const sample = () => {
                const state = canvas3d.camera.state;
                const sceneRadius = (canvas3d.boundingSphere?.radius ?? 0)
                    * (canvas3d.props?.sceneRadiusFactor ?? 1);
                return {
                    radiusMax: state.radiusMax,
                    sceneRadius,
                    distance: Math.hypot(
                        state.position[0] - state.target[0],
                        state.position[1] - state.target[1],
                        state.position[2] - state.target[2],
                    ),
                };
            };

            const deadline = Date.now() + 45000;
            let last = null as null | ReturnType<typeof sample>;
            while (Date.now() < deadline) {
                if (canvas3d && (canvas3d.boundingSphere?.radius ?? 0) > 0) {
                    last = sample();
                    // Framed is `radiusMax` agreeing with the scene radius; the
                    // controller uses the same test, for the same reason.
                    if (Math.abs(last.radiusMax - last.sceneRadius) / last.sceneRadius < 0.1) {
                        // Hold, so a transient agreement cannot pass for a settled one.
                        await wait(2000);
                        return { ...sample(), sawContent: true };
                    }
                }
                await wait(200);
            }
            return last ? { ...last, sawContent: true } : { sawContent: false };
        });

        assert.ok(measured.sawContent, "the exported page never produced a scene with content");
        const { radiusMax, sceneRadius, distance } = measured as any;
        console.log(
            `[E2E exported-page-framing]   radiusMax=${radiusMax.toFixed(2)} `
            + `sceneRadius=${sceneRadius.toFixed(2)} distance=${distance.toFixed(1)}`,
        );

        assert.ok(sceneRadius > 0, "the scene reported no radius");
        assert.ok(
            Math.abs(radiusMax - sceneRadius) / sceneRadius < 0.1,
            `the exported page never framed its scene: radiusMax ${radiusMax} against a scene `
            + `radius of ${sceneRadius}. ${radiusMax === MOLSTAR_DEFAULT_RADIUS_MAX
                ? "That is Mol*'s default, i.e. a camera that never framed anything."
                : ""}`,
        );
        assert.ok(
            distance < sceneRadius * 6,
            `framed, then left at distance ${distance} from a scene of radius ${sceneRadius}`,
        );

        const afterRepresentationChange = await page.evaluate(async () => {
            const controller = (window as any).__molsysviewerDocsController;
            const handleMessage = (window as any).__molsysviewerDocsHandleMessage;
            const wait = (ms: number) => new Promise(r => setTimeout(r, ms));
            const representationNames = () => Array.from(
                (controller as any).state?.globalReprs ?? [],
            ).map((ref: any) => controller.plugin.state.data.cells.get(ref))
                .filter(Boolean)
                .map((cell: any) => cell.transform?.params?.type?.name)
                .filter((name: any) => typeof name === "string");

            await handleMessage({
                op: "set_whole_representation",
                representation: "spacefill",
                preset: null,
                params: {},
            });

            const deadline = Date.now() + 30000;
            while (Date.now() < deadline && !representationNames().includes("spacefill")) {
                await wait(100);
            }
            await wait(1000);

            const canvas3d: any = controller.plugin.canvas3d;
            const state = canvas3d.camera.state;
            const changedSceneRadius = (canvas3d.boundingSphere?.radius ?? 0)
                * (canvas3d.props?.sceneRadiusFactor ?? 1);
            return {
                representationNames: representationNames(),
                sceneRadius: changedSceneRadius,
                distance: Math.hypot(
                    state.position[0] - state.target[0],
                    state.position[1] - state.target[1],
                    state.position[2] - state.target[2],
                ),
            };
        });

        assert.deepStrictEqual(
            afterRepresentationChange.representationNames,
            ["spacefill"],
            "the exported page did not replace the rendered whole representation",
        );
        assert.ok(
            afterRepresentationChange.sceneRadius > 0
                && afterRepresentationChange.distance < afterRepresentationChange.sceneRadius * 6,
            "the exported page lost usable framing after changing the whole representation",
        );

        assert.deepStrictEqual(errors, [], "the exported page raised errors while framing");
        console.log("[E2E exported-page-framing]   initial and post-representation framing are usable");
    } finally {
        await browser.close();
    }

    console.log("[E2E exported-page-framing] passed");
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
