import assert from "node:assert/strict";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import type { BrowserContext, Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";

async function clickSample(page: Page, sample: number) {
    const svg = page.locator('[data-molsysviewer-datacard="authority-plot"] svg:has(polyline)');
    await svg.waitFor({ state: "visible" });
    const position = await svg.evaluate((node, sample) => {
        const values = node.querySelector("polyline")!.getAttribute("points")!.split(/\s+/)[sample].split(",").map(Number);
        const point = (node as SVGSVGElement).createSVGPoint();
        [point.x, point.y] = values;
        const screen = point.matrixTransform((node as SVGSVGElement).getScreenCTM()!);
        const rect = node.getBoundingClientRect();
        return { x: screen.x - rect.left, y: screen.y - rect.top };
    }, sample);
    await svg.click({ position });
}

async function inspect(bridge: PythonFixtureBridge) {
    const result = await bridge.request([{ plot_fixture: "inspect" }]);
    const record = result.messages.map((message: any) => message.content.protocolVersion === undefined
        ? message.content : message.content.payload).find((content: any) => content.op === "trajectory_plot_fixture_state");
    assert.ok(record, "The real Python authority must return an explicit current-state observation");
    return record;
}

async function clickAndReceive(page: Page, source: Page, sample: number) {
    const before = await source.evaluate(() => (window as any).__plotAuthorityIntents.length);
    await clickSample(page, sample);
    // A popup posts asynchronously to its opener. Draining an empty host queue
    // cannot acknowledge a message that has not arrived there yet.
    await source.waitForFunction(({ before, sample }) => (window as any).__plotAuthorityIntents
        .slice(before).some((event: any) => event.index === sample), { before, sample });
    await source.evaluate(() => (window as any).__popupFixtureDrain());
}

async function rendered(page: Page, index: number, coordinates: number[][][]) {
    await page.waitForFunction(({ index, coordinates }) => {
        const controller = (window as any).__mirrorController;
        if (controller?.trajectory.getTrajectoryState().currentFrame !== index) return false;
        const structure = controller.getStructureData();
        if (!structure) return false;
        const atoms = new Map<number, number[]>();
        for (const unit of structure.units) for (const atom of unit.elements) {
            atoms.set(atom, Array.from(unit.conformation.position(atom, [0, 0, 0])));
        }
        return atoms.size === coordinates[index].length && coordinates[index].every((point, atom) =>
            point.every((value, dimension) => Math.abs(value - atoms.get(atom)![dimension]) < 2e-4));
    }, { index, coordinates });
}

/** A real click must reach the retained Python owner, not just a local playhead. */
export async function checkTrajectoryPlotAuthority(context: BrowserContext, dir: string) {
    await withFixtureWorkspace("plot-authority", async workspace => {
        const bridge = new PythonFixtureBridge(resolve(dir, "trajectory-plot-bridge.py"), resolve(dir, "../../../.."),
            90000, { args: ["--static-path", resolve(workspace, "plot.html")], env: fixtureEnvironment(workspace) });
        const source = await context.newPage();
        const errors: string[] = [];
        source.on("pageerror", error => errors.push(String(error)));
        let popup: Page | undefined;
        let release: (() => Promise<void>) | undefined;
        try {
            release = await mountCanvasPopupFixture(source, bridge, { trajectoryLabel: "3 / 3" });
            await captureCanvasPopupControllers(source);
            await source.evaluate(() => {
                const w = window as any;
                const model = w.__popupWidgetModel;
                const send = model.send.bind(model);
                const intents = w.__plotAuthorityIntents = [];
                model.send = (message: any) => {
                    const event = message.protocolVersion === undefined ? message : message.payload;
                    if (event?.event === "interaction_context_action" && event.action === "set_trajectory_frame") {
                        intents.push({ index: event.index });
                    }
                    return send(message);
                };
            });
            let state = await inspect(bridge);
            assert.equal(state.index, 2);
            assert.deepEqual(state.callbacks, []);
            await rendered(source, 2, state.coordinates);

            await clickAndReceive(source, source, 1);
            state = await inspect(bridge);
            assert.equal(state.index, 1, "Plot click reached Mol* but did not update Python's current structure");
            assert.deepEqual(state.callbacks.map((event: any) => event.frame), [1]);
            await rendered(source, 1, state.coordinates);
            const distance = Math.hypot(...state.coordinates[1][0].map((value: number, dimension: number) =>
                value - state.coordinates[1][5][dimension]));
            assert.ok(Math.abs(state.current_distance - distance) < 1e-9);

            await clickAndReceive(source, source, 1);
            state = await inspect(bridge);
            assert.deepEqual(state.callbacks.map((event: any) => event.frame), [1], "Repeated selection emitted duplicate Python callbacks");

            const opened = source.waitForEvent("popup");
            await source.getByTitle("Open popup", { exact: true }).click();
            popup = await opened;
            popup.on("pageerror", error => errors.push(String(error)));
            await popup.waitForFunction(() => !!(window as any).__mirrorController);
            await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
            await rendered(popup, 1, state.coordinates);
            await clickAndReceive(popup, source, 2);
            state = await inspect(bridge);
            assert.equal(state.index, 2);
            assert.deepEqual(state.callbacks.map((event: any) => event.frame), [1, 2]);
            for (const endpoint of [source, popup]) await rendered(endpoint, 2, state.coordinates);

            await source.evaluate(() => {
                (window as any).__popupWidgetModel.send({ plot_fixture: "go", index: 0 });
                return (window as any).__popupFixtureDrain();
            });
            state = await inspect(bridge);
            assert.equal(state.index, 0);
            assert.deepEqual(state.callbacks.map((event: any) => event.frame), [1, 2, 0]);
            for (const endpoint of [source, popup]) await rendered(endpoint, 0, state.coordinates);
            assert.equal(state.plot_count, 1);
            assert.equal(state.is_playing, false);
            const staticPage = await context.newPage();
            staticPage.on("pageerror", error => errors.push(String(error)));
            try {
                await staticPage.goto(pathToFileURL(state.static_path).href);
                await staticPage.waitForFunction(() => !!(window as any).__molsysviewerDocsController);
                await captureCanvasPopupControllers(staticPage);
                await rendered(staticPage, 2, state.coordinates);
                await clickSample(staticPage, 1);
                await rendered(staticPage, 1, state.coordinates);
                // The exported file is self-contained and independent of the
                // retained notebook authority, including its public callbacks.
                state = await inspect(bridge);
                assert.equal(state.index, 0);
                assert.deepEqual(state.callbacks.map((event: any) => event.frame), [1, 2, 0]);
            } finally { await staticPage.close(); }
            assert.deepEqual(await source.evaluate(() => (window as any).__popupFixtureErrors), []);
            assert.deepEqual(errors, []);
            console.log("[E2E trajectory plot] actual source/popup clicks, Python callbacks, physical structures, reverse navigation and independent static HTML passed");
        } finally {
            if (popup && !popup.isClosed()) await popup.close();
            if (release) await release();
            await source.close();
            await bridge.close();
        }
    });
}
