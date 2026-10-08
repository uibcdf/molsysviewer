import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";

const dir = dirname(fileURLToPath(import.meta.url));

function objectBridge(events: unknown[] = []) {
    const result = spawnSync(process.env.PYTHON || "python", ["-c", `
import json, sys
import molsysmt as msm
import molsysviewer as msv
from molsysviewer.interactions import _to_plain
view = msv.demo["dialanine"]
records = [{"structure_index": 0, "interaction_type": "a_unsupported", "participants": [
    {"role": "ring", "atom_indices": [3, 4]}, {"role": "ring", "atom_indices": [5, 6]}]}]
records.extend({"structure_index": 0, "interaction_type": "hbond", "participants": [
    {"role": role, "atom_indices": [atom]} for role, atom in zip(["donor", "hydrogen", "acceptor"], [0, 1, 2])],
    "measurements": {"distance": 0.2 + index / 1000}} for index in range(61))
analysis = msm.Interactions.from_records(records, n_atoms=view.molsys.get_n_atoms(), n_structures=1,
    evaluated_structure_indices=[0], method="synthetic_menu_identity", measure_units={"distance": "nm"})
view.interactions.attach(analysis, name="parallel", assume_aligned=True)
view.interactions.add("parallel", tag="parallel-set")
view.annotations.add(text="Menu annotation", atom_indices=[3, 4], tag="menu-note")
view.shapes.add_sphere(center=msv.pyunitwizard.quantity([3, 3, 3], "nm"), radius="0.3 nm", tag="menu-sphere")
view.measurements.add_distance([0], [1], tag="menu-distance")
view.measurements.add_distance([1], [2], tag="menu-sphere")
view.active_selection.set([9])
initial = view._build_embedded_runtime_snapshot()
view._ready = True
sent = []
view.widget.send = sent.append
for event in json.load(sys.stdin):
    view._handle_frontend_event(event)
print(json.dumps(_to_plain({"initial": initial, "messages": sent, "selection": view.active_selection.atom_indices,
    "analyses": view.interactions.analyses(), "sets": view.interactions.records()})))
view.close()
`], { cwd: resolve(dir, "../../../.."), input: JSON.stringify(events), encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr || String(result.error));
    return JSON.parse(result.stdout);
}

async function run() {
    // Real demo and Python scene snapshot: no fabricated molecular topology.
    const fixture = spawnSync(process.env.PYTHON || "python", ["-c", `
import json
import molsysviewer as msv
from molsysviewer.interactions import _to_plain
view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
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
        assert.equal(await page.evaluate(() => document.activeElement?.textContent), "Dihedral");
        await page.keyboard.press("Home");
        assert.equal(await page.evaluate(() => document.activeElement?.textContent), "Distance");
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

        // Click-driven parallel cards: preserve the parent and bound both cards.
        await firstGroup.click({ button: "right" });
        const rootMenu = context.locator('[data-molsysviewer-menu-page]').first();
        const measureTrigger = context.locator('[data-molsysviewer-context-submenu="Measure"]');
        const rootBefore = await rootMenu.boundingBox();
        await measureTrigger.hover();
        assert.equal(await context.locator('[data-molsysviewer-menu-page]:visible').count(), 1);
        await measureTrigger.click();
        assert.equal(await rootMenu.isVisible(), true);
        assert.deepEqual(await rootMenu.boundingBox(), rootBefore);
        assert.equal(await measureTrigger.getAttribute("aria-expanded"), "true");
        assert.equal(await context.locator('[data-molsysviewer-menu-page]:visible').count(), 2);
        await measureTrigger.click();
        assert.equal(await context.locator('[data-molsysviewer-menu-page]:visible').count(), 1);
        await measureTrigger.click();
        await context.locator('[data-molsysviewer-context-submenu="Create"]').click();
        assert.equal(await context.getByRole("menu", { name: "Measure", exact: true }).isVisible(), false);
        assert.equal(await context.locator('[data-molsysviewer-menu-page]:visible').count(), 2);
        await context.getByRole("menuitem", { name: "Region from Target…", exact: true }).click();
        assert.equal(await rootMenu.isVisible(), true);
        assert.equal(await context.getByRole("dialog", { name: "New Region" }).isVisible(), true);
        await context.getByPlaceholder("Region tag (optional)").fill("unsent-draft");
        await page.locator("#root").evaluate(el => { el.style.width = "430px"; el.style.height = "360px"; });
        await page.waitForFunction(() => document.querySelector('[data-molsysviewer-context-scroll]')?.getAttribute("data-molsysviewer-menu-layout") === "inline");
        assert.equal(await rootMenu.isVisible(), false);
        assert.equal(await context.getByPlaceholder("Region tag (optional)").inputValue(), "unsent-draft");
        await page.keyboard.press("Escape");
        assert.equal(await context.getByRole("menu", { name: "Create", exact: true }).isVisible(), true);
        await context.getByRole("menuitem", { name: "‹ Back", exact: true }).click();
        assert.equal(await rootMenu.isVisible(), true);
        await page.locator("#root").evaluate(el => { el.style.width = "700px"; el.style.height = "520px"; });
        await page.waitForFunction(() => document.querySelector('[data-molsysviewer-context-scroll]')?.getAttribute("data-molsysviewer-menu-layout") === "lateral");
        await page.keyboard.press("Escape");
        assert.equal(await page.evaluate(() => JSON.stringify((window as any).__controller.currentActiveSelection)), selectionBefore);
        assert.equal(await page.evaluate(() => (window as any).__messages.filter((m: any) => m.event === "interaction_context_action").length), stateBefore.events);

        // At either edge the child is adjacent, flips left, and stays in canvas.
        for (const x of [5, 350, 695]) for (const y of [5, 515]) {
            await page.evaluate(({ x, y }) => {
                const c = (window as any).__controller;
                const host = document.getElementById("root")!.getBoundingClientRect();
                c.contextMenu.open({ event: "interaction_context_menu", kind: "empty" }, host.left + x, host.top + y,
                    c.currentActiveSelection, null, [], [], [], [], c.contextHistoryState);
            }, { x, y });
            await context.locator('[data-molsysviewer-context-submenu="View"]').click();
            const main = await rootMenu.boundingBox();
            const child = await context.getByRole("menu", { name: "View", exact: true }).boundingBox();
            const host = await page.locator("#root").boundingBox();
            assert.ok(main && child && host);
            assert.ok(Math.abs(main.x + main.width - child.x - 1) < 2 || Math.abs(child.x + child.width - main.x - 1) < 2);
            for (const card of [main, child]) {
                assert.ok(card.x >= host.x && card.y >= host.y);
                assert.ok(card.x + card.width <= host.x + host.width + 1);
                assert.ok(card.y + card.height <= host.y + host.height + 1);
            }
            if (x === 695) assert.ok(child.x < main.x);
            await page.keyboard.press("Escape");
            await page.keyboard.press("Escape");
        }

        // Work on residue B while the working selection remains residue A.
        const secondGroup = page.locator('[data-molsysviewer-group-item="true"]').nth(1);
        const contextualRequests: any[] = [];
        const latestRequest = () => page.evaluate(() => [...(window as any).__messages].reverse()
            .find((message: any) => message.event === "interaction_context_action"));
        await secondGroup.click({ button: "right" });
        await context.getByRole("menuitem", { name: "Inspect Target…", exact: true }).click();
        assert.equal(await page.locator('[data-molsysviewer-context-inspector]').isVisible(), true);
        assert.equal(await page.evaluate(() => JSON.stringify((window as any).__controller.currentActiveSelection)), selectionBefore);
        await secondGroup.click({ button: "right" });
        await context.locator('[data-molsysviewer-context-submenu="Create"]').click();
        await context.getByRole("menuitem", { name: "Region from Target…", exact: true }).click();
        assert.deepEqual(await context.locator('[data-molsysviewer-context-target-scope] option').allTextContents(),
            ["Target atoms", "Pointed atom", "Group", "Chain"]);
        await context.getByLabel("Target atom scope").selectOption("group");
        await context.getByPlaceholder("Region tag (optional)").fill("context-residue");
        await context.getByRole("button", { name: "Create Region", exact: true }).click();
        contextualRequests.push(await latestRequest());
        await secondGroup.click({ button: "right" });
        await context.locator('[data-molsysviewer-context-submenu="Create"]').click();
        await context.getByRole("menuitem", { name: "Annotation from Target…", exact: true }).click();
        await context.getByPlaceholder("Label text").fill("Residue B");
        await context.getByRole("button", { name: "Create Label", exact: true }).click();
        contextualRequests.push(await latestRequest());
        assert.equal(await page.evaluate(() => JSON.stringify((window as any).__controller.currentActiveSelection)), selectionBefore);
        await secondGroup.click({ button: "right" });
        await context.locator('[data-molsysviewer-context-submenu="Create"]').click();
        await context.getByRole("menuitem", { name: "Shape from Target in Studio…", exact: true }).click();
        assert.equal(await page.evaluate(() => (window as any).__controller.groupPanel.activeTab), "shapes");
        assert.match(await page.locator('[data-molsysviewer-group-panel-section="shapes"]').textContent(), /Anchored to context target/);
        assert.equal(await page.evaluate(() => JSON.stringify((window as any).__controller.currentActiveSelection)), selectionBefore);
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        const calculationCount = await page.evaluate(() => (window as any).__messages.filter((m: any) => m.action === "create_interaction").length);
        await secondGroup.click({ button: "right" });
        await context.locator('[data-molsysviewer-context-submenu="Interactions"]').click();
        await context.getByRole("menuitem", { name: "Calculate for Target…", exact: true }).click();
        assert.equal(await page.locator('[data-molsysviewer-interaction-calc-scope="true"]').inputValue(), "a");
        assert.equal(await page.locator('[data-molsysviewer-interaction-field="calc-structures"]').inputValue(), "current");
        assert.equal(await page.evaluate(() => (window as any).__messages.filter((m: any) => m.action === "create_interaction").length), calculationCount);
        assert.equal(await page.evaluate(() => JSON.stringify((window as any).__controller.currentActiveSelection)), selectionBefore);
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        for (const label of ["Add to selection · group", "Remove from selection · group", "Replace selection · group"]) {
            await secondGroup.click({ button: "right" });
            await context.locator('[data-molsysviewer-context-submenu="Select"]').click();
            assert.deepEqual(await context.locator('[data-molsysviewer-context-selection-scope="group"]').allTextContents(),
                ["Replace selection", "Add to selection", "Remove from selection"]);
            assert.equal((await context.innerText()).includes("Residue"), false);
            await context.getByRole("menuitem", { name: label, exact: true }).click();
            contextualRequests.push(await latestRequest());
        }
        // Replay the actual browser requests through the real Python owner.
        const backend = spawnSync(process.env.PYTHON || "python", ["-c", `
import json, sys
import molsysviewer as msv
from molsysviewer.interactions import _to_plain
from molsysviewer.viewer.panel_actions import dispatch_panel_action
payload = json.load(sys.stdin)
view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
view.active_selection.set(payload["selection"])
view._ready = True
sent = []
view.widget.send = sent.append
states = []
for request in payload["requests"]:
    sent.clear()
    dispatch_panel_action(view, request)
    states.append({"selection": view.active_selection.atom_indices, "messages": list(sent)})
print(json.dumps(_to_plain({"states": states, "region": list(view.regions.get("context-residue").atom_indices), "annotation": view.annotations.info()[-1]})))
view.close()
`], { cwd: resolve(dir, "../../../.."), encoding: "utf8", input: JSON.stringify({ selection: JSON.parse(selectionBefore).atom_indices, requests: contextualRequests }) });
        assert.equal(backend.status, 0, backend.stderr || String(backend.error));
        const result = JSON.parse(backend.stdout);
        const working = JSON.parse(selectionBefore).atom_indices;
        const pointed = contextualRequests[0].context.atom_indices;
        assert.deepEqual(result.region, pointed);
        assert.deepEqual(result.annotation.atom_indices, pointed);
        assert.deepEqual(result.states[0].selection, working);
        assert.deepEqual(result.states[1].selection, working);
        assert.deepEqual(new Set(result.states[2].selection), new Set([...working, ...pointed]));
        assert.deepEqual(result.states[3].selection, working.filter((atom: number) => !pointed.includes(atom)));
        assert.deepEqual(result.states[4].selection, pointed);
        await page.evaluate(async batches => {
            for (const state of batches) for (const message of state.messages) await (window as any).__controller.handleMessage(message, { throwOnError: true });
        }, result.states);
        assert.deepEqual(await page.evaluate(() => (window as any).__controller.currentActiveSelection.atom_indices), pointed);
        // Related regions offer quick navigation and visibility; their editor
        // stays in Studio. Opening it must preserve the working selection.
        await secondGroup.click({ button: "right" });
        await context.locator('[data-molsysviewer-context-submenu="Related regions"]').click();
        assert.equal(await context.getByRole("menuitem", { name: "Focus region context-residue", exact: true }).count(), 1);
        assert.equal(await context.getByRole("menuitem", { name: "Hide region", exact: true }).count(), 1);
        assert.equal(await context.getByRole("menuitem", { name: "Rename region", exact: true }).count(), 0);
        assert.equal(await context.getByRole("menuitem", { name: "Delete region", exact: true }).count(), 0);
        await context.getByRole("menuitem", { name: "Open region context-residue in Studio", exact: true }).click();
        assert.equal(await page.evaluate(() => (window as any).__controller.groupPanel.activeTab), "regions");
        assert.equal(await page.locator('[data-molsysviewer-region-rename="context-residue"]').count(), 1);
        assert.deepEqual(await page.evaluate(() => (window as any).__controller.currentActiveSelection.atom_indices), pointed);
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        // The two peptide links crossing the contextual residue must retain
        // their region-owned halves; atom spheres must stay inside the region.
        const assertBoundaryLinks = async () => {
            const geometry = await page.evaluate(() => (window as any).Harness.inspectRegionBoundaryGeometry((window as any).__controller, "context-residue"));
            assert.ok(geometry.length > 0);
            for (const representation of geometry) {
                assert.equal(representation.boundaryHalves, 2);
                assert.equal(representation.drawnBoundaryHalves, 2);
                assert.equal(representation.foreignSpheres, 0);
            }
        };
        await assertBoundaryLinks();
        for (const frame of [1, 2, 0]) {
            await page.evaluate(async index => (window as any).__controller.handleMessage({ op: "set_trajectory_frame", index }), frame);
            await assertBoundaryLinks();
        }
        for (const representation of ["line", "ball-and-stick", "inherit"]) {
            await page.evaluate(async representation => (window as any).__controller.handleMessage({ op: "set_region_representation", tag: "context-residue", representation }), representation);
            await assertBoundaryLinks();
        }

        // View controls exist on molecular targets; root size is independent of
        // the saved collection, and the collection route selects its Studio tab.
        await page.evaluate(() => {
            const c = (window as any).__controller;
            c.savedSelections = Array.from({ length: 1000 }, (_, i) => ({ tag: `saved-${i}`, atom_count: 1, atom_indices: [0] }));
        });
        await firstGroup.click({ button: "right" });
        assert.equal(await context.locator('[data-molsysviewer-context-submenu="View"]').count(), 1);
        assert.equal(await context.locator('[data-molsysviewer-saved-selection]').count(), 0);
        assert.ok(await context.locator('[role="menu"]:visible button:visible').count() <= 16);
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
        await context.getByRole("menuitem", { name: "Undo", exact: true }).focus();
        assert.match(await context.locator('[data-molsysviewer-menu-disabled-reason]:visible').innerText(), /No scene history/);
        await page.keyboard.press("Enter");
        await page.keyboard.press("Space");
        assert.equal(await context.isVisible(), true);
        assert.equal(await page.evaluate(() => (window as any).__messages.filter((m: any) => m.event === "scene_history_undo").length), 0);
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

        // A popped-out Studio has hierarchy but no local trajectory. Its
        // topology request must not declare a fictitious frame zero.
        await page.evaluate(async () => {
            const w = window as any, viewer = w.__controller;
            const host = document.createElement("div"); host.id = "panel-only";
            Object.assign(host.style, { position: "relative", width: "700px", height: "520px" });
            document.body.appendChild(host);
            const panel = await w.Harness.createController("panel-only", { isPanelOnly: true, panelModeStyle: "split" });
            panel.setHierarchyItems(JSON.parse(JSON.stringify(viewer.getHierarchyItems())));
            w.__controller = viewer;
            w.__panel = panel;
        });
        const panel = page.locator("#panel-only");
        await panel.locator('[data-molsysviewer-group-item="true"]').first().click({ button: "right" });
        const panelMenu = panel.locator('[data-molsysviewer-context-menu="true"]');
        await panelMenu.locator('[data-molsysviewer-context-submenu="Select"]').click();
        await panelMenu.getByRole("menuitem", { name: "Replace selection · group", exact: true }).click();
        const panelRequest = await latestRequest();
        assert.equal(panelRequest.action, "select_context_target");
        assert.equal(panelRequest.structure_index, undefined);
        assert.ok(panelRequest.context.atom_indices.length > 0);

        // Real rendered objects and a parallel occurrence beyond the first
        // inspector page; skipped geometry makes link index != query offset.
        const objects = objectBridge();
        await page.evaluate(async wire => {
            const w = window as any;
            const host = document.createElement("div"); host.id = "objects";
            Object.assign(host.style, { position: "relative", width: "700px", height: "520px" });
            document.body.appendChild(host);
            const c = await w.Harness.createController("objects");
            w.Harness.attachContextHelp(c, host);
            for (const message of wire) await c.handleMessage(message, { throwOnError: true });
        }, objects.initial);
        const objectMenu = page.locator('#objects [data-molsysviewer-context-menu="true"]');
        const picked = await page.evaluate(() => (window as any).Harness.openInteractionContext((window as any).__controller, "parallel-set", 60));
        assert.equal(picked.context.entity_ref.query_offset, 61);
        assert.equal(picked.context.entity_ref.occurrence_index, 61);
        assert.match(await objectMenu.locator('[data-molsysviewer-context-menu-title]').innerText(), /hbond.*parallel-set.*structure 0/);
        await objectMenu.getByRole("menuitem", { name: "Inspect This Interaction…", exact: true }).click();
        const inspectEvent = await page.evaluate(() => [...(window as any).__messages].reverse().find((m: any) => m.action === "inspect_interaction_occurrence"));
        assert.ok(inspectEvent);
        assert.equal(await page.evaluate(() => (window as any).__messages.filter((m: any) => m.action === "inspect_interaction_occurrence").length), 1);
        let replay = objectBridge([inspectEvent]);
        assert.deepEqual(replay.selection, [9], "inspection must preserve the working selection");
        await page.evaluate(async wire => { for (const message of wire) await (window as any).__controller.handleMessage(message, { throwOnError: true }); }, replay.messages);
        assert.equal(await page.locator('#objects [data-molsysviewer-interaction-observation="61"]').count(), 1);
        assert.equal(await page.locator('#objects [data-molsysviewer-interaction-observation]').count(), 1);
        assert.match(await page.locator('#objects [data-molsysviewer-interaction-observation="61"]').innerText(), /distance: 0\.26 nm/);

        const requests: any[] = [inspectEvent];
        for (const [label, action] of [["Select Participants", "select_picked_interaction"], ["Focus Participants", "focus_picked_interaction"]]) {
            await page.evaluate(() => (window as any).Harness.openInteractionContext((window as any).__controller, "parallel-set", 60));
            await objectMenu.getByRole("menuitem", { name: label, exact: true }).click();
            const event = await page.evaluate(action => [...(window as any).__messages].reverse().find((m: any) => m.action === action), action);
            assert.ok(event); requests.push(event);
        }
        replay = objectBridge(requests);
        assert.deepEqual(replay.selection, [0, 1, 2]);
        await page.evaluate(async wire => { for (const message of wire) await (window as any).__controller.handleMessage(message, { throwOnError: true }); }, replay.messages);
        await page.evaluate(() => (window as any).Harness.openInteractionContext((window as any).__controller, "parallel-set", 60));
        await objectMenu.locator('[data-molsysviewer-context-submenu="Interaction set"]').click();
        await objectMenu.getByRole("menuitem", { name: "Edit Interaction Set in Studio…", exact: true }).click();
        assert.equal(await page.locator('#objects [data-molsysviewer-interaction-field="tag"]').inputValue(), "parallel-set");
        await page.evaluate(() => (window as any).Harness.openInteractionContext((window as any).__controller, "parallel-set", 60));
        await objectMenu.locator('[data-molsysviewer-context-submenu="Interaction set"]').click();
        await objectMenu.getByRole("menuitem", { name: "Hide Interaction Representation", exact: true }).click();
        const hide = await page.evaluate(() => [...(window as any).__messages].reverse().find((m: any) => m.action === "toggle_interaction_visibility"));
        assert.equal(hide.hidden, true);
        requests.push(hide); replay = objectBridge(requests);
        assert.deepEqual(replay.analyses.map((analysis: any) => analysis.name), ["parallel"]);
        assert.equal(replay.sets[0].hidden, true);
        await page.evaluate(async wire => { for (const message of wire) await (window as any).__controller.handleMessage(message, { throwOnError: true }); }, replay.messages);
        await page.evaluate(() => (window as any).Harness.openInteractionContext((window as any).__controller, "parallel-set", 60));
        const summary = replay.messages.findLast((message: any) => message.op === "set_interaction_summaries");
        assert.ok(summary);
        await page.evaluate(async summary => {
            const c = (window as any).__controller;
            await c.handleMessage(summary);
        }, summary);
        assert.equal(await objectMenu.isVisible(), false, "updated analyses/filters invalidate an open occurrence menu");

        await page.evaluate(() => (window as any).Harness.openSceneObjectContext((window as any).__controller, "annotation", "menu-note"));
        await objectMenu.getByRole("menuitem", { name: "Edit Annotation Text…", exact: true }).click();
        assert.equal(await page.locator('#objects [data-molsysviewer-annotation-text-input="menu-note"]').inputValue(), "Menu annotation");
        await page.evaluate(() => (window as any).Harness.openSceneObjectContext((window as any).__controller, "shape", "menu-sphere"));
        assert.equal(await objectMenu.getByRole("menuitem", { name: "Select Associated Atoms", exact: true }).isDisabled(), true);
        assert.equal(await objectMenu.getByRole("menuitem", { name: "Focus Target", exact: true }).isEnabled(), true);
        await objectMenu.getByRole("menuitem", { name: "Focus Target", exact: true }).click();
        await page.waitForFunction(() => (window as any).__controller.plugin.canvas3d.camera.state.target.every((v: number) => Math.abs(v - 30) < 0.01));
        // Actual screen input: a direct loci injection would miss the alpha
        // threshold regression reported during the human review.
        await page.evaluate(() => (window as any).__controller.groupPanel.setExpanded(false));
        await page.locator("#objects canvas").scrollIntoViewIfNeeded();
        await page.waitForFunction(() => {
            const w = window as any;
            if (w.__controller.plugin.canvas3d.camera.transition.inTransition) return false;
            const { target } = w.Harness.pickScenePosition(w.__controller, [30, 30, 30]);
            return target.kind === "shape" && target.tag === "menu-sphere";
        });
        const spherePoint = await page.evaluate(() => (window as any).Harness.projectScenePosition((window as any).__controller, [30, 30, 30]));
        await page.mouse.move(spherePoint.x, spherePoint.y, { steps: 3 });
        await page.waitForFunction(() => {
            const hover = (window as any).__controller.lastHoverPayload;
            return hover?.kind === "shape" && hover.tag === "menu-sphere";
        });
        await page.mouse.click(spherePoint.x, spherePoint.y);
        await page.waitForFunction(() => (window as any).__controller.currentActiveSelection.items.some((item: any) => item.source_kind === "shape" && item.tag === "menu-sphere"));
        await page.waitForFunction(() => {
            const c = (window as any).__controller;
            const ref = (window as any).Harness.inspectTaggedRefs(c, "shape", "menu-sphere")[0].ref;
            return c.plugin.state.data.cells.get(ref).obj.data.repr.renderObjects.some((ro: any) => ro.values.tMarker.ref.value.array.some((value: number) => (value & 2) !== 0));
        }); // Mol* applies queued selection marks on its next render tick.
        await page.mouse.click(spherePoint.x, spherePoint.y, { button: "right" });
        assert.equal(await objectMenu.locator('[data-molsysviewer-context-menu-title]').innerText(), "menu-sphere");
        assert.equal(await objectMenu.getByRole("menuitem", { name: "Edit Appearance in Studio…", exact: true }).isVisible(), true);
        await page.keyboard.press("Escape");
        await page.evaluate(() => (window as any).Harness.openSceneObjectContext((window as any).__controller, "shape", "menu-sphere"));
        await objectMenu.getByRole("menuitem", { name: "Edit Appearance in Studio…", exact: true }).click();
        assert.equal(await page.locator('#objects [data-molsysviewer-shape-style="menu-sphere"]').count(), 1);
        await page.locator('#objects [data-molsysviewer-shape-rename="menu-sphere"]').fill("renamed-sphere");
        await page.locator('#objects [data-molsysviewer-shape-rename-confirm="menu-sphere"]').click();
        const rename = await page.evaluate(() => [...(window as any).__messages].reverse().find((m: any) => m.action === "rename_shape"));
        requests.push(rename); replay = objectBridge(requests);
        await page.evaluate(async wire => { for (const message of wire) await (window as any).__controller.handleMessage(message, { throwOnError: true }); }, replay.messages);
        const renamed = await page.evaluate(() => (window as any).Harness.openSceneObjectContext((window as any).__controller, "shape", "renamed-sphere"));
        assert.equal(renamed.tag, "renamed-sphere");
        assert.equal(renamed.kind, "shape", "same-tag measurements must not change a shape's domain");
        assert.equal(await objectMenu.locator('[data-molsysviewer-context-menu-title]').innerText(), "renamed-sphere");
        await objectMenu.getByRole("menuitem", { name: "Edit Appearance in Studio…", exact: true }).click();
        assert.equal(await page.locator('#objects [data-molsysviewer-shape-style="renamed-sphere"]').count(), 1);
        await page.evaluate(() => (window as any).Harness.openSceneObjectContext((window as any).__controller, "measurement", "menu-distance"));
        assert.equal(await objectMenu.locator('[data-molsysviewer-context-menu-title]').innerText(), "menu-distance");
        await objectMenu.getByRole("menuitem", { name: "Inspect and Edit Measurement…", exact: true }).click();
        assert.equal(await page.locator('#objects [data-molsysviewer-measurement-rename-input="menu-distance"]').count(), 1);

        // Common scene actions call their existing local owner exactly once.
        await page.evaluate(() => {
            const c = (window as any).__controller;
            c.contextMenu.open({ event: "interaction_context_menu", kind: "empty" }, 80, 80, null, null, [], [], [], [], { canFocusAll: true, canHelp: true });
        });
        await objectMenu.getByRole("menuitem", { name: "Focus All", exact: true }).click();
        await page.waitForFunction(() => (window as any).__controller.plugin.canvas3d.camera.state.target.some((v: number) => Math.abs(v - 30) > 0.1));
        assert.equal(await page.evaluate(() => (window as any).__messages.some((m: any) => m.action === "focus_all")), false);
        await page.evaluate(() => {
            const c = (window as any).__controller;
            c.contextMenu.open({ event: "interaction_context_menu", kind: "empty" }, 80, 80, null, null, [], [], [], [], { canFocusAll: true, canHelp: true });
        });
        await objectMenu.getByRole("menuitem", { name: "Help", exact: true }).click();
        assert.equal(await page.locator('#objects .molsysviewer-help-card').isVisible(), true);

        // An actual secondary browser window uses its own canvas bounds.
        const popupReady = page.waitForEvent("popup");
        await page.evaluate(() => window.open("about:blank", "menu-layout-review", "width=720,height=560"));
        const popup = await popupReady;
        popup.on("pageerror", error => errors.push(String(error)));
        await popup.setViewportSize({ width: 720, height: 560 });
        await popup.setContent('<style>body{margin:0}</style><div id="popup-root" style="position:relative;width:100vw;height:100vh"></div>');
        await popup.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        await popup.evaluate(async wire => {
            const w = window as any;
            const c = await w.Harness.createController("popup-root");
            w.__controller = c;
            for (const message of wire) await c.handleMessage(message, { throwOnError: true });
            c.contextMenu.open({ event: "interaction_context_menu", kind: "empty" }, 715, 555);
        }, messages);
        await popup.waitForFunction(() => (window as any).__controller.plugin.canvas3d?.reprCount.value > 0);
        const popupMenu = popup.locator('[data-molsysviewer-context-menu="true"]');
        await popupMenu.locator('[data-molsysviewer-context-submenu="View"]').click();
        assert.equal(await popupMenu.locator('[data-molsysviewer-menu-page]:visible').count(), 2);
        await popup.setViewportSize({ width: 420, height: 360 });
        await popup.waitForFunction(() => document.querySelector('[data-molsysviewer-context-scroll]')?.getAttribute("data-molsysviewer-menu-layout") === "inline");
        assert.equal(await popupMenu.locator('[data-molsysviewer-menu-page]:visible').count(), 1);
        const popupBounds = await popupMenu.boundingBox();
        assert.ok(popupBounds && popupBounds.x >= 0 && popupBounds.y >= 0);
        assert.ok(popupBounds.x + popupBounds.width <= 420 && popupBounds.y + popupBounds.height <= 360);
        await popupMenu.getByRole("menuitem", { name: "‹ Back", exact: true }).click();
        await popup.keyboard.press("Escape");
        assert.equal(await popupMenu.isVisible(), false);
        await popup.close();

        assert.deepEqual(errors, []);
        console.log("[E2E context menu] adaptive adjacent cards, edge flipping, narrow/form preservation, disabled keyboard reasons and actual popup; molecular/object rendering, occurrence scope, editors, keys/Escape and single dispatch pass");
    } finally { await browser.close(); }
}

run().catch(error => { console.error(error); process.exit(1); });
