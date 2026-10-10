import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";
import { PythonFixtureBridge } from "./python-fixture-bridge";

const dir = dirname(fileURLToPath(import.meta.url));
async function run() {
    const bridge = new PythonFixtureBridge(resolve(dir, "studio-usability-bridge.py"), resolve(dir, "../../../.."));
    const browser = await chromium.launch();
    try {
        const fixture = await bridge.request([], "refinement");
        const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
        const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
        const apply = (messages: any[]) => page.evaluate(async messages => { for (const message of messages) await (window as any).__controller.handleMessage(message, { throwOnError: true }); }, messages);
        await page.setContent('<div id="root" style="position:relative;width:1100px;height:850px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => { await (window as any).Harness.createController("root", { panelModeStyle: "floating-unified" }); });
        await apply(fixture.initial_messages);
        await page.waitForFunction(() => (window as any).__controller.plugin.canvas3d?.reprCount.value > 0);
        await apply(fixture.selection_messages);
        await page.evaluate(() => (window as any).__controller.setPanelMode("navigate", true));
        const open = (key: string) => page.evaluate(key => (window as any).__controller.groupPanel.openSection(key), key);
        const section = (key: string) => page.locator(`[data-molsysviewer-group-panel-section="${key}"]`);
        const events: any[] = [];
        const lastAction = (action: string) => page.evaluate(action => [...(window as any).__messages].reverse().find((message: any) => message.action === action), action);
        const reply = async (event: any) => {
            events.push(event); const result = await bridge.request(events, "refinement");
            await apply(result.message_batches.at(-1)); return result;
        };
        const creation = (key: string) => section(key).locator('details[data-molsysviewer-disclosure="creation"]');
        await open("shapes");
        assert.equal(await creation("shapes").evaluate((element: HTMLDetailsElement) => element.open), false);
        await creation("shapes").locator(":scope > summary").click();
        const create = page.locator('[data-molsysviewer-shape-create-btn]');
        assert.ok(await create.isDisabled(), "A sphere needs a staged anchor");
        await page.locator('[data-molsysviewer-shape-anchor-btn]').click();
        await page.getByLabel("Shape tag", { exact: true }).fill("alpha-one");
        await create.click(); const failed = await lastAction("create_shape");
        const failureReply = await reply(failed);
        assert.ok(failureReply.message_batches.at(-1).some((message: any) => message.op === "studio_action_result" && !message.ok));
        assert.equal(await page.getByLabel("Shape tag", { exact: true }).inputValue(), "alpha-one");
        assert.ok(await create.isEnabled(), "A backend failure keeps staged anchors available");
        await page.getByLabel("Shape tag", { exact: true }).fill("new-sphere");
        await create.click(); await reply(await lastAction("create_shape"));
        assert.equal(await page.getByLabel("Shape tag", { exact: true }).inputValue(), "");
        assert.ok(await create.isDisabled(), "Only success clears the staging anchors");
        await page.waitForFunction(() => document.querySelector('[data-molsysviewer-shape-tag="new-sphere"]'));

        await page.getByLabel("Shape type", { exact: true }).selectOption("add_displacement_vectors");
        await page.getByRole("button", { name: "Anchor 1 (Start)", exact: true }).click();
        await reply({ action: "apply_selection_query", expression: "atom_index in [7, 8]", syntax: "MolSysMT", op: "replace" });
        await page.getByRole("button", { name: "Anchor 2 (End)", exact: true }).click();
        await page.getByLabel("Shape tag", { exact: true }).fill("snapshot-arrow");
        assert.ok(await page.getByLabel("Arrow radius scale", { exact: true }).isVisible());
        assert.match(await section("shapes").innerText(), /geometry is fixed/);
        await create.click(); await reply(await lastAction("create_shape"));
        await page.waitForFunction(() => (window as any).Harness.inspectTaggedRefs((window as any).__controller, "shape", "snapshot-arrow").some((item: any) => item.exists));

        // Searching and marking rows leave molecular selection and scene actions unchanged.
        const messageCount = await page.evaluate(() => (window as any).__messages.length);
        const search = section("shapes").getByLabel("Search saved shapes", { exact: true });
        await search.fill("alpha");
        assert.equal(await section("shapes").locator('[data-molsysviewer-shape-tag]:visible').count(), 2);
        await section("shapes").locator('[data-molsysviewer-list-management] > summary').click();
        await section("shapes").getByRole("button", { name: "Mark matches", exact: true }).click();
        assert.equal(await section("shapes").locator('[data-molsysviewer-list-mark]:checked').count(), 2);
        assert.equal(await page.evaluate(() => (window as any).__messages.length), messageCount);
        // Changing search does not discard marked targets hidden by the filter.
        await search.fill("beta");
        await section("shapes").getByRole("button", { name: "Hide marked", exact: true }).click();
        const hidden = await lastAction("batch_scene_objects"); assert.deepEqual(hidden.tags, ["alpha-one", "alpha-two"]);
        await reply(hidden);
        assert.equal(await section("shapes").locator('[data-molsysviewer-shape-tag="beta"]').evaluate(element => element.style.opacity), "1");
        await reply({ event: "scene_history_undo" });
        const restoredAnnotations = await page.evaluate(() => (window as any).Harness.inspectTaggedRefs((window as any).__controller, "annotation", "alpha-one"));
        assert.ok(restoredAnnotations.some((item: any) => item.exists), "Undo must restore actual annotation state cells");
        await search.fill("");
        assert.equal(await section("shapes").locator('[data-molsysviewer-shape-tag="alpha-one"]').evaluate(element => element.style.opacity), "1");

        // An unfocused secondary draft survives reply, tab and structure updates.
        await open("selection");
        await page.locator('[data-molsysviewer-saved-selection-rename="alpha-one"]').click();
        let editor = page.locator('[data-molsysviewer-saved-selection-editor="alpha-one:rename"]');
        await editor.fill("unfinished selection"); await editor.evaluate((element: HTMLInputElement) => element.setSelectionRange(4, 8));
        await reply({ action: "set_trajectory_frame", index: 1 });
        assert.equal(await editor.inputValue(), "unfinished selection");
        assert.deepEqual(await editor.evaluate((element: HTMLInputElement) => [element.selectionStart, element.selectionEnd]), [4, 8]);
        await open("whole"); await reply({ action: "set_trajectory_frame", index: 2 }); await open("selection");
        assert.equal(await editor.inputValue(), "unfinished selection");
        await editor.press("Escape");
        assert.equal(await editor.isVisible(), false);
        await open("annotations");
        await page.locator('[data-molsysviewer-annotation-more="alpha-one"]').click();
        const rename = page.locator('[data-molsysviewer-annotation-rename-input="alpha-one"]');
        await rename.fill("unfinished annotation"); await section("annotations").getByLabel("Search saved annotations", { exact: true }).focus();
        await reply({ action: "set_trajectory_frame", index: 0 });
        assert.equal(await rename.inputValue(), "unfinished annotation");
        await open("whole"); await reply({ action: "set_trajectory_frame", index: 1 }); await open("annotations");
        assert.equal(await rename.inputValue(), "unfinished annotation");
        assert.equal(await creation("annotations").evaluate((element: HTMLDetailsElement) => element.open), false);
        await creation("annotations").locator(":scope > summary").click();
        const advanced = section("annotations").locator('[data-molsysviewer-disclosure="annotation-advanced"]');
        await advanced.locator(":scope > summary").click();
        await reply({ action: "set_trajectory_frame", index: 2 });
        assert.ok(await advanced.evaluate((element: HTMLDetailsElement) => element.open));

        // A deleted target drops its editor even while this tab is hidden.
        await open("whole"); await reply({ action: "delete_annotation", tag: "alpha-one" });
        await reply({ event: "scene_history_undo" }); await open("annotations");
        assert.equal(await rename.count(), 0);
        await page.locator('[data-molsysviewer-annotation-more="alpha-one"]').click();
        assert.equal(await rename.inputValue(), "alpha-one");

        // Destruction is confirmed with the exact captured target names; Cancel is inert.
        await open("interactions");
        await section("interactions").locator('[data-molsysviewer-list-management] > summary').click();
        await section("interactions").getByRole("button", { name: "Mark matches", exact: true }).click();
        await section("interactions").getByRole("button", { name: "Delete marked", exact: true }).click();
        const confirmation = section("interactions").locator('[data-molsysviewer-list-confirmation]');
        assert.match(await confirmation.innerText(), /hbonds.*Stored analyses are kept/);
        const beforeRemark = await page.evaluate(() => (window as any).__messages.length);
        await section("interactions").getByRole("button", { name: "Mark matches", exact: true }).click();
        assert.equal(await confirmation.count(), 0, "Changing marks invalidates a captured deletion confirmation");
        assert.equal(await page.evaluate(() => (window as any).__messages.length), beforeRemark);
        await section("interactions").getByRole("button", { name: "Delete marked", exact: true }).click();
        const beforeCancel = await page.evaluate(() => (window as any).__messages.length);
        await confirmation.getByRole("button", { name: "Cancel", exact: true }).click();
        assert.equal(await page.evaluate(() => (window as any).__messages.length), beforeCancel);
        await section("interactions").getByRole("button", { name: "Delete marked", exact: true }).click();
        await confirmation.getByRole("button", { name: "Confirm deletion", exact: true }).click();
        await reply(await lastAction("batch_scene_objects"));
        assert.equal(await section("interactions").locator('[data-molsysviewer-interaction-set]').count(), 0);
        const analyses = section("interactions").locator('[data-molsysviewer-interaction-analyses]');
        await analyses.locator(":scope > summary").click();
        assert.ok((await analyses.innerText()).includes("review"), "Stored analyses remain after visual set deletion");
        await analyses.getByLabel("Search stored analyses", { exact: true }).fill("no-such-analysis");
        assert.equal(await analyses.locator('[data-molsysviewer-stored-analysis]:visible').count(), 0);
        await analyses.getByLabel("Search stored analyses", { exact: true }).fill("review");
        assert.equal(await analyses.locator('[data-molsysviewer-stored-analysis]:visible').count(), 1);
        for (const [key, domain, attribute, query] of [
            ["selection", "selections", "saved-selection-card", "alpha"],
            ["regions", "regions", "region-card", "alpha"],
            ["annotations", "annotations", "annotation-tag", "alpha"],
            ["measures", "measurements", "measurement-tag", "alpha"],
            ["layers", "layers", "layer-card", "presentation"],
        ]) {
            await open(key);
            const field = section(key).getByLabel(`Search saved ${domain}`, { exact: true });
            await field.fill(query);
            assert.equal(await section(key).locator(`[data-molsysviewer-${attribute}]:visible`).count(), key === "layers" ? 1 : 2);
            await field.fill("no-such-saved-object");
            assert.equal(await section(key).locator(`[data-molsysviewer-${attribute}]:visible`).count(), 0);
            await field.fill("");
            const unnamed = await section(key).locator('input:not([aria-label]):not([aria-labelledby]), select:not([aria-label]):not([aria-labelledby])').evaluateAll(fields => fields.filter(field => !field.closest("label")).length);
            assert.equal(unnamed, 0, `${key} fields must have accessible names`);
        }
        for (const [key, attribute] of [["layers", "layer-create-input"], ["measures", "measurement-name-input"]]) {
            await open(key); const disclosure = creation(key);
            await disclosure.locator(":scope > summary").click();
            const draft = section(key).locator(`[data-molsysviewer-${attribute}]`);
            await draft.fill("not submitted");
            await open("whole"); await reply({ action: "set_trajectory_frame", index: 0 }); await open(key);
            assert.equal(await draft.inputValue(), "not submitted", `${key} creation draft survives tab and projection`);
        }
        await page.screenshot({ path: "/tmp/msv-studio-list-workflows.png" });
        assert.deepEqual(errors, []);
        await page.evaluate(() => (window as any).__controller.dispose());
    } finally { await bridge.close(); await browser.close(); }
    console.log("Studio saved-list workflows: real Python creation, filtering, batches, undo and persistent drafts passed");
}
run().catch(error => { console.error(error); process.exit(1); });
