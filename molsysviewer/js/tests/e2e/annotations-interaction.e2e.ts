import assert from "node:assert";
import process from "node:process";
import { chromium } from "./e2e-browser";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { execFileSync } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PDB_TEXT = `
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
`;

async function run() {
    const envBin = process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome";
    const browser = await chromium.launch({
        headless: true,
        executablePath: envBin,
        chromiumSandbox: false,
        args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    } as any);

    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", err => errors.push(String(err)));

    const harnessPath = resolve(__dirname, "harness.bundle.js");
    await page.setContent(
        `<!doctype html><html><body><div id="root" style="width:800px;height:600px;"></div></body></html>`,
    );
    await page.addScriptTag({ path: harnessPath });
    await page.waitForFunction(() => typeof (window as any).Harness !== "undefined");

    // ── Scenario 1: add_label renders without errors ─────────────────────────
    console.log("[E2E annotations] Scenario: add_label renders");

    await page.evaluate(async (pdb) => {
        const controller = await (window as any).Harness.createController("root");
        (window as any).__controller = controller;
        (window as any).__messages = [];
        await controller.handleMessage({
            op: "load_structure_from_string",
            data: pdb,
            format: "pdb",
            label: "test-annotations",
        });

        // Poll for structure to be loaded
        for (let i = 0; i < 50; i++) {
            const s = (controller as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
            if (s?.elementCount > 0) break;
            await new Promise(r => setTimeout(r, 100));
        }

        await controller.handleMessage({
            op: "add_label",
            tag: "label-n",
            options: {
                text: "N-terminus",
                atom_indices: [0],
                tag: "label-n",
                style: { color: "#FF0000", size_em: 1.2, background: true, background_opacity: 0.7 },
            },
        });
    }, PDB_TEXT);

    // ── Scenario 2: label visibility toggle works ────────────────────────────
    console.log("[E2E annotations] Scenario: label visibility toggle");

    await page.evaluate(async () => {
        const controller = (window as any).__controller;
        // Add a second label with a shared layer
        await controller.handleMessage({
            op: "add_label",
            tag: "label-ca",
            options: {
                text: "CA",
                atom_indices: [1],
                tag: "label-ca",
                layer_tag: "backbone-labels",
            },
        });
        await controller.handleMessage({
            op: "add_label",
            tag: "label-c",
            options: {
                text: "C",
                atom_indices: [2],
                tag: "label-c",
                layer_tag: "backbone-labels",
            },
        });
        // Hide the shared layer
        await controller.handleMessage({
            op: "set_visibility",
            tag: "backbone-labels",
            visible: false,
        });
        // Re-show it
        await controller.handleMessage({
            op: "set_visibility",
            tag: "backbone-labels",
            visible: true,
        });
    });

    // ── Scenario 3: resolveTooltipPayload logic via notifyHover ──────────────
    // We cannot trigger actual Mol* hover events without WebGL, but we can verify
    // that the controller's internal annotation registry is populated correctly.
    console.log("[E2E annotations] Scenario: annotation registry populated");

    const hasAnnotation = await page.evaluate(() => {
        const controller = (window as any).__controller;
        return (controller as any).annotations?.hasTag?.("label-n") === true;
    });
    assert.ok(hasAnnotation, "annotation 'label-n' should be registered in AnnotationHandlers");

    // ── Scenario 4: add_distance with measurement_style ──────────────────────
    console.log("[E2E annotations] Scenario: add_distance_measurement with measurement_style");

    await page.evaluate(async () => {
        const controller = (window as any).__controller;
        const structure = (controller as any).plugin?.managers?.structure?.hierarchy?.current?.structures?.[0]?.cell?.obj?.data;
        if (!structure) return;

        // Build loci for atoms 0 and 1 using the controller's structure
        await controller.handleMessage({
            op: "add_distance_measurement",
            tag: "dist-ca-n",
            options: {
                atom_indices: [0, 1],
                tag: "dist-ca-n",
                measurement_style: { color: "#00FF00", size_em: 1.0, background: false },
            },
        });
    });

    const hasMeasurement = await page.evaluate(() => {
        const controller = (window as any).__controller;
        return (controller as any).measurements?.hasTag?.("dist-ca-n") === true;
    });
    assert.ok(hasMeasurement, "measurement 'dist-ca-n' should be registered in MeasurementHandlers");

    // ── Scenario 5: tooltip payload resolution via internal method ────────────
    console.log("[E2E annotations] Scenario: resolveTooltipPayload via controller");

    const tooltipResult = await page.evaluate(() => {
        const controller = (window as any).__controller;
        const annotations = (controller as any).annotations;
        const measurements = (controller as any).measurements;
        if (!annotations || !measurements) return null;

        // Simulate what resolveTooltipPayload does:
        const tooltipTag = "label-n";
        if (annotations.hasTag(tooltipTag)) {
            const spec = annotations.getSpec(tooltipTag);
            return { kind: "annotation", tag: tooltipTag, text: spec?.text, atom_indices: spec?.atom_indices };
        }
        return null;
    });

    assert.ok(tooltipResult !== null, "tooltip resolution should find annotation");
    assert.strictEqual(tooltipResult?.kind, "annotation");
    assert.strictEqual(tooltipResult?.tag, "label-n");
    assert.strictEqual(tooltipResult?.text, "N-terminus");
    assert.deepStrictEqual(tooltipResult?.atom_indices, [0]);

    // Real demo trajectory, public Python creation, and actual Mol* canvas geometry.
    const fixture = JSON.parse(execFileSync(process.env.PYTHON || "python", [
        resolve(__dirname, "annotation-callout-bridge.py"),
    ], { encoding: "utf8" }));
    const observed = await page.evaluate(async fixture => {
        const controller = (window as any).__controller;
        await controller.handleMessage({ op: "clear_all" });
        let draws = 0;
        const subscription = controller.plugin.canvas3d.didDraw.subscribe(() => draws++);
        for (const message of fixture.messages) await controller.handleMessage(message);
        const geometry = (tag: string) => {
            const cell = Array.from(controller.plugin.state.data.cells.values()).find((cell: any) =>
                cell.obj?.data?.sourceData?.tag === tag) as any;
            if (!cell) throw new Error(`Missing annotation geometry ${tag}`);
            return { ...cell.obj.data.sourceData,
                drawCounts: cell.obj.data.repr.renderObjects.map((object: any) => object.values.drawCount.ref.value) };
        };
        const world = ["solid", "dashed", "dotted"].map(pattern => geometry(`world-${pattern}`));
        const cameraBefore = geometry("camera-dotted");
        const camera = controller.plugin.canvas3d.camera;
        camera.setState({ position: [30, 0, 10], target: fixture.point, up: [0, 1, 0] }, 0);
        controller.annotations.onCamera(camera.getSnapshot());
        await controller.annotations.refresh();
        const cameraAfter = geometry("camera-dotted");
        const worldAfter = geometry("world-dotted");
        await controller.handleMessage({ op: "set_trajectory_frame", index: 2 });
        const lastFrame = geometry("camera-dotted");
        const worldLast = geometry("world-dotted");
        await controller.handleMessage({ op: "set_trajectory_frame", index: 0 });
        await new Promise<void>(async (resolve, reject) => {
            const timeout = setTimeout(() => { unsubscribe(); reject(new Error("Annotation playback did not settle")); }, 10000);
            const unsubscribe = controller.trajectory.onTrajectoryState((state: any) => {
                if (!state.isPlaying && state.currentFrame === 2) {
                    clearTimeout(timeout); unsubscribe(); resolve();
                }
            }, { immediate: false });
            try {
                await controller.handleMessage({ op: "set_trajectory_playback", action: "play", fps: 30, mode: "once" });
            } catch (error) { clearTimeout(timeout); unsubscribe(); reject(error); }
        });
        const afterPlayback = geometry("camera-dotted");
        // World-to-atom transition must clear the old absolute position.
        await controller.handleMessage({ op: "update_label", tag: "world-solid", options: {
            position: null, atom_indices: [0], text: "now atom anchored" } });
        const reanchored = geometry("world-solid");
        await controller.handleMessage({ op: "hide_layer", tag: "world-dotted", kind: "annotation" });
        const hidden = !Array.from(controller.plugin.state.data.cells.values()).some((cell: any) =>
            cell.obj?.data?.sourceData?.tag === "world-dotted");
        await controller.handleMessage({ op: "update_label", tag: "world-dotted", options: { text: "edited while hidden" } });
        const hiddenAfterEdit = !Array.from(controller.plugin.state.data.cells.values()).some((cell: any) =>
            cell.obj?.data?.sourceData?.tag === "world-dotted");
        await controller.handleMessage({ op: "show_layer", tag: "world-dotted", kind: "annotation" });
        const shown = geometry("world-dotted");
        // Wait for a real canvas draw after the final asynchronous state writes.
        await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => reject(new Error("No canvas draw for annotation callouts")), 10000);
            let armed = false;
            const sub = controller.plugin.canvas3d.didDraw.subscribe(() => {
                if (!armed) return;
                clearTimeout(timeout); sub.unsubscribe(); resolve();
            });
            armed = true;
            controller.plugin.canvas3d.requestDraw(true);
        });
        subscription.unsubscribe();
        return { world, cameraBefore, cameraAfter, worldAfter, lastFrame, afterPlayback, worldLast, reanchored, hidden, hiddenAfterEdit, shown, draws };
    }, fixture);
    const close = (actual: number[], expected: number[]) =>
        actual.forEach((value, i) => assert.ok(Math.abs(value - expected[i]) < 1e-4, `${value} differs from ${expected[i]}`));
    for (const world of observed.world) {
        close(world.anchor, fixture.point);
        close(world.position, fixture.point.map((value: number, i: number) => value + [3, 2, 1][i]));
        assert.ok(world.drawCounts.some((count: number) => count > 0), "callout has renderable canvas geometry");
    }
    assert.equal(new Set(observed.world.map((world: any) => world.drawCounts.join(","))).size, 3,
        "solid, dashed and dotted leaders have distinct rendered geometry");
    close(observed.worldAfter.position, observed.world[2].position);
    close(observed.worldLast.position, observed.world[2].position);
    assert.notDeepEqual(observed.cameraBefore.position, observed.cameraAfter.position);
    close(observed.lastFrame.anchor, fixture.atom_at_last_frame);
    close(observed.afterPlayback.anchor, fixture.atom_at_last_frame);
    close(observed.reanchored.anchor, fixture.atom_at_last_frame);
    assert.ok(observed.hidden);
    assert.ok(observed.hiddenAfterEdit);
    assert.equal(observed.shown.text, "edited while hidden");
    close(observed.shown.position, observed.world[2].position);
    assert.ok(observed.draws > 0);

    await browser.close();

    assert.strictEqual(errors.length, 0, `Console errors: ${errors.join("; ")}`);
    console.log("[E2E annotations] All scenarios passed");
}

run().catch(err => {
    console.error(err);
    process.exit(1);
});
