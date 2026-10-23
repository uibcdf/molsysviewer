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
    } finally {
        await first.close();
        await late.close();
        await bridge.close();
    }
}
