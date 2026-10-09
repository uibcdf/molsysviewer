import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";
import { PythonFixtureBridge } from "./python-fixture-bridge";

const dir = dirname(fileURLToPath(import.meta.url));

async function run() {
    const bridge = new PythonFixtureBridge(resolve(dir, "studio-usability-bridge.py"), resolve(dir, "../../../.."));
    const browser = await chromium.launch();
    const downloadDir = await mkdtemp(resolve(tmpdir(), "msv-studio-downloads-"));
    try {
        const fixture = await bridge.request();
        const page = await browser.newPage({ viewport: { width: 1200, height: 900 }, acceptDownloads: true });
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        await page.setContent('<div id="root" style="position:relative;width:1050px;height:760px"></div>');
        await page.addScriptTag({ path: resolve(dir, "harness.bundle.js") });
        const apply = (messages: unknown[]) => page.evaluate(async messages => {
            for (const msg of messages) await (window as any).__controller.handleMessage(msg, { throwOnError: true });
        }, messages);
        await page.evaluate(async () => {
            await (window as any).Harness.createController("root", { panelModeStyle: "floating-unified" });
        });
        await apply(fixture.initial_messages);
        await page.waitForFunction(() => (window as any).__controller.plugin.canvas3d?.reprCount.value > 0);
        await page.evaluate(() => (window as any).__controller.setPanelMode("navigate", true));
        assert.match((await page.locator('[data-molsysviewer-group-panel-tab="export"]').getAttribute("title"))!, /PNG.*HTML/);
        assert.match((await page.locator('[data-molsysviewer-group-panel-tab="layers"]').getAttribute("title"))!, /visibility/);
        assert.match((await page.locator('[data-molsysviewer-group-settings-btn]').getAttribute("title"))!, /controls hide automatically/);
        const section = (key: string) => page.locator(`[data-molsysviewer-group-panel-section="${key}"]`);
        const open = (key: string) => page.evaluate(key => (window as any).__controller.groupPanel.openSection(key), key);
        const dragHandle = () => page.evaluate(() => {
            const header = (window as any).__controller.sharedShell.headerElement as HTMLElement;
            const rect = header.getBoundingClientRect(), y = rect.y + rect.height / 2;
            for (let x = rect.x + 4; x < rect.right; x += 4) {
                const hit = document.elementFromPoint(x, y);
                if (hit && header.contains(hit) && !hit.closest("button, input, select")) return { x, y };
            }
            throw new Error("Floating panel header has no drag area");
        });

        await open("interactions");
        const form = page.locator('[data-molsysviewer-interaction-form="true"]');
        assert.equal(await form.evaluate((element: HTMLDetailsElement) => element.open), false);
        assert.ok(await page.locator('[data-molsysviewer-interactions-experimental="true"]').isVisible());
        assert.ok(await page.locator('[data-molsysviewer-interaction-set="hbonds"]').isVisible());
        await form.locator(":scope > summary").focus(); await page.keyboard.press("Enter");
        assert.ok(await form.evaluate((element: HTMLDetailsElement) => element.open));
        await page.getByLabel("Calculate atoms", { exact: true }).selectOption("a");
        assert.ok(await page.locator('[data-molsysviewer-interaction-filters="true"]').evaluate((element: HTMLDetailsElement) => element.open));
        await page.getByLabel("Calculate atoms", { exact: true }).focus();
        await apply(fixture.initial_messages.filter((message: any) => message.op === "set_interaction_summaries"));
        assert.ok(await page.getByLabel("Calculate atoms", { exact: true }).evaluate(element => element === element.ownerDocument.activeElement));
        assert.match(await page.locator('[data-molsysviewer-interaction-calculation-coverage]').innerText(), /Only the current structure/);
        await page.locator('[data-molsysviewer-interaction-field="calc-structures"]').fill("all");
        assert.match(await page.locator('[data-molsysviewer-interaction-calculation-coverage]').innerText(), /All loaded structures/);
        await form.locator(":scope > summary").click();

        await open("export");
        assert.equal(await page.getByLabel("Resolution Scale", { exact: true }).inputValue(), "1.5");
        assert.equal(await page.getByLabel("Transparent Background", { exact: true }).isChecked(), false);
        const dimensions = await page.evaluate(() => {
            const gl = (window as any).__controller.plugin.canvas3d.webgl.gl;
            return [Math.round(gl.drawingBufferWidth * 1.5), Math.round(gl.drawingBufferHeight * 1.5)];
        });
        assert.ok((await page.locator('[data-molsysviewer-export-dimensions]').innerText()).includes(`${dimensions[0]} × ${dimensions[1]} px`));
        // Native checkbox keyboard activation must survive the real Python reply.
        await page.getByLabel("Transparent Background", { exact: true }).focus();
        await page.keyboard.press("Space");
        const figureAction = await page.evaluate(() => [...(window as any).__messages].reverse().find((msg: any) => msg.action === "set_figure_spec"));
        assert.ok(figureAction.figure_variants.includes("transparent"));
        const figureReply = await bridge.request([figureAction]); await apply(figureReply.message_batches[0]);
        assert.ok(await page.getByLabel("Transparent Background", { exact: true }).isChecked());
        assert.ok(await page.getByLabel("Transparent Background", { exact: true }).evaluate(element => element === element.ownerDocument.activeElement));
        const pngReady = page.waitForEvent("download");
        await page.getByRole("button", { name: "Download PNG Image", exact: true }).click();
        const png = await pngReady; assert.equal(png.suggestedFilename(), "molsysviewer.png");
        const pngPath = resolve(downloadDir, "figure.png"); await png.saveAs(pngPath);
        const bytes = await readFile(pngPath);
        assert.deepEqual([bytes.readUInt32BE(16), bytes.readUInt32BE(20)], dimensions);
        const alpha = await page.evaluate(async data => {
            const image = new Image(); image.src = `data:image/png;base64,${data}`; await image.decode();
            const canvas = document.createElement("canvas"); canvas.width = canvas.height = 1;
            const ctx = canvas.getContext("2d")!; ctx.drawImage(image, 0, 0);
            return ctx.getImageData(0, 0, 1, 1).data[3];
        }, bytes.toString("base64"));
        assert.equal(alpha, 0, "Transparent Background must reach the actual PNG pixels");

        let downloads = 0; page.on("download", () => downloads++);
        await page.getByRole("button", { name: "Download HTML View", exact: true }).click();
        const htmlAction = await page.evaluate(() => [...(window as any).__messages].reverse().find((msg: any) => msg.action === "export_html"));
        assert.ok(htmlAction.request_id);
        const htmlReply = (await bridge.request([htmlAction])).message_batches[0];
        const htmlReady = page.waitForEvent("download"); await apply(htmlReply);
        const html = await htmlReady; assert.equal(html.suggestedFilename(), "molsysviewer.html");
        const htmlPath = resolve(downloadDir, "view.html"); await html.saveAs(htmlPath);
        const text = await readFile(htmlPath, "utf8");
        assert.match(text, /id="molsysviewer-messages"/);
        assert.match(text, /id="molsysviewer-runtime-source"/);
        await apply(htmlReply); // Shared/replayed reply must not download twice.
        assert.equal(downloads, 1);

        // A dragged and resized floating card retains its bounds through layout toggles.
        const header = await dragHandle();
        await page.mouse.move(header.x, header.y); await page.mouse.down();
        await page.mouse.move(header.x + 50, header.y + 30); await page.mouse.up();
        const bounds = () => page.evaluate(() => {
            const panel = (window as any).__controller.sharedShell.panel;
            return { left: panel.style.left, top: panel.style.top, width: panel.style.width, height: panel.style.height };
        });
        const floating = await bounds();
        await page.getByTitle("Unlock background (Ambient)", { exact: true }).click(); assert.deepEqual(await bounds(), floating);
        await page.getByTitle("Lock background", { exact: true }).click(); assert.deepEqual(await bounds(), floating);
        await page.getByTitle("Minimize", { exact: true }).click();
        await page.getByTitle("Restore", { exact: true }).click(); assert.deepEqual(await bounds(), floating);
        await page.getByTitle("Dock panel (Split)", { exact: true }).click();
        await page.getByTitle("Float panel", { exact: true }).click(); assert.deepEqual(await bounds(), floating);

        await page.evaluate(() => document.getElementById("root")!.style.width = "480px");
        await page.waitForFunction(() => document.querySelector<HTMLElement>('[data-molsysviewer-group-panel-left]')!.style.display === "none");
        const navigation = page.getByLabel("Studio section", { exact: true }); assert.ok(await navigation.isVisible());
        await navigation.selectOption("settings"); assert.ok(await section("settings").isVisible());
        assert.ok(await page.getByRole("switch", { name: "Autohide Controls", exact: true }).isVisible());
        await open("export");
        assert.ok(await navigation.evaluate(element => element === element.ownerDocument.activeElement));
        await navigation.selectOption("shapes"); assert.ok(await section("shapes").isVisible());
        assert.ok(await page.getByLabel("Shape type", { exact: true }).isVisible());
        assert.ok(await page.locator('[data-molsysviewer-group-panel-right]').evaluate(element => element.clientWidth > 300));
        await page.screenshot({ path: "/tmp/msv-studio-review-compact.png" });
        await page.evaluate(() => (window as any).__controller.setPanelMode("addons", true));
        await page.waitForFunction(() => document.querySelector<HTMLElement>('[data-molsysviewer-addons-panel-left]')!.style.display === "none");
        assert.ok(await page.getByLabel("Addon workspace", { exact: true }).isVisible());
        assert.equal(await page.locator('[data-molsysviewer-addon-card="molsysmt"]').count(), 0);
        assert.equal(await page.locator('[data-molsysviewer-addon-workspace-tab="molsysmt"]').count(), 0);
        assert.ok((await page.locator('[data-molsysviewer-addons-panel-right]').innerText()).includes("Add-ons manager"));
        await page.evaluate(() => (window as any).__controller.setPanelMode("navigate", true));
        assert.equal(await navigation.inputValue(), "shapes");
        await page.evaluate(() => document.getElementById("root")!.style.width = "1050px");
        // Host growth preserves the clamped card size until the user resizes it.
        const shellWidth = await bounds(); assert.ok(parseFloat(shellWidth.width) <= 460);
        await navigation.selectOption("whole");
        assert.equal(await section("whole").locator('select:not([aria-label]):not([aria-labelledby])').count(), 0);
        await page.screenshot({ path: "/tmp/msv-studio-review-wide.png" });

        // Disposal during a drag must stop both global drag and host resize work.
        const endHeader = await dragHandle();
        await page.mouse.move(endHeader.x, endHeader.y); await page.mouse.down();
        const disposed = await page.evaluate(() => {
            const c = (window as any).__controller; (window as any).__disposedPanel = c.sharedShell.panel;
            c.dispose(); return (window as any).__disposedPanel.getAttribute("style");
        });
        await page.mouse.move(30, 30); await page.mouse.up();
        await page.evaluate(() => new Promise<void>(resolve => {
            const host = document.getElementById("root")!;
            const observer = new ResizeObserver(() => { observer.disconnect(); requestAnimationFrame(() => requestAnimationFrame(() => resolve())); });
            observer.observe(host); host.style.width = "250px";
        }));
        assert.equal(await page.evaluate(() => (window as any).__disposedPanel.getAttribute("style")), disposed);
        assert.deepEqual(errors, []);
        console.log("[E2E Studio] real PNG/HTML downloads, transparency, native labels, compact navigation, floating bounds, disposal and MolSysMT retirement passed");
    } finally {
        try { await browser.close(); } finally {
            try { await bridge.close(); } finally { await rm(downloadDir, { recursive: true, force: true }); }
        }
    }
}

run().catch(error => { console.error(error); process.exit(1); });
