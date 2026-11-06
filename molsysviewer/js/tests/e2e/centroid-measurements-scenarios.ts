import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import type { BrowserContext, Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";

type Oracle = { coordinates: number[][][]; measurements: Array<{
    kind: string; tag: string; effective: number[][]; points: number[][][]; values: number[]; python_series: number[] | null;
}> };

function near(actual: number, expected: number, tolerance = 2e-5) {
    assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected} (tolerance ${tolerance})`);
}

async function read(page: Page, tag: string) {
    return page.evaluate(tag => {
        const w = window as any;
        return w.Harness.inspectMeasurementGeometry(w.__mirrorController ?? w.__controller, tag);
    }, tag);
}

async function registered(page: Page, tag: string) {
    return page.evaluate(tag => {
        const w = window as any;
        return w.Harness.inspectTaggedRefs(w.__controller, "measurement", tag);
    }, tag);
}

async function check(page: Page, oracle: Oracle, frame: number, hidden: string[] = []) {
    for (const record of oracle.measurements) {
        if (record.python_series !== null) record.python_series.forEach((value, index) => near(value, record.values[index], 1e-9));
        const actual = await read(page, record.tag);
        if (hidden.includes(record.tag) || record.python_series === null) {
            assert.equal(actual.geometry.length, 0, `${record.tag} unexpectedly rendered`);
            continue;
        }
        assert.ok(actual.geometry.some((item: any) => item.kind === "text"), `${record.tag} has no actual text geometry`);
        for (const geometry of actual.geometry) {
            geometry.points.forEach((point: number[], index: number) => point.forEach((value, dimension) =>
                near(value, record.points[frame][index][dimension])));
            const value = /(?:Distance|Angle|Dihedral)\s+(-?\d+(?:\.\d+)?)/.exec(geometry.label);
            assert.ok(value, geometry.label);
            near(Number(value[1]), record.values[frame], .011);
            assert.equal(geometry.props.textColor, 0xab1234);
            assert.equal(geometry.props.textSize, 1.7);
            assert.equal(geometry.props.background, true);
            assert.equal(geometry.props.backgroundOpacity, .6);
            if (geometry.kind === "text" && record.kind === "distance") {
                geometry.labelAnchor.forEach((value: number, dimension: number) => near(value,
                    (record.points[frame][0][dimension] + record.points[frame][1][dimension]) / 2));
            }
        }
        assert.deepEqual(actual.participants, record.effective.flat(), `${record.tag} lost participant occurrences`);
    }
}

async function frame(page: Page, index: number) {
    await page.evaluate(async index => (window as any).__controller.trajectory.setTrajectoryFrame(index), index);
}

async function load(page: Page, dir: string, messages: unknown[]) {
    await page.goto("about:blank");
    await page.setContent('<div id="root" style="width:900px;height:650px"></div>');
    await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
    await page.evaluate(async messages => {
        const w = window as any;
        w.__controller = await w.Harness.createController("root");
        for (const message of messages) await w.__controller.handleMessage(message);
    }, messages);
}

/** Actual geometry follows its structure dependency, without manual measure replay. */
export async function checkCentroidMeasurements(context: BrowserContext, dir: string) {
    await withFixtureWorkspace("centroid-measurements", async workspace => {
        const result = spawnSync(process.env.PYTHON || "python", [resolve(dir, "centroid-measurements-bridge.py")],
            { encoding: "utf8", cwd: resolve(dir, "../../../.."), env: fixtureEnvironment(workspace), maxBuffer: 16 * 1024 * 1024 });
        assert.equal(result.status, 0, result.stderr);
        const fixture = JSON.parse(result.stdout);
        const page = await context.newPage();
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        try {
            await load(page, dir, fixture.initial);
            const target = await page.evaluate(() => {
                const w = window as any;
                return w.Harness.openSceneObjectContext(w.__controller, "measurement", "centroid-distance");
            });
            assert.equal(target.kind, "measurement");
            assert.equal(target.tag, "centroid-distance");
            assert.deepEqual(target.atom_indices, [0, 2, 4, 5]);
            const originalRef = (await read(page, "centroid-distance")).geometry[0].ref;
            for (const tag of ["centroid-distance", "atomic-distance"]) {
                const initialCount = (await registered(page, tag)).length;
                for (let cycle = 0; cycle < 3; cycle++) {
                    await page.evaluate(async tag => (window as any).__controller.measurements.setVisibility(tag, false), tag);
                    assert.deepEqual(await registered(page, tag), []);
                    await page.evaluate(async tag => (window as any).__controller.measurements.setVisibility(tag, true), tag);
                    const refs = await registered(page, tag);
                    assert.equal(refs.length, initialCount);
                    assert.ok(refs.every((ref: { exists: boolean }) => ref.exists));
                }
            }
            const liveRef = (await read(page, "centroid-distance")).geometry[0].ref;
            for (const index of [0, 2, 1, 0]) { await frame(page, index); await check(page, fixture.before, index); }
            assert.notEqual(liveRef, originalRef);
            assert.equal((await read(page, "centroid-distance")).geometry[0].ref, liveRef);
            await page.evaluate(async () => (window as any).__controller.trajectory.stepTrajectory(1));
            await check(page, fixture.before, 1);
            await frame(page, 0);
            await page.evaluate(async () => (window as any).__controller.trajectory.setTrajectoryPlayback({
                action: "play", fps: 15, mode: "once", direction: "forward", step: 1,
            }));
            await page.waitForFunction(() => {
                const state = (window as any).__controller.trajectory.getTrajectoryState();
                return !state.isPlaying && state.currentFrame === 2;
            });
            await check(page, fixture.before, 2);
            await frame(page, 0);
            for (const stage of fixture.stages) {
                const retired = stage.name === "delete"
                    ? (await registered(page, "renamed-distance")).map((item: { ref: string }) => item.ref) : [];
                await page.evaluate(async messages => {
                    for (const message of messages) await (window as any).__controller.handleMessage(message);
                }, stage.messages);
                // Check immediately: a subsequent frame navigation must not mask
                // missing dependency updates at the coordinate-edit completion.
                await check(page, stage.oracle, 0, stage.name === "hide" ? ["centroid-distance"] : []);
                if (stage.name === "delete") {
                    assert.ok(retired.length > 0);
                    assert.ok(await page.evaluate(refs => refs.every(ref =>
                        !(window as any).__controller.plugin.state.data.cells.has(ref)), retired),
                    "delete removed registration but retained actual centroid measurement nodes");
                }
                if (stage.name === "rename") {
                    const renamed = await page.evaluate(() => {
                        const w = window as any;
                        return w.Harness.openSceneObjectContext(w.__controller, "measurement", "renamed-distance");
                    });
                    assert.equal(renamed.kind, "measurement");
                    assert.equal(renamed.tag, "renamed-distance");
                    assert.deepEqual(renamed.atom_indices, [0, 2, 4, 5]);
                }
                for (const index of [2, 1, 0]) {
                    await frame(page, index);
                    await check(page, stage.oracle, index, stage.name === "hide" ? ["centroid-distance"] : []);
                }
            }
            const acknowledgments = await page.evaluate(() => ((window as any).__messages || [])
                .filter((message: any) => message.event === "trajectory_frame_rendered").map((message: any) => message.transaction_id));
            assert.ok(acknowledgments.includes("centroids"));
            await load(page, dir, fixture.session);
            for (const index of [0, 2, 1]) { await frame(page, index); await check(page, fixture.session_oracle, index); }
            assert.deepEqual(errors, []);
            console.log("[E2E measurements] real centroids, signed values, live edits, lifecycle and session passed");
        } finally { await page.close(); }

        // Use the actual widget bootstrap and popup transport with a live
        // Python authority; a second independently constructed harness is not a mirror.
        const notebook = await context.newPage();
        notebook.on("pageerror", error => errors.push(String(error)));
        const bridge = new PythonFixtureBridge(resolve(dir, "centroid-measurements-bridge.py"), resolve(dir, "../../../.."),
            90000, { args: ["--popup"], env: fixtureEnvironment(workspace) });
        let popup: Page | undefined;
        let panelPopup: Page | undefined;
        let release: (() => Promise<void>) | undefined;
        try {
            release = await mountCanvasPopupFixture(notebook, bridge);
            await captureCanvasPopupControllers(notebook);
            const opened = notebook.waitForEvent("popup");
            await notebook.getByTitle("Open popup", { exact: true }).click();
            popup = await opened;
            popup.on("pageerror", error => errors.push(String(error)));
            await popup.waitForFunction(() => !!(window as any).__mirrorController);
            await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
            for (const endpoint of [notebook, popup]) {
                await endpoint.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
                await check(endpoint, fixture.before, 0);
            }
            await popup.getByTitle("Panel mode (N / W)", { exact: true }).click();
            const panelOpened = popup.waitForEvent("popup");
            await popup.getByTitle("Popout panel to external window", { exact: true }).click();
            panelPopup = await panelOpened;
            panelPopup.on("pageerror", error => errors.push(String(error)));
            await panelPopup.locator('[data-molsysviewer-group-panel-tab="measures"]').click();
            const checkPanel = async (frame: number) => {
                for (const record of fixture.before.measurements) {
                    const distance = record.kind === "distance";
                    const value = distance ? record.values[frame] * 100 : record.values[frame] * Math.PI / 180;
                    // The formatter abbreviates radians, but preserves other
                    // canonical unit labels such as Pint's "picometer".
                    const expected = `${value.toFixed(distance ? 2 : 3)} ${distance ? "picometer" : "rad"}`;
                    try {
                        await panelPopup!.waitForFunction(({ tag, expected }) =>
                            document.querySelector(`[data-molsysviewer-measurement-value="${tag}"]`)?.textContent === expected,
                        { tag: record.tag, expected });
                    } catch (error) {
                        const actual = await panelPopup!.locator(`[data-molsysviewer-measurement-value="${record.tag}"]`).textContent();
                        for (const [name, endpoint] of [["notebook", notebook], ["canvas-popup", popup]] as [string, Page][]) {
                            console.error(name, await endpoint.evaluate(() => {
                                const c = (window as any).__mirrorController;
                                return { frame: c.trajectory.getTrajectoryState(), settings: c.measurementSettings,
                                    summaries: c.measurementSummaries };
                            }));
                        }
                        console.error("authority summaries", JSON.stringify((await bridge.request([{ measurement_fixture: "inspect" }])).messages));
                        throw new Error(`${record.tag} frame ${frame}: expected ${expected}, actual ${actual}`, { cause: error });
                    }
                }
            };
            await checkPanel(0);
            for (const [origin, index] of [[popup, 1], [notebook, 2]] as [Page, number][]) {
                await origin.bringToFront();
                await origin.locator('[data-molsysviewer-trajectory-step="next"]').click();
                await notebook.evaluate(() => (window as any).__popupFixtureDrain());
                for (const endpoint of [notebook, popup]) {
                    await endpoint.waitForFunction(index => (window as any).__mirrorController.trajectory.getTrajectoryState().currentFrame === index, index);
                    // A follower can receive Python's summary before its queued
                    // frame projection. Wait for applied geometry, not the label.
                    await endpoint.waitForFunction(points => {
                        const w = window as any, c = w.__mirrorController;
                        const actual = w.Harness.inspectMeasurementGeometry(c, "centroid-distance").geometry;
                        return !c.plugin.behaviors.state.isUpdating.value && actual.length > 0
                            && actual.every((geometry: any) => geometry.points.every((point: number[], index: number) =>
                                point.every((value, dimension) => Math.abs(value - points[index][dimension]) < 2e-5)));
                    }, fixture.before.measurements[0].points[index]);
                    await check(endpoint, fixture.before, index);
                }
                await checkPanel(index);
            }
            assert.deepEqual(await notebook.evaluate(() => (window as any).__popupFixtureErrors), []);
            assert.deepEqual(errors, []);
            console.log("[E2E measurements] notebook/canvas-popup geometry, Studio popup pm/rad values and bidirectional frame mirror passed");
        } finally {
            await release?.();
            await panelPopup?.close();
            await popup?.close();
            await notebook.close();
            await bridge.close();
        }
    });
}
