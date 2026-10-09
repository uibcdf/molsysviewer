import assert from "node:assert";
import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
import { PythonFixtureBridge } from "./python-fixture-bridge";
let fixtureWorker: PythonFixtureBridge;
const bridge = (events: unknown[] = [], family?: string) => fixtureWorker.request(events, family);
async function checkCalculationAndDisplayScopes(page: any) {
    const family = "pentalanine_scope";
    const fixture = await bridge([], family);
    await freshController(page);
    await apply(page, fixture.initial_messages);
    await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
    await page.locator('[data-molsysviewer-group-panel-tab="interactions"]').click();
    await openCreationForm(page);
    const latest = (action: string) => page.evaluate(action => [...((window as any).__messages || [])].reverse()
        .find((message: any) => message.action === action || message.event === action), action);
    const actionCount = (action: string) => page.evaluate(action => ((window as any).__messages || [])
        .filter((message: any) => message.action === action).length, action);
    const scope = page.locator('[data-molsysviewer-interaction-calc-scope="true"]');
    const create = page.locator('[data-molsysviewer-interaction-create="true"]');
    assert.equal(await scope.inputValue(), "all");
    await scope.selectOption("a");
    await create.click();
    assert.equal(await actionCount("create_interaction"), 0, "an unset calculation A must stop dispatch");
    await scope.selectOption("all");
    if (!await page.locator("[data-molsysviewer-interaction-filters]").evaluate((element: HTMLDetailsElement) => element.open))
        await page.locator('[data-molsysviewer-interaction-filters] > summary').click();
    const stagedEvents: any[] = [];
    async function stageQuery(atom: number, slot: "A" | "B") {
        await page.locator('[data-molsysviewer-interaction-filters] button').filter({ hasText: `Stage ${slot}` }).click();
        await page.locator('[data-molsysviewer-interaction-filters] button').filter({ hasText: "Select by query" }).click();
        await page.locator('[data-molsysviewer-query-input="interactions"]').fill(`atom_index==${atom}`);
        await page.locator('[data-molsysviewer-query-check="interactions"]').click();
        const request = await latest("selection_query_preview_request");
        const preview = (await bridge([request], family)).message_batches[0];
        const selectionCount = await actionCount("apply_selection_query");
        const stale = preview.map((message: any) => ({ ...message, request_id: request.request_id - 1 }));
        await apply(page, stale);
        assert.equal(await actionCount("apply_selection_query"), selectionCount, "stale query previews must not activate selection");
        await apply(page, preview);
        assert.equal(await actionCount("apply_selection_query"), selectionCount + 1, "current successful query must activate selection");
        const selection = await latest("apply_selection_query");
        assert.equal(selection.expression, `atom_index==${atom}`);
        stagedEvents.push(selection);
        const selected = await bridge(stagedEvents, family);
        await apply(page, selected.message_batches.at(-1));
        await page.locator('[data-molsysviewer-interaction-filters] button').filter({ hasText: "Active selection" }).click();
        await page.locator('[data-molsysviewer-interaction-slot-set="0"]').click();
    }
    await stageQuery(5, "A");
    await scope.selectOption("between");
    await create.click();
    assert.equal(await actionCount("create_interaction"), 0, "an unset calculation B must stop dispatch");
    await stageQuery(5, "B");
    await create.click();
    assert.equal(await actionCount("create_interaction"), 0, "overlapping calculation A/B must stop dispatch");
    await stageQuery(6, "B");
    await scope.selectOption("all");
    await page.locator('[data-molsysviewer-interaction-field="parameter-distance_threshold"]').fill("0.4");
    await page.locator('[data-molsysviewer-interaction-field="name"]').fill("whole");
    await openCreationForm(page);
    await page.locator('[data-molsysviewer-interaction-field="tag"]').fill("filtered");
    await create.click();
    const wholeEvent = await latest("create_interaction");
    assert.equal(wholeEvent.calculation.selection, "all");
    assert.ok(!("selection_2" in wholeEvent.calculation), "display B must not leak into calculation");
    assert.deepEqual(wholeEvent.filter.selection, [5]);
    assert.equal(wholeEvent.filter.mode, "involving_selection");
    const whole = await bridge([wholeEvent], family);
    assert.equal(whole.summary.analyses.find((item: any) => item.name === "whole").n_occurrences, 20);
    assert.equal(whole.summary.interactions.find((item: any) => item.tag === "filtered").n_observations, 1);
    await apply(page, whole.message_batches[0]);
    assert.match(await page.locator('[data-molsysviewer-interaction-set="filtered"]').textContent(), /1 drawn \/ 1 observations/);
    const displayMode = page.locator('[data-molsysviewer-interaction-filters] select').first();
    const modes = ["involving_selection", "within_selection", "across_selection_boundary", "between_selections"];
    assert.deepEqual(await displayMode.locator("option").evaluateAll(options => options.map(option => (option as HTMLOptionElement).value)), modes);
    for (const mode of modes) {
        await displayMode.selectOption(mode);
        await openCreationForm(page);
        await page.locator('[data-molsysviewer-interaction-field="tag"]').fill(`mode-${mode}`);
        await create.click();
        const request = await latest("create_interaction");
        assert.equal(request.filter.mode, mode);
        assert.deepEqual(request.filter.selection, [5]);
        assert.deepEqual(request.filter.selection_2, mode === "between_selections" ? [6] : null);
        const response = await bridge([wholeEvent, request], family);
        assert.equal(response.message_batches[1].find((message: any) => message.op === "interaction_action_result")?.ok, true);
        const item = response.summary.interactions.find((item: any) => item.tag === `mode-${mode}`);
        assert.equal(item.filter.mode, mode);
        if (mode !== "between_selections") assert.equal(item.n_observations, mode === "within_selection" ? 0 : 1);
        assert.equal(response.summary.analyses.find((item: any) => item.name === "whole").n_occurrences, 20);
        await apply(page, response.message_batches[1]);
    }
    await displayMode.selectOption("involving_selection");
    await page.locator('[data-molsysviewer-interaction-source="calculate"]').click();
    await scope.selectOption("a");
    await page.locator('[data-molsysviewer-interaction-field="name"]').fill("limited");
    await openCreationForm(page);
    await page.locator('[data-molsysviewer-interaction-field="tag"]').fill("limited");
    await create.click();
    const limitedEvent = await latest("create_interaction");
    assert.deepEqual(limitedEvent.calculation.selection, [5]);
    assert.ok(!("selection_2" in limitedEvent.calculation));
    const limited = await bridge([wholeEvent, limitedEvent], family);
    assert.equal(limited.summary.analyses.find((item: any) => item.name === "limited").n_occurrences, 0);
    assert.deepEqual(limited.calculation_scopes.limited.atom_indices, [5]);
    await apply(page, limited.message_batches[1]);
    assert.match(await page.locator('[data-molsysviewer-interaction-set="limited"]').textContent(), /Evaluated · no matching observations/);
    await page.locator('[data-molsysviewer-interaction-source="calculate"]').click();
    await scope.selectOption("between");
    await page.locator('[data-molsysviewer-interaction-field="name"]').fill("between");
    await openCreationForm(page);
    await page.locator('[data-molsysviewer-interaction-field="tag"]').fill("between");
    await create.click();
    const betweenEvent = await latest("create_interaction");
    assert.deepEqual(betweenEvent.calculation.selection, [5]);
    assert.deepEqual(betweenEvent.calculation.selection_2, [6]);
    const between = await bridge([betweenEvent], family);
    assert.equal(between.message_batches[0].find((message: any) => message.op === "interaction_action_result")?.ok, true);
    assert.equal(between.calculation_scopes.between.mode, "between");
    await apply(page, between.message_batches[0]);
    await page.locator('[data-molsysviewer-interaction-source="calculate"]').click();
    await page.locator('[data-molsysviewer-interaction-kind="true"]').selectOption("disulfide_candidate");
    const before = await actionCount("create_interaction");
    await create.click();
    assert.equal(await actionCount("create_interaction"), before, "an unsupported retained scope must stop dispatch");
    console.log("[E2E interactions calculation scope] query A/B, stale responses, 20 calculated/1 displayed, explicit restrictions passed");
}
async function checkCalculationForms(page: any) {
    const customPlane = { distance_threshold: "0.55", angle_threshold: "30", offset_threshold: "0.2", planarity_threshold: "0.01" };
    const cases: Array<{ system: string; kind?: string; criterion?: string; fields?: Record<string, string> }> = [
        { system: "hbond", fields: { distance_threshold: "0.4" } },
        { system: "hbond", criterion: "luzard_chandler", fields: { distance_threshold: "0.6", angle_threshold: "180" } },
        { system: "water_bridge", kind: "hbond", criterion: "baker_hubbard" },
        { system: "water_bridge", kind: "hbond", criterion: "wernet_nilsson" },
        { system: "disulfide_candidate" },
        { system: "ionic_contact", fields: { distance_threshold: "0.4" } },
        { system: "pi_pi" },
        { system: "pi_pi", criterion: "least_squares", fields: customPlane },
        { system: "pi_pi", criterion: "smarts_5_6" },
        { system: "cation_pi" },
        { system: "cation_pi", criterion: "three_atom_plane" },
        { system: "cation_pi", criterion: "least_squares", fields: customPlane },
        { system: "halogen_bond", fields: { "donor_angle_range-min": "130", "donor_angle_range-max": "180",
            "acceptor_angle_range-min": "80", "acceptor_angle_range-max": "140" } },
        { system: "hydrophobic_contact" },
        { system: "metal_coordination_candidate" },
        { system: "water_bridge" },
        { system: "water_bridge_2", kind: "water_bridge", fields: { order: "2" } },
    ];
    const selected = process.argv.find(arg => arg.startsWith("--calculation-families="))?.split("=")[1].split(",");
    const selectedCases = cases.filter(item => !selected || selected.includes(item.kind ?? item.system));
    assert.ok(selectedCases.length, "calculation selection must execute actual cases");
    for (const item of selectedCases) {
        const caseLabel = `${item.system}/${item.criterion ?? "default"}`;
        const started = Date.now();
        console.log(`[E2E interaction calculation] ${caseLabel}: preparing`);
        const fixture = await bridge([], item.system);
        await freshController(page);
        await apply(page, fixture.initial_messages);
        console.log(`[E2E interaction calculation] ${caseLabel}: controls`);
        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="interactions"]').click();
        await openCreationForm(page);
        await page.locator('[data-molsysviewer-interaction-kind="true"]').selectOption(item.kind ?? item.system);
        if (item.criterion) await page.locator('[data-molsysviewer-interaction-criterion="true"]').selectOption(item.criterion);
        assert.equal(await page.locator('[data-molsysviewer-interaction-field="parameters"]').count(), 0);
        if (item.system === "ionic_contact") {
            await page.locator('[data-molsysviewer-interaction-create="true"]').click();
            const requests = await page.evaluate(() => ((window as any).__messages || []).filter((m: any) => m.action === "create_interaction"));
            assert.equal(requests.length, 0, "required ionic cutoff must stop dispatch");
        }
        for (const [key, value] of Object.entries(item.fields ?? {})) {
            const field = page.locator(`[data-molsysviewer-interaction-field="parameter-${key}"]`);
            if (key === "order") await field.selectOption(value); else await field.fill(value);
        }
        if (item.system === "hbond" && !item.criterion) {
            const criterion = page.locator('[data-molsysviewer-interaction-criterion="true"]');
            await criterion.selectOption("luzard_chandler");
            assert.equal(await page.locator('[data-molsysviewer-interaction-field="parameter-distance_threshold"]').inputValue(), "");
            await page.locator('[data-molsysviewer-interaction-field="parameter-angle_threshold"]').fill("30");
            await criterion.selectOption("buch");
            assert.equal(await page.locator('[data-molsysviewer-interaction-field="parameter-angle_threshold"]').count(), 0);
            await page.locator('[data-molsysviewer-interaction-field="parameter-distance_threshold-unit"]').selectOption("angstroms");
            assert.equal(await page.locator('[data-molsysviewer-interaction-field="parameter-distance_threshold"]').inputValue(), "4");
            await apply(page, [fixture.initial_messages.find((message: any) => message.op === "set_interaction_summaries")]);
            assert.equal(await page.locator('[data-molsysviewer-interaction-field="parameter-distance_threshold"]').inputValue(), "4");
        }
        await page.locator('[data-molsysviewer-interaction-field="name"]').fill("form-analysis");
        await openCreationForm(page);
        await page.locator('[data-molsysviewer-interaction-field="tag"]').fill("form-set");
        if (item.system === "halogen_bond") await page.screenshot({ path: "/tmp/molsysviewer-interactions-calculation-controls.png" });
        await page.locator('[data-molsysviewer-interaction-create="true"]').click();
        const event = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "create_interaction"));
        assert.ok(event, `${item.system}/${item.criterion}: form did not dispatch`);
        assert.equal(event.calculation.kind, item.kind ?? item.system);
        if (item.system === "hbond" && !item.criterion) assert.deepEqual(event.calculation.parameters, { method: "buch", distance_threshold: "4 angstroms" });
        if (item.system === "water_bridge_2") assert.equal(event.calculation.parameters.order, 2);
        if (item.system === "halogen_bond") assert.deepEqual(event.calculation.parameters.donor_angle_range, ["130 degrees", "180 degrees"]);
        const calculated = await bridge([event], item.system);
        const reply = calculated.message_batches[0].find((message: any) => message.op === "interaction_action_result");
        assert.equal(reply?.ok, true, reply?.error_message ?? `${item.system}: missing calculation result`);
        const analysis = calculated.summary.analyses.find((item: any) => item.name === "form-analysis");
        assert.ok(analysis?.n_occurrences > 0, `${item.system}/${item.criterion}: no real calculated observations`);
        await apply(page, calculated.message_batches[0]);
        assert.equal(await page.locator('[data-molsysviewer-interaction-set="form-set"]').count(), 1);
        const refs = await page.evaluate(() => (window as any).Harness.inspectTaggedRefs((window as any).__controller, "interaction", "form-set"));
        assert.equal(refs.length, 1, `${item.system}: calculated set did not draw`);
        console.log(`[E2E interaction calculation] ${caseLabel}: passed in ${Date.now() - started} ms`);
    }
    return selectedCases.length;
}
function scientificFixture() {
    const result = spawnSync(process.env.PYTHON || "python", [resolve(dir, "../../../../devtools/qualify_interactions.py"),
        `/tmp/msv-interactions-scientific-browser-${process.pid}`, "--browser-fixture"],
        { encoding: "utf8", cwd: resolve(dir, "../../../.."), maxBuffer: 16 * 1024 * 1024 });
    assert.equal(result.status, 0, result.stderr || result.stdout);
    return JSON.parse(result.stdout);
}
async function checkFamilyGeometry(page: any) {
    console.log("[E2E interaction geometry] calculating family fixtures");
    const result = spawnSync(process.env.PYTHON || "python", [resolve(dir, "../../../../devtools/qualify_interaction_families.py"),
        `/tmp/msv-interaction-families-browser-${process.pid}`],
        { encoding: "utf8", cwd: resolve(dir, "../../../.."), maxBuffer: 64 * 1024 * 1024 });
    assert.equal(result.status, 0, result.stderr || result.stdout);
    const fixture = JSON.parse(result.stdout);
    assert.equal(fixture.cases.length, 10);
    console.log("[E2E interaction geometry] 10 family fixtures ready");
    for (const item of fixture.cases) {
        for (const messages of [item.initial_messages, item.restored_messages]) {
            await freshController(page);
            await apply(page, messages);
            const actual = await page.evaluate(() => {
                const c = (window as any).__controller;
                return (window as any).Harness.inspectTaggedRefs(c, "interaction", "family").map((ref: any) => {
                    const object = c.plugin.state.data.cells.get(ref.ref)?.obj?.data;
                    return { links: object?.sourceData?.links, observations: object?.sourceData?.interaction?.observations,
                        labels: object?.sourceData?.links?.map((link: any) => link.label) };
                });
            });
            assert.equal(actual.length, 1, item.kind);
            assert.equal(actual[0].links.length, item.expected.n_segments, item.kind);
            assert.equal(new Set(actual[0].observations.map((o: any) => o.occurrence_index)).size, item.expected.n_supported);
            actual[0].links.forEach((link: any, index: number) => {
                const expected = item.expected.links[index];
                assert.equal(actual[0].observations[index].occurrence_index, expected.occurrence_index);
                assert.equal(actual[0].observations[index].segment_index, expected.segment_index);
                assert.deepEqual(actual[0].observations[index].participants, expected.participants);
                for (const endpoint of ["start", "end"]) {
                    link[endpoint].forEach((v: number, axis: number) =>
                        assert.ok(Math.abs(v - expected[endpoint][axis] * 10) < 1e-5, `${item.kind}: ${endpoint}`));
                }
                if (expected.geometry === "participant_centroids") assert.match(actual[0].labels[index], /participant-centroid guide/);
            });
            await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
            await page.locator('[data-molsysviewer-group-panel-tab="interactions"]').click();
        await openCreationForm(page);
            const card = page.locator('[data-molsysviewer-interaction-set="family"]');
            assert.match(await card.textContent() || "", new RegExp(`${item.expected.n_supported} drawn / ${item.expected.n_observations} observations.*${item.expected.n_segments} segments`));
            const kinds = await page.locator('[data-molsysviewer-interaction-kind="true"] option').evaluateAll(options => options.map(option => (option as HTMLOptionElement).value));
            assert.equal(kinds.length, 9);
            if (item.kind.startsWith("water_bridge")) {
                // Distinct directed paths can share a mediator and endpoints.
                // Count occurrences independently from their graphical legs.
                assert.equal(item.expected.n_segments, item.expected.n_supported * (item.kind === "water_bridge" ? 2 : 3));
            }
        }
        console.log(`[E2E interaction geometry] ${item.kind}: original and restored meshes passed`);
    }
}
async function checkScientificGeometry(page: any) {
    console.log("[E2E interaction geometry] calculating periodic fixtures");
    const fixture = scientificFixture();
    console.log("[E2E interaction geometry] periodic fixtures ready");
    assert.ok(fixture.nonzero_image_observations > 0);
    const errors: string[] = [];
    page.on("pageerror", (error: Error) => errors.push(String(error)));
    for (const messages of [fixture.initial_messages, fixture.restored_messages]) {
        await freshController(page);
        await apply(page, messages);
        await apply(page, fixture.series);
        for (const frame of [0, 3, 2]) {
            await apply(page, [{ op: "set_trajectory_frame", index: frame }]);
            await page.waitForFunction((expectedFrame: number) => {
                const c = (window as any).__controller;
                const refs = (window as any).Harness.inspectTaggedRefs(c, "interaction", "real-hb");
                return refs.some((item: any) => c.plugin.state.data.cells.get(item.ref)?.obj?.data?.sourceData?.interaction?.frame === expectedFrame);
            }, frame);
            const meshes = await page.evaluate(() => {
                const c = (window as any).__controller;
                return (window as any).Harness.inspectTaggedRefs(c, "interaction", "real-hb").map((item: any) => {
                    const data = c.plugin.state.data.cells.get(item.ref)?.obj?.data?.sourceData;
                    return { ...item, links: data?.links, observations: data?.interaction?.observations };
                });
            });
            assert.equal(meshes.length, 1);
            assert.equal(meshes[0].exists, true);
            const expected = fixture.expected.filter((item: any) => item.frame === frame);
            assert.equal(meshes[0].links.length, expected.length);
            for (let index = 0; index < meshes[0].links.length; index++) {
                const occurrence = meshes[0].observations[index].occurrence_index;
                const observation = expected.find((item: any) => item.occurrence_index === occurrence);
                assert.ok(observation, `Unrecognized occurrence ${occurrence}`);
                for (const endpoint of ["start", "end"]) {
                    meshes[0].links[index][endpoint].forEach((value: number, axis: number) =>
                        assert.ok(Math.abs(value - observation[`${endpoint}_nm`][axis] * 10) < 1e-5));
                }
                assert.ok(Math.abs(meshes[0].links[index].radius - 0.2) < 1e-6);
            }
        }
        await page.screenshot({ path: `/tmp/msv-interactions-scientific-${messages === fixture.initial_messages ? "original" : "restored"}.png` });
        assert.deepEqual(errors, []);
    }
}
/** Reuse executable code only; dispose Mol* and construct a fresh scene each time. */
async function freshController(page: any) {
    if (!await page.evaluate(() => Boolean((window as any).Harness))) {
        await page.setContent('<div id="root" style="width:1000px;height:760px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
    }
    await page.evaluate(async () => {
        (window as any).__controller?.dispose();
        document.getElementById("root")!.replaceChildren();
        (window as any).__controller = await (window as any).Harness.createController("root");
    });
}
async function openCreationForm(page: any) {
    const form = page.locator("[data-molsysviewer-interaction-form]");
    if (!await form.evaluate((element: HTMLDetailsElement) => element.open)) await form.locator(":scope > summary").click();
    const options = form.locator("details").filter({ has: page.getByText("Representation name and layer (optional)", { exact: true }) }).first();
    if (!await options.evaluate((element: HTMLDetailsElement) => element.open)) await options.locator(":scope > summary").click();
}
async function apply(page: any, messages: unknown[]) {
    await page.evaluate(async list => { for (const msg of list) await (window as any).__controller.handleMessage(msg); }, messages);
}
async function inspect(page: any) {
    return page.evaluate(() => {
        const c = (window as any).__controller;
        return (window as any).Harness.inspectTaggedRefs(c, "interaction", "hb").map((item: any) => {
            const data = c.plugin.state.data.cells.get(item.ref)?.obj?.data?.sourceData;
            return { ...item, dashed: data?.dashed, links: data?.links, interaction: data?.interaction };
        });
    });
}
export async function runInteractionsSuite(chromium: typeof import("./e2e-browser").chromium, mode: "lifecycle" | "geometry" | "calculation") {
    const started = Date.now();
    fixtureWorker = new PythonFixtureBridge(resolve(dir, "interactions-subpanel-bridge.py"), resolve(dir, "../../../.."));
    const browser = await chromium.launch({ headless: true, executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome", chromiumSandbox: false,
        args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"] } as any);
    const page = await browser.newPage({ viewport: { width: 1100, height: 800 } });
    const errors: string[] = []; page.on("pageerror", error => errors.push(String(error)));
    try {
        if (mode === "calculation" || process.argv.includes("--calculation-forms")) {
            await checkCalculationAndDisplayScopes(page);
            const count = await checkCalculationForms(page);
            assert.deepEqual(errors, []);
            console.log(`[E2E interactions-subpanel calculation forms] ${count} real calculations passed`);
            return;
        }
        if (mode === "geometry") {
            await checkScientificGeometry(page);
            await checkFamilyGeometry(page);
            assert.deepEqual(errors, []);
            console.log("[E2E interactions geometry] passed");
            return;
        }
        const fixture = await bridge();
        await page.setContent('<div id="root" style="width:1000px;height:760px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => { (window as any).__controller = await (window as any).Harness.createController("root"); });
        await apply(page, fixture.initial_messages);
        let refs = await inspect(page);
        assert.equal(refs.length, 1); assert.equal(refs[0].dashed, true);
        assert.equal(refs[0].interaction.observations.length, 2);
        assert.deepEqual(refs[0].interaction.observations.map((item: any) => item.occurrence_index), [0, 1]);
        assert.deepEqual(refs[0].links[0].start, fixture.series[0].frames[0].links[0].start.map((v: number) => v * 10));
        const unitError = await page.evaluate(async message => {
            try { await (window as any).__controller.interactions.apply({ ...message, style: { ...message.style, radius_unit: "angstrom" } }); }
            catch (error) { return String(error); }
            return "not rejected";
        }, fixture.initial_messages.find((m: any) => m.op === "set_interaction_frame"));
        assert.match(unitError, /radius requires explicit nm/);
        assert.equal((await inspect(page))[0].links[0].radius, fixture.series[0].style.radius_nm * 10);
        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="interactions"]').click();
        await openCreationForm(page);
        const card = page.locator('[data-molsysviewer-interaction-set="hb"]');
        assert.match(await card.textContent() || "", /2 drawn \/ 3 observations.*1 unsupported/);
        await card.getByRole("button", { name: "Inspect", exact: true }).click();
        let event = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "inspect_interaction"));
        assert.equal(event.frame, 0); const inspected = await bridge([event]); await apply(page, inspected.message_batches[0]);
        assert.match(await card.textContent() || "", /#2 pi_stacking/);
        const observation = card.locator('[data-molsysviewer-interaction-observation="2"]');
        await observation.getByRole("button", { name: "Select participants", exact: true }).click();
        const selectedEvent = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "select_interaction_observation"));
        assert.equal(selectedEvent.occurrence_index, 2);
        assert.equal(selectedEvent.analysis_revision, inspected.inspection.analysis_revision);
        assert.equal(selectedEvent.query_revision, inspected.inspection.query_revision);
        const selected = await bridge([event, selectedEvent]);
        assert.deepEqual(selected.state.active_selection.atom_indices, [3, 4, 5, 6]);
        await apply(page, selected.message_batches[1]);
        await observation.getByRole("button", { name: "Focus participants", exact: true }).click();
        const focusEvent = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "focus_interaction_observation"));
        const focused = await bridge([event, focusEvent]);
        assert.ok(focused.message_batches[1].some((message: any) => message.op === "zoom"));
        await apply(page, focused.message_batches[1]);
        await card.getByRole("button", { name: "Hide", exact: true }).click();
        event = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "toggle_interaction_visibility"));
        const hidden = await bridge([event]); await apply(page, hidden.message_batches[0]);
        assert.ok((await inspect(page)).every((item: any) => item.hidden));
        const shown = await bridge([event, event]); await apply(page, shown.message_batches[1]);
        await page.screenshot({ path: "/tmp/molsysviewer-interactions-native.png" });
        // Live frame request + stale reply: geometry is immediately hidden.
        await page.evaluate(() => (window as any).__controller.interactions.onFrame(1));
        const request = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.event === "request_interaction_frame"));
        assert.equal(request.frame, 1); assert.ok((await inspect(page)).every((item: any) => item.hidden));
        await apply(page, [{ ...fixture.initial_messages.find((m: any) => m.op === "set_interaction_frame"), request_id: request.request_id }]);
        assert.ok((await inspect(page)).every((item: any) => item.hidden));
        const empty = await bridge([event, event, request]); await apply(page, empty.message_batches[2]);
        assert.equal((await inspect(page)).filter((item: any) => item.exists).length, 0);
        assert.match(await card.textContent() || "", /Evaluated.*no matching observations/);
        // Static series: playback carries no computation, including unevaluated frames.
        await apply(page, fixture.series);
        await page.evaluate(() => (window as any).__controller.interactions.onFrame(2));
        await page.waitForFunction(() => document.querySelector('[data-molsysviewer-interaction-set="hb"]')?.textContent?.includes("Not evaluated"));
        assert.equal((await inspect(page)).filter((item: any) => item.exists).length, 0);
        await page.evaluate(() => (window as any).__controller.interactions.onFrame(0));
        await page.waitForFunction(() => document.querySelector('[data-molsysviewer-interaction-set="hb"]')?.textContent?.includes("2 drawn"));
        assert.equal((await inspect(page)).filter((item: any) => item.exists).length, 1);
        await page.locator('[data-molsysviewer-interaction-field="calc-structures"]').fill("invalid");
        await page.locator('[data-molsysviewer-interaction-source="file"]').click();
        assert.ok(await page.locator('[data-molsysviewer-interaction-create="true"]').isDisabled());
        await page.locator('[data-molsysviewer-interaction-aligned="true"]').check();
        assert.ok(await page.locator('[data-molsysviewer-interaction-create="true"]').isEnabled());
        await page.locator('[data-molsysviewer-interaction-field="atom-map"]').fill("invalid");
        await page.locator('[data-molsysviewer-interaction-create="true"]').click();
        assert.ok(await page.locator('[data-molsysviewer-interaction-create="true"]').isEnabled(), "validation error stranded the form as busy");
        await page.locator('[data-molsysviewer-interaction-source="stored"]').click();
        await openCreationForm(page);
        await page.locator('[data-molsysviewer-interaction-field="tag"]').fill("hb-copy");
        await page.locator('[data-molsysviewer-interaction-create="true"]').click();
        assert.ok(await page.locator('[data-molsysviewer-interaction-create="true"]').isDisabled(), "duplicate submission was enabled");
        const create = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "create_interaction"));
        assert.equal(create.source, "stored"); assert.equal(create.analysis_name, "contacts"); assert.equal(create.tag, "hb-copy");
        const created = await bridge([event, event, create]); await apply(page, created.message_batches[2]);
        assert.equal(await page.locator('[data-molsysviewer-interaction-set="hb-copy"]').count(), 1);
        assert.ok(await page.locator('[data-molsysviewer-interaction-create="true"]').isEnabled());
        // A filter edit keeps the scientific signature but invalidates inspected rows.
        const inspectedBefore = (await bridge([{ action: "inspect_interaction", event: "interaction_context_action", tag: "hb", frame: 0, request_id: 1 }])).inspection;
        const filterEdit = { event: "interaction_context_action", action: "edit_interaction", tag: "hb", filter: { selection: [0], mode: "involving_selection" } };
        const filtered = await bridge([event, event, create, filterEdit]);
        await card.getByRole("button", { name: "Inspect", exact: true }).click();
        const inspectionRequest = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "inspect_interaction"));
        await apply(page, filtered.message_batches[3]);
        await apply(page, [{ op: "interaction_inspection", request_id: inspectionRequest.request_id, result: inspectedBefore }]);
        assert.doesNotMatch(await card.textContent() || "", /#2 pi_stacking/);
        // The real mesh pick retains its domain even with same-tag measurements.
        const picked = await page.evaluate(() => (window as any).Harness.openInteractionContext((window as any).__controller, "hb"));
        assert.equal(picked.context.kind, "interaction"); assert.equal(picked.click.kind, "interaction");
        assert.equal(picked.context.entity_ref.occurrence_index, 0);
        assert.equal(await page.getByRole("button", { name: "Delete Shape", exact: true }).count(), 0);
        await page.locator('[data-molsysviewer-context-submenu="Interaction set"]').click();
        await page.getByRole("menuitem", { name: "Delete Interaction Representation", exact: true }).click();
        const deletedEvent = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "delete_interaction"));
        assert.equal(deletedEvent.tag, "hb");
        const deleted = await bridge([event, event, create, filterEdit, deletedEvent]); await apply(page, deleted.message_batches[4]);
        const domains = await page.evaluate(() => {
            const c = (window as any).__controller;
            return { shape: (window as any).Harness.inspectTaggedRefs(c, "shape", "hb"), measurement: (window as any).Harness.inspectTaggedRefs(c, "measurement", "hb") };
        });
        assert.ok(domains.shape.some((item: any) => item.exists));
        assert.ok(domains.measurement.some((item: any) => item.exists));
        assert.equal((await inspect(page)).filter((item: any) => item.exists).length, 0);
        // Deletion during a real Mol* state write must not resurrect its mesh.
        const race = await page.evaluate(async message => {
            const c = (window as any).__controller; let removedDuringWrite = false;
            const subscription = c.plugin.state.data.events.object.created.subscribe((ev: any) => {
                if (ev.obj?.data?.sourceData?.tag === "race") { removedDuringWrite = true; c.interactions.drop("race"); }
            });
            try { const { projection_revision, request_id, ...frame } = message; await c.interactions.apply({ ...frame, tag: "race" }); }
            finally { subscription.unsubscribe(); }
            return { removedDuringWrite, remaining: [...c.plugin.state.data.cells.values()].filter((cell: any) => cell.obj?.data?.sourceData?.tag === "race").length };
        }, fixture.initial_messages.find((m: any) => m.op === "set_interaction_frame"));
        assert.equal(race.removedDuringWrite, true); assert.equal(race.remaining, 0);
        const history = [event, event, create, filterEdit, deletedEvent];
        await page.locator('[data-molsysviewer-interaction-source="calculate"]').click();
        await page.locator('[data-molsysviewer-interaction-field="name"]').fill("browser-buch");
        await page.locator('[data-molsysviewer-interaction-field="parameter-distance_threshold"]').fill("0.4");
        await page.locator('[data-molsysviewer-interaction-field="calc-structures"]').fill("current");
        await openCreationForm(page);
        await page.locator('[data-molsysviewer-interaction-field="tag"]').fill("browser-buch");
        await page.locator('[data-molsysviewer-interaction-create="true"]').click();
        const calculationEvent = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "create_interaction"));
        assert.equal(calculationEvent.source, "calculate"); history.push(calculationEvent);
        const calculated = await bridge(history); await apply(page, calculated.message_batches.at(-1));
        assert.ok(calculated.summary.analyses.find((item: any) => item.name === "browser-buch").n_occurrences > 0);
        assert.equal(await page.locator('[data-molsysviewer-interaction-set="browser-buch"]').count(), 1);
        await page.locator('[data-molsysviewer-interaction-source="file"]').click();
        await page.locator('[data-molsysviewer-interaction-field="name"]').fill("browser-file");
        await page.locator('[data-molsysviewer-interaction-field="filename"]').fill(fixture.fixture_file);
        await page.locator('[data-molsysviewer-interaction-field="file-analysis"]').fill("contacts");
        await page.locator('[data-molsysviewer-interaction-field="atom-map"]').fill("");
        await openCreationForm(page);
        await page.locator('[data-molsysviewer-interaction-field="tag"]').fill("browser-file");
        await page.locator('[data-molsysviewer-interaction-create="true"]').click();
        const fileEvent = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "create_interaction"));
        assert.equal(fileEvent.source, "file"); history.push(fileEvent);
        const imported = await bridge(history); await apply(page, imported.message_batches.at(-1));
        assert.equal(imported.summary.analyses.find((item: any) => item.name === "browser-file").n_occurrences, 3);
        assert.equal(await page.locator('[data-molsysviewer-interaction-set="browser-file"]').count(), 1);
        const filters = page.locator('[data-molsysviewer-interaction-filters="true"]');
        if (!await filters.evaluate((element: HTMLDetailsElement) => element.open)) await filters.locator(":scope > summary").click();
        await filters.locator("select").selectOption("between_selections");
        await filters.locator('input[type="checkbox"]').check();
        await filters.locator("select").selectOption("involving_selection");
        await openCreationForm(page);
        await page.locator('[data-molsysviewer-interaction-field="tag"]').fill("mode-reset");
        await page.locator('[data-molsysviewer-interaction-create="true"]').click();
        const resetModeEvent = await page.evaluate(() => [...((window as any).__messages || [])].reverse().find((m: any) => m.action === "create_interaction"));
        assert.equal(resetModeEvent.filter.exclusive, false); history.push(resetModeEvent);
        const resetMode = await bridge(history); await apply(page, resetMode.message_batches.at(-1));
        assert.equal(await page.locator('[data-molsysviewer-interaction-set="mode-reset"]').count(), 1);
        assert.deepEqual(errors, []);
        console.log("[E2E interactions-subpanel] passed");
    } finally {
        try { await browser.close(); } finally { await fixtureWorker.close(); }
        console.log(`[E2E interactions ${mode}] ${Date.now() - started} ms`);
    }
}
