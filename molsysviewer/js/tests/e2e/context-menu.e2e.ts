import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";

const dir = dirname(fileURLToPath(import.meta.url));

async function run() {
    // Real demo and Python scene snapshot: no fabricated molecular topology.
    const fixture = spawnSync(process.env.PYTHON || "python", ["-c", `
import json
import molsysviewer as msv
from molsysviewer.interactions import _to_plain
view = msv.demo["dialanine"]
view.whole.set_representation("ball-and-stick")
snapshot = view._build_embedded_runtime_snapshot()
view._ready = True
sent = []
view.widget.send = sent.append
echoes = {}
for name, action, parameters in [
    ("spin", "toggle_spin", {"enabled": True}),
    ("swing", "toggle_swing", {"enabled": True}),
    ("dark", "toggle_background", {"mode": "dark"}),
    ("light", "toggle_background", {"mode": "light"}),
]:
    sent.clear()
    view._handle_frontend_event({"event": "interaction_context_action", "action": action, **parameters})
    echoes[name] = list(sent)
print(json.dumps(_to_plain({"messages": snapshot, "echoes": echoes})))
view.close()
`], { cwd: resolve(dir, "../../../.."), encoding: "utf8" });
    assert.equal(fixture.status, 0, fixture.stderr || String(fixture.error));
    const { messages, echoes } = JSON.parse(fixture.stdout);
    const browser = await chromium.launch({ headless: true });
    try {
        const page = await browser.newPage();
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        await page.setContent('<div id="root" style="position:relative;width:700px;height:520px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await page.evaluate(async wire => {
            const w = window as any;
            const c = await w.Harness.createController("root");
            w.__controller = c;
            for (const message of wire) await c.handleMessage(message, { throwOnError: true });
        }, messages);
        await page.waitForFunction(() => (window as any).__controller.plugin.canvas3d?.reprCount.value > 0);

        // The System strip opens the same production menu as a canvas pick.
        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        const firstGroup = page.locator('[data-molsysviewer-group-item="true"]').first();
        await firstGroup.click();
        const selectionBefore = await page.evaluate(() => JSON.stringify((window as any).__controller.currentActiveSelection));
        const context = page.locator('[data-molsysviewer-context-menu="true"]');
        await firstGroup.click({ button: "right" });
        assert.match(await context.locator('[data-molsysviewer-context-menu-title]').innerText(), /\S+\s+\d+.*chain/);
        assert.equal(await context.locator('[data-molsysviewer-context-action="distance"]:visible').count(), 0);
        assert.equal(await context.locator('[data-molsysviewer-context-submenu="Measure"]').count(), 1);
        const stateBefore = await page.evaluate(() => ({
            selection: JSON.stringify((window as any).__controller.currentActiveSelection),
            panel: (window as any).__controller.groupPanel.isExpanded(),
            events: (window as any).__messages.filter((m: any) => m.event === "interaction_context_action").length,
        }));
        assert.equal(stateBefore.selection, selectionBefore);

        // Navigate a submenu using only keys, then dismiss one level at a time.
        await context.locator('[data-molsysviewer-context-submenu="Measure"]').focus();
        await page.keyboard.press("ArrowRight");
        assert.equal(await context.getByRole("menu", { name: "Measure", exact: true }).isVisible(), true);
        assert.equal(await context.getByRole("menuitem", { name: "Distance", exact: true }).isVisible(), true);
        await page.keyboard.press("End");
        assert.equal(await page.evaluate(() => document.activeElement?.textContent), "Dihedral (Representative Atom)");
        await page.keyboard.press("Home");
        assert.equal(await page.evaluate(() => document.activeElement?.textContent), "‹ Back");
        await page.keyboard.press("Escape");
        assert.equal(await context.getByRole("menuitem", { name: "Focus Target", exact: true }).isVisible(), true);
        assert.equal(await page.evaluate(() => document.activeElement?.getAttribute("data-molsysviewer-context-submenu")), "Measure");
        await page.keyboard.press("Escape");
        assert.equal(await context.isVisible(), false);
        const afterEscape = await page.evaluate(() => ({
            selection: JSON.stringify((window as any).__controller.currentActiveSelection),
            panel: (window as any).__controller.groupPanel.isExpanded(),
            events: (window as any).__messages.filter((m: any) => m.event === "interaction_context_action").length,
            focusInViewer: document.getElementById("root")!.contains(document.activeElement),
        }));
        assert.equal(afterEscape.selection, stateBefore.selection);
        assert.equal(afterEscape.panel, stateBefore.panel);
        assert.equal(afterEscape.events, stateBefore.events);
        assert.equal(afterEscape.focusInViewer, true);

        // View controls exist on molecular targets; root size is independent of
        // the saved collection, and the collection route selects its Studio tab.
        await page.evaluate(() => {
            const c = (window as any).__controller;
            c.savedSelections = Array.from({ length: 1000 }, (_, i) => ({ tag: `saved-${i}`, atom_count: 1, atom_indices: [0] }));
        });
        await firstGroup.click({ button: "right" });
        assert.equal(await context.locator('[data-molsysviewer-context-submenu="View"]').count(), 1);
        assert.equal(await context.locator('[data-molsysviewer-saved-selection]').count(), 0);
        assert.ok(await context.locator('[role="menu"]:visible button:visible').count() <= 12);
        await context.getByRole("menuitem", { name: "Saved selections in Studio…", exact: true }).click();
        assert.equal(await page.evaluate(() => (window as any).__controller.groupPanel.activeTab), "selection");
        assert.equal(await context.isVisible(), false);
        assert.equal(await page.evaluate(() => (window as any).__messages.some((m: any) => m.event === "interaction_context_action" && m.action === "open_navigate")), false);

        // The public Python viewport handlers echo explicit requested states,
        // so their acknowledgement cannot accidentally flip a local toggle.
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        for (const [name, label, action] of [["spin", "Start Automatic Rotation", "toggle_spin"], ["swing", "Start Swing", "toggle_swing"]]) {
            await firstGroup.click({ button: "right" });
            await context.locator('[data-molsysviewer-context-submenu="View"]').click();
            await context.getByRole("menuitem", { name: label, exact: true }).click();
            const request = await page.evaluate(a => [...(window as any).__messages].reverse().find((m: any) => m.action === a), action);
            assert.equal(request.enabled, true);
            await page.evaluate(async wire => {
                for (const message of wire) await (window as any).__controller.handleMessage(message, { throwOnError: true });
            }, echoes[name]);
            assert.equal(await page.evaluate(field => (window as any).__controller.scene[field], name === "spin" ? "isSpinActive" : "isSwingActive"), true);
        }
        await firstGroup.click({ button: "right" });
        await context.locator('[data-molsysviewer-context-submenu="View"]').click();
        await context.locator('[data-molsysviewer-context-action="toggle_background"]').click();
        const background = await page.evaluate(() => [...(window as any).__messages].reverse().find((m: any) => m.action === "toggle_background"));
        assert.ok(["light", "dark"].includes(background.mode));
        await page.evaluate(async wire => {
            for (const message of wire) await (window as any).__controller.handleMessage(message, { throwOnError: true });
        }, echoes[background.mode]);
        assert.equal(await page.evaluate(() => (window as any).__controller.scene.isDarkMode), background.mode === "dark");

        // History has its own authoritative availability and emits exactly once.
        await page.evaluate(async () => {
            const c = (window as any).__controller;
            await c.handleMessage({ op: "set_history_state", can_undo: false, can_redo: false });
            c.contextMenu.open({ event: "interaction_context_menu", kind: "empty" }, 690, 510,
                c.currentActiveSelection, null, [], [], [], [], c.contextHistoryState);
        });
        assert.equal(await context.getByRole("menuitem", { name: "Undo", exact: true }).isDisabled(), true);
        await page.evaluate(async () => (window as any).__controller.handleMessage({ op: "set_history_state", can_undo: true, can_redo: false }));
        await context.getByRole("menuitem", { name: "Undo", exact: true }).click();
        assert.equal(await page.evaluate(() => (window as any).__messages.filter((m: any) => m.event === "scene_history_undo").length), 1);

        // An atomless object cannot claim focus by atom indices, and a
        // shape-only selection cannot run molecular queries or creation.
        await page.evaluate(() => {
            const c = (window as any).__controller;
            c.contextMenu.open({ event: "interaction_context_menu", kind: "shape", tag: "free", atom_indices: [] }, 690, 510,
                { ...c.currentActiveSelection, source_kind: "shape", atom_indices: [], count_atoms: 0, count_shapes: 1 });
        });
        assert.equal(await context.getByRole("menuitem", { name: "Focus Target", exact: true }).isDisabled(), true);
        await context.locator('[data-molsysviewer-context-submenu^="Active selection"]').click();
        assert.equal(await context.getByRole("menuitem", { name: "Create Region from Selection…", exact: true }).isDisabled(), true);
        const menuBox = await context.boundingBox();
        const hostBox = await page.locator("#root").boundingBox();
        assert.ok(menuBox && hostBox);
        assert.ok(menuBox.x >= hostBox.x && menuBox.y >= hostBox.y);
        assert.ok(menuBox.x + menuBox.width <= hostBox.x + hostBox.width + 1);
        assert.ok(menuBox.y + menuBox.height <= hostBox.y + hostBox.height + 1);
        await page.keyboard.press("Escape");
        await page.keyboard.press("Escape");

        // Callback and menu no longer send the same destructive request twice.
        await page.evaluate(() => {
            const c = (window as any).__controller;
            c.contextMenu.open({ event: "interaction_context_menu", kind: "measurement", tag: "probe", atom_indices: [0, 1] }, 100, 100);
        });
        await context.getByRole("menuitem", { name: "Hide Measurement", exact: true }).click();
        assert.equal(await page.evaluate(() => (window as any).__messages.filter((m: any) => m.event === "interaction_context_action" && m.action === "hide_measurement").length), 1);

        // Escape inside an open menu does not cancel an already active tool.
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        await firstGroup.click({ button: "right" });
        await context.locator('[data-molsysviewer-context-submenu="Measure"]').click();
        await context.getByRole("menuitem", { name: "Distance", exact: true }).click();
        await firstGroup.click({ button: "right" });
        await page.keyboard.press("Escape");
        assert.equal(await context.isVisible(), false);
        assert.equal(await page.evaluate(() => (window as any).__controller.measurementTools.isActive()), true);
        await page.keyboard.press("Escape");
        assert.equal(await page.evaluate(() => (window as any).__controller.measurementTools.isActive()), false);

        assert.deepEqual(errors, []);
        console.log("[E2E context menu] real dialanine rendering; compact submenus, keys/Escape, selection preservation, Studio, history, scope guards and single dispatch pass");
    } finally { await browser.close(); }
}

run().catch(error => { console.error(error); process.exit(1); });
