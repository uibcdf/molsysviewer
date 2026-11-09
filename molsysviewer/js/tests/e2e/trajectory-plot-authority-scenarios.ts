import assert from "node:assert/strict";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import type { BrowserContext, Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";

async function clickSample(page: Page, sample: number, tag = "authority-plot") {
    const svg = page.locator(`[data-molsysviewer-datacard="${tag}"] svg:has(polyline)`);
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

async function clickAndReceive(page: Page, source: Page, sample: number, tag = "authority-plot") {
    const before = await source.evaluate(() => (window as any).__plotAuthorityIntents.length);
    await clickSample(page, sample, tag);
    // A popup posts asynchronously to its opener. Draining an empty host queue
    // cannot acknowledge a message that has not arrived there yet.
    await source.waitForFunction(({ before, sample }) => (window as any).__plotAuthorityIntents
        .slice(before).some((event: any) => event.index === sample), { before, sample });
    await source.evaluate(() => (window as any).__popupFixtureDrain());
}

async function capturePlotIntents(source: Page) {
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
            await capturePlotIntents(source);
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
            // Repeated and reversed x positions still represent three distinct
            // molecular structures. Native keyboard input selects by index.
            await plotFixtureAction(source, { plot_fixture: "keyboard" });
            const expectedCallbacks = [1, 2, 0];
            for (const endpoint of [source, popup]) {
                const slider = endpoint.locator('[data-molsysviewer-plot-navigation="authority-plot"] input');
                for (const [key, frame] of [["End", 2], ["ArrowLeft", 1], ["Home", 0]] as const) {
                    const mark = await source.evaluate(() => (window as any).__plotAuthorityIntents.length);
                    await slider.focus(); await slider.press(key);
                    await source.waitForFunction(({ mark, frame }) => (window as any).__plotAuthorityIntents
                        .slice(mark).some((event: any) => event.index === frame), { mark, frame });
                    await source.evaluate(() => (window as any).__popupFixtureDrain());
                    state = await inspect(bridge); expectedCallbacks.push(frame);
                    assert.equal(state.index, frame);
                    assert.deepEqual(state.callbacks.map((event: any) => event.frame), expectedCallbacks);
                    assert.deepEqual(state.plot_records[0].x, [4, 4, 0]);
                    for (const target of [source, popup]) {
                        await rendered(target, frame, state.coordinates);
                        assert.equal(await target.locator('[data-molsysviewer-plot-navigation="authority-plot"] input').inputValue(), String(frame));
                    }
                    const readout = await slider.getAttribute("aria-valuetext");
                    assert.ok(readout?.includes(`Structure ${frame + 1} of 3; index ${frame}; x: ${state.plot_records[0].x[frame]}`));
                    assert.ok(readout?.includes(String(state.plot_records[0].series[0].values[frame])));
                    assert.ok(readout?.includes("Å"));
                }
            }
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
                assert.deepEqual(state.callbacks.map((event: any) => event.frame), expectedCallbacks);
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

interface PrecisionControl {
    name: string;
    x: number[];
    y: number[];
    unit?: string;
    x_fractions: number[];
    y_fractions: number[];
    records: any[];
    state_restored: boolean;
}

async function plotFixtureAction(source: Page, action: Record<string, unknown>) {
    await source.evaluate(action => {
        const w = window as any;
        w.__popupWidgetModel.send(action);
        return w.__popupFixtureDrain();
    }, action);
    assert.deepEqual(await source.evaluate(() => (window as any).__popupFixtureErrors), [],
        "The real Python fixture rejected a public trajectory-plot operation");
}

async function precisionRendered(page: Page, control: PrecisionControl, frame: number) {
    const svg = page.locator('[data-molsysviewer-datacard="precision-plot"] svg:has(polyline)');
    await svg.waitFor({ state: "visible" });
    const expectedRaw = `x: ${control.x[frame]} · y: ${control.y[frame]}`;
    await page.waitForFunction(expected => document.querySelector(
        '[data-molsysviewer-datacard="precision-plot"] [data-molsysviewer-plot-value="readout"]',
    )?.getAttribute("aria-label") === expected, expectedRaw);
    const observation = await svg.evaluate(node => {
        const axisNode = node.querySelector("path")!;
        const axis = axisNode.getBBox();
        const rect = (element: Element) => {
            const value = element.getBoundingClientRect();
            return { x: value.x, y: value.y, width: value.width, height: value.height,
                left: value.left, right: value.right, top: value.top, bottom: value.bottom };
        };
        const elementState = (element: Element) => {
            const style = getComputedStyle(element);
            return { tag: element.tagName, id: element.id, class: element.getAttribute("class"),
                isConnected: element.isConnected, display: style.display, visibility: style.visibility,
                opacity: style.opacity, contentVisibility: style.contentVisibility, overflow: style.overflow,
                position: style.position, transform: style.transform, bounds: rect(element) };
        };
        const ancestors = [];
        for (let element = node.parentElement; element; element = element.parentElement) {
            ancestors.push(elementState(element));
        }
        const viewBox = (node as SVGSVGElement).viewBox.baseVal;
        const numeric = (name: string) => {
            const text = node.querySelector<SVGTextElement>(`[data-molsysviewer-plot-value="${name}"]`)!;
            const bounds = text.getBBox();
            return {
                display: text.querySelector("tspan")!.textContent!, raw: text.querySelector("title")!.textContent!,
                accessible: text.getAttribute("aria-label"), tabIndex: text.getAttribute("tabindex"),
                left: bounds.x, right: bounds.x + bounds.width,
            };
        };
        return {
            axis: { left: axis.x, top: axis.y, width: axis.width, height: axis.height },
            points: node.querySelector("polyline")!.getAttribute("points")!.trim().split(/\s+/)
                .map(point => point.split(",").map(Number)),
            min: numeric("x-min"), max: numeric("x-max"), readout: numeric("readout"),
            width: (node as SVGSVGElement).viewBox.baseVal.width,
            text: node.textContent!,
            layout: {
                endpointURL: location.href, endpoint: window.opener ? "canvas-popup" : "source",
                documentVisibility: document.visibilityState, documentHasFocus: document.hasFocus(),
                svg: elementState(node), viewBox: { x: viewBox.x, y: viewBox.y, width: viewBox.width, height: viewBox.height },
                axis: { ...elementState(axisNode), d: axisNode.getAttribute("d"),
                    initialBBox: { x: axis.x, y: axis.y, width: axis.width, height: axis.height } },
                ancestors,
            },
        };
    });
    // Keep the original atomic observation even when a later assertion fails.
    // The receiving command owns this log; it contains no notebook/server data.
    console.log("B2_PRECISION_OBSERVATION " + JSON.stringify({ case: control.name, frame, ...observation }));
    // The oracle is produced from exact represented floats using Python Decimal;
    // observed axis bounds come from the browser's SVG, not copied layout math.
    assert.equal(observation.points.length, control.x.length);
    for (let sample = 0; sample < control.x.length; sample++) {
        const [x, y] = observation.points[sample];
        assert.ok(Number.isFinite(x) && Number.isFinite(y), `${control.name}: finite data produced invalid SVG geometry`);
        const xFraction = (x - observation.axis.left) / observation.axis.width;
        const yFraction = (observation.axis.top + observation.axis.height - y) / observation.axis.height;
        assert.ok(Math.abs(xFraction - control.x_fractions[sample]) < 1e-10,
            `${control.name} sample ${sample}: X ${xFraction} != Decimal ${control.x_fractions[sample]}`);
        assert.ok(Math.abs(yFraction - control.y_fractions[sample]) < 1e-10,
            `${control.name} sample ${sample}: Y ${yFraction} != Decimal ${control.y_fractions[sample]}`);
    }
    const minimum = Math.min(...control.x);
    const maximum = Math.max(...control.x);
    assert.equal(observation.min.raw, String(minimum));
    assert.equal(observation.max.raw, String(maximum));
    if (minimum !== maximum) assert.notEqual(observation.min.display, observation.max.display,
        `${control.name}: unequal X limits collapsed to one visible label`);
    if (minimum !== maximum) assert.notEqual(Number(observation.min.display), Number(observation.max.display),
        `${control.name}: unequal X limits only differed in notation`);
    for (const value of [observation.min, observation.max, observation.readout]) {
        assert.equal(value.accessible, value.raw);
        assert.equal(value.tabIndex, "0");
        assert.ok(value.left >= 0 && value.right <= observation.width,
            `${control.name}: numeric text is clipped by the card: ${JSON.stringify(value)}`);
    }
    assert.equal(observation.readout.raw, expectedRaw, `${control.name}: full raw readout was lost`);
    const visible = /^x: (\S+) · y: (\S+)$/.exec(observation.readout.display);
    assert.ok(visible, `Unexpected numeric readout ${observation.readout.display}`);
    for (const [raw, displayed] of [[control.x[frame], visible[1]], [control.y[frame], visible[2]]] as const) {
        assert.ok(Number.isFinite(Number(displayed)));
        if (raw === 0) assert.equal(displayed, "0");
        else {
            assert.notEqual(Number(displayed), 0, `${control.name}: a nonzero sample was displayed as zero`);
            assert.equal(Math.sign(Number(displayed)), Math.sign(raw));
        }
    }
    if (control.name === "tiny") assert.equal(visible[2], ["1e-4", "2e-4", "5e-4"][frame]);
    if (control.name === "angstrom") assert.equal(visible[2], ["0.001", "0.002", "0.005"][frame]);
    if (control.unit) assert.ok(observation.text.includes(`Numeric control (${control.unit})`));
    const readout = svg.locator('[data-molsysviewer-plot-value="readout"]');
    await readout.focus();
    assert.equal(await readout.evaluate(node => node === document.activeElement), true,
        "The full raw accessible value must also be keyboard reachable");
}

/** Real molecular rendering, exact Decimal geometry, retained raw data and popup receiving. */
export async function checkTrajectoryPlotPrecision(context: BrowserContext, dir: string) {
    await withFixtureWorkspace("plot-precision", async workspace => {
        const bridge = new PythonFixtureBridge(resolve(dir, "trajectory-plot-bridge.py"), resolve(dir, "../../../.."),
            90000, { args: ["--state-path", resolve(workspace, "precision.json")], env: fixtureEnvironment(workspace) });
        const source = await context.newPage();
        const errors: string[] = [];
        source.on("pageerror", error => errors.push(String(error)));
        let popup: Page | undefined;
        let release: (() => Promise<void>) | undefined;
        const cases = ["tiny", "angstrom", "signed", "large-offset", "negative-offset", "unordered-offset", "wide",
            "asymmetric-wide", "subnormal", "adjacent", "lower-notation-threshold", "upper-notation-threshold",
            "extreme-adjacent", "constant", "broad"];
        try {
            release = await mountCanvasPopupFixture(source, bridge, { trajectoryLabel: "3 / 3" });
            await captureCanvasPopupControllers(source);
            await capturePlotIntents(source);
            for (const name of cases) {
                await plotFixtureAction(source, { plot_fixture: "precision", case: name });
                let state = await inspect(bridge);
                const control: PrecisionControl = state.precision;
                assert.equal(control.name, name);
                assert.equal(control.records.length, 1, `${name}: the public plot operation must retain exactly one card`);
                assert.deepEqual(control.records[0].x, control.x);
                assert.deepEqual(control.records[0].series[0].values, control.y);
                for (let frame = 0; frame < 3; frame++) {
                    await plotFixtureAction(source, { plot_fixture: "go", index: frame });
                    await rendered(source, frame, state.coordinates);
                    await precisionRendered(source, control, frame);
                }
                if (["tiny", "angstrom", "signed", "large-offset", "wide", "subnormal"].includes(name)) {
                    await plotFixtureAction(source, { plot_fixture: "restore-precision" });
                    state = await inspect(bridge);
                    assert.equal(state.precision.state_restored, true);
                    assert.deepEqual(state.precision.records, control.records, `${name}: file restore changed raw plot data`);
                    await precisionRendered(source, control, 2);
                }
            }

            const opened = source.waitForEvent("popup");
            await source.getByTitle("Open popup", { exact: true }).click();
            popup = await opened;
            popup.on("pageerror", error => errors.push(String(error)));
            await popup.waitForFunction(() => !!(window as any).__mirrorController);
            await popup.locator("#molsysviewer-loading").waitFor({ state: "hidden" });
            for (const name of ["large-offset", "signed", "angstrom"]) {
                await plotFixtureAction(source, { plot_fixture: "precision", case: name });
                const state = await inspect(bridge);
                const control: PrecisionControl = state.precision;
                assert.equal(control.records.length, 1, `${name}: the popup fixture must retain exactly one card`);
                await plotFixtureAction(source, { plot_fixture: "go", index: 0 });
                for (const endpoint of [source, popup]) {
                    await rendered(endpoint, 0, state.coordinates);
                    await precisionRendered(endpoint, control, 0);
                }
                await clickAndReceive(popup, source, 1, "precision-plot");
                const received = await inspect(bridge);
                assert.equal(received.index, 1, `${name}: popup sample click did not reach the Python frame owner`);
                assert.equal(received.callbacks.at(-1).frame, 1);
                for (const endpoint of [source, popup]) {
                    await rendered(endpoint, 1, state.coordinates);
                    await precisionRendered(endpoint, control, 1);
                }
                await plotFixtureAction(source, { plot_fixture: "restore-precision" });
                const restored = await inspect(bridge);
                assert.deepEqual(restored.precision.records, control.records);
                for (const endpoint of [source, popup]) await precisionRendered(endpoint, control, 1);
            }
            assert.deepEqual(await source.evaluate(() => (window as any).__popupFixtureErrors), []);
            assert.deepEqual(errors, []);
            console.log(`[E2E trajectory plot] ${cases.length} Decimal/binary64 precision controls, raw access, actual frames, state files and canvas popup passed`);
        } finally {
            if (popup && !popup.isClosed()) await popup.close();
            if (release) await release();
            await source.close();
            await bridge.close();
        }
    });
}
