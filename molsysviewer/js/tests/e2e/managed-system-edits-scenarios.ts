import assert from "node:assert";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { PythonFixtureBridge } from "./python-fixture-bridge";

const dir = dirname(fileURLToPath(import.meta.url));

/** Two real Mol* endpoints consume the actual Python synchronization states. */
export async function checkManagedSystemEdits(browser: any): Promise<void> {
    const bridge = new PythonFixtureBridge(resolve(dir, "managed-system-edits-bridge.py"), resolve(dir, "../../../.."));
    const first = await browser.newPage();
    const late = await browser.newPage();
    const apply = (page: any, messages: unknown[]) => page.evaluate(async items => {
        for (const item of items) await (window as any).__controller.handleMessage(item);
    }, messages);
    const setup = async (page: any) => {
        await page.setContent('<div id="root" style="width:800px;height:600px;position:relative"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async () => {
            (window as any).__controller = await (window as any).Harness.createController("root");
            (window as any).__messages.length = 0;
        });
    };
    const overlay = (page: any) => page.locator('[data-molsysviewer-system-sync="true"]');
    try {
        await setup(first);
        const initial = await bridge.request([], "initial");
        await apply(first, initial.messages);
        assert.equal(await overlay(first).isVisible(), false);
        const pending = await bridge.request([], "defer");
        assert.equal(pending.status.state, "pending");
        await apply(first, pending.messages);
        assert.equal(await overlay(first).isVisible(), true);
        assert.match(await overlay(first).innerText(), /molecular system has changed/);
        assert.equal(await first.evaluate(() => Array.from(document.querySelector("#root")!.children)
            .filter(child => !child.hasAttribute("data-molsysviewer-system-sync"))
            .every(child => (child as HTMLElement).inert)), true);

        await setup(late);
        const snapshot = await bridge.request([], "late_endpoint");
        await apply(late, snapshot.messages);
        assert.equal(await overlay(late).isVisible(), true);
        await overlay(late).getByRole("button", { name: "Update view" }).click();
        const events = await late.evaluate(() => (window as any).__messages.filter((event: any) =>
            event.event === "interaction_context_action" && event.action === "sync_system_edits"));
        assert.equal(events.length, 1);
        const updated = await bridge.request(events);
        assert.equal(updated.status.state, "synchronized");
        assert.equal(updated.status.target_revision, 1);
        for (const page of [first, late]) {
            await apply(page, updated.messages);
            assert.equal(await overlay(page).isVisible(), false);
            assert.equal(await page.evaluate(() => (window as any).__controller.getStructureData().elementCount), updated.atom_count);
            assert.equal(await page.evaluate(() => Array.from(document.querySelector("#root")!.children)
                .filter(child => !child.hasAttribute("data-molsysviewer-system-sync"))
                .every(child => !(child as HTMLElement).inert)), true);
        }
        const boxPending = await bridge.request([], "defer_box");
        assert.equal(boxPending.status.state, "pending");
        for (const page of [first, late]) await apply(page, boxPending.messages);
        await first.evaluate(() => (window as any).__messages.length = 0);
        await overlay(first).getByRole("button", { name: "Update view" }).click();
        const boxEvents = await first.evaluate(() => (window as any).__messages.filter((event: any) =>
            event.event === "interaction_context_action" && event.action === "sync_system_edits"));
        assert.equal(boxEvents.length, 1);
        const boxUpdated = await bridge.request(boxEvents);
        assert.equal(boxUpdated.status.target_revision, 2);
        for (const page of [first, late]) {
            await apply(page, boxUpdated.messages);
            assert.equal(await overlay(page).isVisible(), false);
            const size = await page.evaluate(() => {
                const structure = (window as any).__controller.getStructureData();
                return Array.from(structure.units[0].model._staticPropertyData.model_symmetry.spacegroup.cell.size);
            });
            assert.deepEqual(size, [30, 40, 50]);
        }
        const readerMount = await bridge.request([], "reader_mount");
        const mounted = readerMount.messages.find((item: any) => item.op === "mount_addon_panel");
        assert.deepEqual(mounted.read_only_actions, ["inspect"]);
        await apply(first, readerMount.messages);
        await overlay(first).evaluate(el => {
            (el as any).__readerBaseline = new Map(Array.from(el.parentElement!.children)
                .filter(child => child !== el).map(child => [child, (child as HTMLElement).inert]));
        });
        const readerPending = await bridge.request([], "reader_defer");
        await apply(first, readerPending.messages);
        const reader = overlay(first).locator('[data-molsysviewer-sync-reader="true"]');
        await reader.waitFor({ state: "visible" });
        const input = reader.locator("input");
        const inputIdentity = await input.elementHandle();
        await input.click();
        await first.keyboard.type("retained native reader");
        await first.evaluate(() => (window as any).__messages.length = 0);
        await reader.locator("[data-reader-write]").click();
        assert.equal(await first.evaluate(() => (window as any).__messages
            .filter((item: any) => item.event === "addon_panel_action").length), 0);
        await reader.locator("[data-reader-inspect]").focus();
        for (const key of ["n", "w", "h", "v", "Escape"]) await first.keyboard.press(key);
        assert.equal(await reader.isVisible(), true);
        await first.keyboard.press("Enter");
        const readEvents = await first.evaluate(() => (window as any).__messages
            .filter((item: any) => item.event === "addon_panel_action"));
        assert.equal(readEvents.length, 1);
        const read = await bridge.request(readEvents);
        assert.equal(read.status.state, "pending");
        await apply(first, read.messages);
        const report = JSON.parse(await reader.locator("output").innerText());
        assert.deepEqual(report.box[0], [[4, 0, 0], [0, 5, 0], [0, 0, 6]]);
        assert.equal(report.unit, "nm");
        assert.equal(report.draft, "retained native reader");
        // Old rendered cells remain untouched until the explicit recovery.
        assert.deepEqual(await first.evaluate(() => Array.from((window as any).__controller
            .getStructureData().units[0].model._staticPropertyData.model_symmetry.spacegroup.cell.size)), [30, 40, 50]);
        await first.evaluate(() => (window as any).__messages.length = 0);
        await overlay(first).getByRole("button", { name: "Update view" }).click();
        const recovery = await first.evaluate(() => (window as any).__messages.filter((event: any) =>
            event.event === "interaction_context_action" && event.action === "sync_system_edits"));
        const readerUpdated = await bridge.request(recovery);
        await apply(first, readerUpdated.messages);
        assert.equal(await overlay(first).isVisible(), false);
        assert.equal(await inputIdentity!.evaluate(el => el.isConnected && !!el.closest('[data-molsysviewer-addon-widget-host]')), true);
        assert.equal(await inputIdentity!.evaluate(el => (el as HTMLInputElement).value), "retained native reader");
        assert.equal(await overlay(first).evaluate(el => Array.from((el as any).__readerBaseline as Map<HTMLElement, boolean>)
            .every(([node, inert]) => !node.isConnected || node.inert === inert)), true);
        await inputIdentity!.dispose();
        console.log("[managed-edits] declared reader keys/native primary, old scene inertness and exact mounted-DOM restoration pass");
        console.log(`[managed-edits] coordinate/box receiving, addon setter=${Boolean(boxUpdated.addon_set)}`);
    } finally {
        await first.close();
        await late.close();
        await bridge.close();
    }
}
