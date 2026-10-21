import assert from "node:assert/strict";
import { resolve } from "node:path";
import type { ConsoleMessage, Page } from "playwright";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { captureCanvasPopupControllers, mountCanvasPopupFixture } from "./canvas-popup-fixture";

/** Real add-on controls, Python shape ownership and actual production popup boot. */
export async function checkShapeOnlyWorkspace(page: Page, dir: string) {
    const bridge = new PythonFixtureBridge(resolve(dir, "shape_only_workspace_fixture.py"), resolve(dir, "../../../.."));
    const errors: string[] = [];
    const onError = (error: Error) => errors.push(String(error));
    const onConsole = (message: ConsoleMessage) => {
        if (message.text().includes("unknown op: set_trajectory_summary")) errors.push(message.text());
    };
    page.on("pageerror", onError);
    page.on("console", onConsole);
    let release: (() => Promise<void>) | undefined;
    let popup: Page | undefined, panel: Page | undefined;
    const welcome = (endpoint: Page) => endpoint.locator('[data-molsysviewer-welcome-card="true"]');
    const drain = async () => {
        await page.evaluate(() => (window as any).__popupFixtureDrain());
        assert.deepEqual(await page.evaluate(() => (window as any).__popupFixtureErrors), []);
    };
    const fixture = async (action: string) => {
        await page.evaluate(action => (window as any).__popupWidgetModel.send({ workspace_fixture: action }), action);
        await drain();
    };
    const hasShape = async (endpoint: Page, tag: string, present: boolean) => endpoint.waitForFunction(({tag, present}) => {
        const c = (window as any).__mirrorController;
        return c.shapeSummaries.some((item: any) => item.tag === tag) === present
            && (c.state.resolveObjectLoci("shape", tag) !== null) === present;
    }, {tag, present});
    const geometryControl = (endpoint: Page, id: string) => endpoint.locator(`[data-workspace-geometry="${id}"]`);
    const visibleShape = async (endpoint: Page, tag: string, position: number[]) => {
        await endpoint.bringToFront();
        await endpoint.waitForFunction(({tag, position}) => {
            const c = (window as any).__mirrorController;
            const canvas = c.plugin.canvas3dContext.canvas;
            const gpu = c.plugin.canvas3d;
            const projected = gpu.camera.project([0, 0, 0, 0], position);
            const rect = canvas.getBoundingClientRect();
            const x = projected[0] * rect.width / canvas.width;
            const y = (canvas.height - projected[1]) * rect.height / canvas.height;
            if (!(x > 0 && x < rect.width && y > 0 && y < rect.height)) return false;
            const hit = gpu.identify([x, y]);
            const loci = hit && gpu.getLoci(hit.id).loci;
            const owner = loci?.shape && c.state.findShapeOwner(loci.shape.sourceData);
            return owner?.kind === "shape" && owner.tag === tag;
        }, {tag, position});
    };
    const panelToggle = (endpoint: Page) => endpoint.locator(".molsysviewer-controls")
        .getByRole("button", {name:/^(Panel|Panel mode \(N \/ W\))$/});
    const openPanels = async (endpoint: Page) => {
        const expanded = await endpoint.evaluate(() => {
            const c = (window as any).__mirrorController;
            return c.groupPanel.isExpanded() || c.addonsPanel.isExpanded();
        });
        if (!expanded) await panelToggle(endpoint).click();
    };
    try {
        release = await mountCanvasPopupFixture(page, bridge, { trajectoryLabel: null });
        // Empty scenes have no camera updates; observe the first actual control.
        await captureCanvasPopupControllers(page, false);
        assert.equal(await welcome(page).count(), 1, "genuinely empty canvas retains quick start");
        const opened = page.waitForEvent("popup");
        await page.getByTitle("Open popup", {exact:true}).click();
        popup = await opened;
        popup.on("pageerror", onError);
        popup.on("console", onConsole);
        await popup.waitForFunction(() => !!(window as any).__mirrorController);
        await popup.locator("#molsysviewer-loading").waitFor({state:"hidden"});
        assert.equal(await welcome(popup).count(), 1, "empty canvas popup retains quick start");
        console.log("[E2E shape-only workspace] empty widget and canvas popup received");

        // Open Studio with its real control, without a molecular prerequisite.
        await panelToggle(page).click();
        assert.equal(await welcome(page).count(), 0, "welcome cannot cover an explicitly opened workspace");
        await page.locator('[data-molsysviewer-group-panel-tab="interactions"]').click();
        assert.equal(await page.locator('[data-molsysviewer-interaction-create="true"]').isDisabled(), true,
            "molecular calculation still requires molecular data");
        await page.getByTitle("Close (Esc)", {exact:true}).click();
        assert.equal(await welcome(page).count(), 1, "closing Studio restores genuinely empty quick start");

        await fixture("caller-shape");
        for (const endpoint of [page, popup]) {
            await hasShape(endpoint, "caller-sphere", true);
            await visibleShape(endpoint, "caller-sphere", [0, 0, 0]);
            assert.equal(await welcome(endpoint).count(), 0, "shape-only scene has no welcome overlay");
            assert.equal(await endpoint.evaluate(() => !!(window as any).__mirrorController.getStructureData()), false);
        }
        await fixture("hide-caller");
        assert.equal(await welcome(page).count(), 0, "hidden owned geometry is still scene content");
        await fixture("delete-caller");
        await hasShape(page, "caller-sphere", false);
        assert.equal(await welcome(page).count(), 1, "deleted geometry cannot survive as stale welcome suppression");
        console.log("[E2E shape-only workspace] native content and molecular prerequisites received");

        // Add-on first: no dummy MolSys and no geometry are needed to reach Render.
        await fixture("enable");
        await openPanels(page);
        const addonsTab = page.locator('[data-molsysviewer-panel-stack-option="addons"]');
        if (await addonsTab.isVisible()) await addonsTab.click();
        await page.locator('[data-molsysviewer-addon-workspace-tab="geometry-review"]').click();
        await geometryControl(page, "render").waitFor({state:"visible"});
        await page.locator('[data-workspace-ready="true"]').waitFor({state:"visible"});
        const stateCount = await page.locator('[data-workspace-ready="true"]').getAttribute("data-workspace-state-count");
        await page.evaluate(async () => {
            await (window as any).__mirrorController.handleMessage({
                op: "addon_panel_message", addon: "another-addon", panel: "geometry",
                content: { type: "state", state: { initial: true } },
            });
        });
        assert.equal(await page.locator('[data-workspace-ready="true"]').getAttribute("data-workspace-state-count"), stateCount,
            "a panel message for another owner cannot reach this widget's listeners");
        await geometryControl(page, "render").click();
        await drain();
        for (const endpoint of [page, popup]) {
            await hasShape(endpoint, "workspace-sphere", true);
            await visibleShape(endpoint, "workspace-sphere", [10, 0, 0]);
        }
        await fixture("caller-shape");
        for (const endpoint of [page, popup]) {
            await visibleShape(endpoint, "workspace-sphere", [10, 0, 0]);
            await visibleShape(endpoint, "caller-sphere", [0, 0, 0]);
        }
        await geometryControl(page, "clear").click();
        await drain();
        for (const endpoint of [page, popup]) {
            await hasShape(endpoint, "workspace-sphere", false);
            await hasShape(endpoint, "caller-sphere", true);
            assert.equal(await welcome(endpoint).count(), 0);
        }

        // Navigation tears down and remounts the actual AnyWidget panel.
        await page.locator('[data-molsysviewer-addon-workspace-tab="core"]').click();
        if (await addonsTab.isVisible()) await addonsTab.click();
        await page.locator('[data-molsysviewer-addon-workspace-tab="geometry-review"]').click();
        await geometryControl(page, "render").waitFor({state:"visible"});
        await geometryControl(page, "render").click(); await drain();
        await hasShape(popup, "workspace-sphere", true);
        console.log("[E2E shape-only workspace] Render/Clear/remount and caller ownership received");

        const panelOpened = page.waitForEvent("popup");
        await page.getByTitle("Popout panel to external window", {exact:true}).click();
        panel = await panelOpened;
        panel.on("pageerror", onError);
        panel.on("console", onConsole);
        await panel.locator("#molsysviewer-loading").waitFor({state:"hidden"});
        assert.equal(await welcome(panel).count(), 0);
        // Navigation is local to each window; reach its workspace through UI.
        if (!await geometryControl(panel, "clear").isVisible()) {
            const panelAddonsTab = panel.locator('[data-molsysviewer-panel-stack-option="addons"]');
            if (await panelAddonsTab.isVisible()) await panelAddonsTab.click();
            await panel.locator('[data-molsysviewer-addon-workspace-tab="geometry-review"]').click();
        }
        await geometryControl(panel, "clear").waitFor({state:"visible"});
        await geometryControl(panel, "clear").click(); await drain();
        await hasShape(popup, "workspace-sphere", false);
        await hasShape(page, "caller-sphere", true);
        await panel.close(); panel = undefined;

        // The canvas peer offers the same workspace controls in both directions.
        if (!await geometryControl(popup, "render").isVisible()) {
            await popup.bringToFront();
            await popup.locator("#molsysviewer-pop").focus();
            await popup.keyboard.press("w");
            await popup.locator('[data-molsysviewer-addon-workspace-tab="geometry-review"]').click();
        }
        await geometryControl(popup, "render").waitFor({state:"visible"});
        await popup.locator('[data-workspace-ready="true"]').waitFor({state:"visible"});
        // Host navigation must not unmount the canvas popup's widget.
        await page.locator('[data-molsysviewer-addon-workspace-tab="core"]').click();
        await drain();
        await geometryControl(popup, "render").click(); await drain();
        await hasShape(page, "workspace-sphere", true);
        await visibleShape(page, "workspace-sphere", [10, 0, 0]);
        await visibleShape(popup, "workspace-sphere", [10, 0, 0]);
        // Adding geometry must not override a deliberately chosen camera.
        const chosen = await page.evaluate(async () => {
            const c = (window as any).__mirrorController;
            const snapshot = c.getCameraSnapshot();
            await c.handleMessage({op: "set_camera_snapshot", snapshot});
            return snapshot;
        });
        await fixture("distant-shape");
        const current = await page.evaluate(() => (window as any).__mirrorController.getCameraSnapshot());
        // Mol* resolves SetSnapshot through requestCameraReset, deriving radiusMax
        // from the scene at that time. A later scene bound may expand; the chosen
        // pose, framing radius and every other camera preference must not change.
        const { radiusMax: chosenBound, ...chosenView } = chosen;
        const { radiusMax: currentBound, ...currentView } = current;
        assert.deepEqual(currentView, chosenView);
        assert.ok(currentBound >= chosenBound, "new geometry must not collapse the camera bound");
        await fixture("load-molecule");
        for (const endpoint of [page, popup]) {
            await endpoint.waitForFunction(() => !!(window as any).__mirrorController.getStructureData());
            await endpoint.waitForFunction(() => (window as any).__mirrorController.trajectory.getTrajectoryState().fps === 17);
            assert.equal(await welcome(endpoint).count(), 0);
        }
        assert.deepEqual(errors, []);
        console.log("[E2E shape-only workspace] PASS: empty, hidden/deleted shapes, addon-first, Render/Clear/remount, ownership, canvas/panel popups, molecular loading");
    } finally {
        await panel?.close(); await popup?.close();
        await page.evaluate(async () => { await (window as any).__popupFixtureDrain?.(); (window as any).__popupWidgetDispose?.(); }).catch(() => undefined);
        await release?.(); await bridge.close(); page.off("pageerror", onError); page.off("console", onConsole);
    }
}
