import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "./e2e-browser";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import type { Download } from "playwright";

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

        const tips = section("interactions").locator('[data-molsysviewer-workflow-help="interactions"]');
        assert.equal(await tips.evaluate((el: HTMLDetailsElement) => el.open), false);
        await tips.locator(":scope > summary").click();
        await apply(fixture.initial_messages.filter((message: any) => message.op === "set_interaction_summaries"));
        assert.ok(await tips.evaluate((el: HTMLDetailsElement) => el.open));
        const layerTag = fixture.initial_messages.find((message: any) => message.op === "set_interaction_summaries").interactions[0].layer_tag;
        const toggleLayer = { action: "set_layer_visibility", tag: layerTag, hidden: true };
        const layerHidden = await bridge.request([toggleLayer]);
        await apply(layerHidden.message_batches[0]);
        assert.match(await section("interactions").innerText(), /0\/1 sets visible/);
        assert.match(await page.locator('[data-molsysviewer-interaction-set="hbonds"]').innerText(), /Hidden by layer/);
        await apply((await bridge.request([toggleLayer, { ...toggleLayer, hidden: false }])).message_batches[1]);
        assert.match(await section("interactions").innerText(), /1\/1 sets visible/);

        // A coordinate annotation has no atom indices: Focus still uses its live owner.
        await open("annotations");
        const absoluteFocus = page.locator('[data-molsysviewer-annotation-focus="absolute-note"]');
        assert.ok(await absoluteFocus.isEnabled()); await absoluteFocus.click();
        const focusAction = await page.evaluate(() => [...(window as any).__messages].reverse().find((msg: any) => msg.action === "focus_annotation"));
        assert.equal(focusAction.tag, "absolute-note");
        await apply((await bridge.request([focusAction])).message_batches[0]);
        await page.waitForFunction(() => {
            const target = (window as any).__controller.plugin.canvas3d.camera.state.target;
            return [10, 20, 30].every((value, index) => Math.abs(target[index] - value) < 0.01);
        });

        await open("export");
        const work = page.locator('[data-molsysviewer-work-files]');
        const filePath = work.getByLabel("Path in Python session", { exact: true });
        const fileKind = work.getByLabel("Work file format", { exact: true });
        const fileStatus = work.locator('[data-molsysviewer-work-file-status]');
        const fileEvents: any[] = [];
        const fileReply = async (action: string) => {
            const event = await page.evaluate(action => [...(window as any).__messages].reverse().find((msg: any) => msg.action === action), action);
            fileEvents.push(event);
            assert.ok(await filePath.isDisabled());
            // A reply for another request must not unlock these controls.
            await apply([{ op: "studio_action_result", action, request_id: "unrelated", domain: "export", ok: true }]);
            assert.ok(await filePath.isDisabled());
            const response = await bridge.request(fileEvents, "workfiles");
            await apply(response.message_batches.at(-1));
            assert.ok(await filePath.isEnabled());
            assert.ok(await work.isVisible(), "Restoration must return to the requesting file controls, not leave them hidden by System loading");
        };
        await filePath.fill(resolve(downloadDir, "missing-directory", "review.json"));
        await work.getByRole("button", { name: "Save file", exact: true }).click();
        await fileReply("save_work_file");
        assert.equal(await fileStatus.getAttribute("role"), "alert");
        assert.ok((await filePath.inputValue()).includes("missing-directory"));
        fileEvents.length = 0;
        const statePath = resolve(downloadDir, "review.json");
        await filePath.fill(statePath);
        await work.getByLabel("Allow overwriting an existing file", { exact: true }).check();
        await work.getByRole("button", { name: "Save file", exact: true }).click();
        await fileReply("save_work_file");
        assert.match(await fileStatus.innerText(), /Saved scene state/);
        assert.ok(JSON.parse(await readFile(statePath, "utf8")).annotations.length > 0);
        await open("viewport"); await open("export");
        assert.equal(await filePath.inputValue(), statePath);
        await work.getByRole("button", { name: "Restore file…", exact: true }).click();
        await work.getByRole("button", { name: "Cancel", exact: true }).click();
        assert.equal(await work.getByRole("button", { name: "Confirm restore", exact: true }).count(), 0);
        await work.getByRole("button", { name: "Restore file…", exact: true }).click();
        await work.getByRole("button", { name: "Confirm restore", exact: true }).click();
        await fileReply("restore_work_file");
        assert.match(await fileStatus.innerText(), /Restored scene state/);
        const sessionPath = resolve(downloadDir, "review.msv");
        await fileKind.selectOption("session"); await filePath.fill(sessionPath);
        await work.getByRole("button", { name: "Save file", exact: true }).click();
        await fileReply("save_work_file");
        assert.match(await fileStatus.innerText(), /Saved experimental session/);
        assert.equal((await readFile(sessionPath)).subarray(0, 2).toString(), "PK");
        await work.getByRole("button", { name: "Restore file…", exact: true }).click();
        await work.getByRole("button", { name: "Confirm restore", exact: true }).click();
        await fileReply("restore_work_file");
        assert.match(await fileStatus.innerText(), /Restored experimental session/);
        assert.equal(await filePath.inputValue(), sessionPath);
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
        assert.ok(figureAction, JSON.stringify(await page.evaluate(() => ({
            active: document.activeElement?.outerHTML.slice(0, 500),
            checkbox: document.querySelector('input[aria-label="Transparent Background"]')?.outerHTML,
            events: (window as any).__messages.slice(-4),
        }))));
        assert.ok(figureAction.figure_variants.includes("transparent"));
        const figureReply = await bridge.request([figureAction]); await apply(figureReply.message_batches[0]);
        assert.ok(await page.getByLabel("Transparent Background", { exact: true }).isChecked());
        assert.ok(await page.getByLabel("Transparent Background", { exact: true }).evaluate(element => element === element.ownerDocument.activeElement));
        // Retain bounded input/render evidence for the unresolved hosted timeout.
        await page.evaluate(() => {
            (window as any).__studioPngInput = [];
            (window as any).__studioPngTasks = [];
            (window as any).__controller.plugin.managers.task.events.progress.subscribe((event: any) => {
                const p = event.progress.root.progress;
                if (p.taskName !== "Generate Image") return;
                const tasks = (window as any).__studioPngTasks;
                tasks.push({ message: p.message, elapsedMs: Math.round(performance.now() - p.startedTime), current: p.current, max: p.max });
                if (tasks.length > 8) tasks.shift();
            });
            for (const type of ["pointerdown", "pointerup", "click"]) document.addEventListener(type, event => {
                const target = event.target as HTMLElement | null;
                if (target?.closest('[data-molsysviewer-export-image]')) (window as any).__studioPngInput.push({ type, connected: target.isConnected });
            }, true);
        });
        // Listen before input, but time file delivery only after rendering. The
        // hosted software renderer needs >30s for this unchanged high-quality
        // image; the existing suite deadline still bounds the entire operation.
        const pngDownloads: Download[] = [];
        const capturePng = (download: Download) => pngDownloads.push(download);
        page.on("download", capturePng);
        const png = await (async () => {
            try {
                const pngButton = page.getByRole("button", { name: "Download PNG Image", exact: true });
                await pngButton.scrollIntoViewIfNeeded();
                const box = (await pngButton.boundingBox())!;
                await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2); await page.mouse.down();
                // A real resize must not remove the button between down and click.
                await page.evaluate(() => {
                    const c = (window as any).__controller, gl = c.plugin.canvas3d.webgl.gl;
                    c.groupPanel.setImageDimensions(gl.drawingBufferWidth + 1, gl.drawingBufferHeight);
                    c.groupPanel.setImageDimensions(gl.drawingBufferWidth, gl.drawingBufferHeight);
                });
                await page.mouse.up();
                await page.waitForFunction(() => {
                    const button = document.querySelector<HTMLButtonElement>('[data-molsysviewer-export-image]');
                    return !!button && !button.disabled;
                }, null, { timeout: Number(process.env.E2E_SUITE_TIMEOUT_MS ?? 180_000) });
                assert.equal(await page.locator('[data-molsysviewer-export-image-status]').innerText(), "PNG download started.");
                return pngDownloads[0] ?? await page.waitForEvent("download", { timeout: 30_000 });
            } catch (error) {
                const diagnostic = await page.evaluate(() => ({
                    input: (window as any).__studioPngInput,
                    status: document.querySelector('[data-molsysviewer-export-image-status]')?.textContent,
                    disabled: document.querySelector<HTMLButtonElement>('[data-molsysviewer-export-image]')?.disabled,
                    tasks: (window as any).__studioPngTasks,
                    contextLost: (window as any).__controller.plugin.canvas3d.webgl.gl.isContextLost(),
                    background: (window as any).__controller.plugin.canvas3d.props.postprocessing.background.variant.name,
                    illumination: (window as any).__controller.plugin.canvas3d.props.illumination.enabled,
                    imageCanvas: [(window as any).__controller.plugin.helpers.viewportScreenshot.canvas.width,
                        (window as any).__controller.plugin.helpers.viewportScreenshot.canvas.height],
                    imagePassSize: (window as any).__controller.plugin.helpers.viewportScreenshot._imagePass
                        ? [(window as any).__controller.plugin.helpers.viewportScreenshot._imagePass._width,
                            (window as any).__controller.plugin.helpers.viewportScreenshot._imagePass._height] : null,
                    drawingBuffer: [(window as any).__controller.plugin.canvas3d.webgl.gl.drawingBufferWidth,
                        (window as any).__controller.plugin.canvas3d.webgl.gl.drawingBufferHeight],
                }));
                throw new Error(`PNG download failed: ${JSON.stringify({ ...diagnostic, pageErrors: errors.slice(-4) })}; ${String(error)}`);
            } finally { page.off("download", capturePng); }
        })();
        assert.equal(png.suggestedFilename(), "molsysviewer.png");
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

        // Inspect the actual downloaded standalone file: scene metadata remains
        // truthful, and missing authority must never strand a pending creation.
        const exported = await page.context().newPage();
        exported.on("pageerror", error => errors.push(String(error)));
        await exported.goto(pathToFileURL(htmlPath).href);
        await exported.waitForFunction(() => (window as any).__molsysviewerDocsController?.plugin.canvas3d?.reprCount.value > 0);
        const openExported = (key: string) => exported.evaluate(key => {
            const c = (window as any).__molsysviewerDocsController;
            c.setPanelMode("navigate", true); c.groupPanel.openSection(key);
        }, key);
        await openExported("export");
        const offlineWork = exported.locator('[data-molsysviewer-work-files]');
        assert.ok(await offlineWork.getByRole("button", { name: "Save file", exact: true }).isDisabled());
        assert.ok(await offlineWork.getByRole("button", { name: "Restore file…", exact: true }).isDisabled());
        assert.match(await offlineWork.innerText(), /requires a live Python session/);
        await openExported("annotations");
        assert.ok(await exported.locator('[data-molsysviewer-annotation-focus="absolute-note"]').isDisabled());
        const exportedAnnotations = exported.locator('[data-molsysviewer-group-panel-section="annotations"]');
        assert.ok(!(await exportedAnnotations.innerText()).includes("Load a structure first."));
        await openExported("shapes");
        const exportedShapes = exported.locator('[data-molsysviewer-group-panel-section="shapes"]');
        const shapeCreation = exportedShapes.locator('details[data-molsysviewer-disclosure="creation"]');
        if (!await shapeCreation.evaluate((element: HTMLDetailsElement) => element.open)) await shapeCreation.locator(":scope > summary").click();
        await exportedShapes.getByText("Coordinates", { exact: true }).click();
        await exportedShapes.getByLabel("Shape tag", { exact: true }).fill("offline-draft");
        await exportedShapes.getByRole("button", { name: "Create Shape", exact: true }).click();
        assert.match(await exportedShapes.innerText(), /needs a running MolSysViewer session/);
        assert.equal(await exportedShapes.getByRole("button", { name: "Creating…", exact: true }).count(), 0);
        assert.equal(await exportedShapes.getByLabel("Shape tag", { exact: true }).inputValue(), "offline-draft");
        await openExported("interactions");
        assert.ok(await exported.locator('[data-molsysviewer-interaction-create]').isDisabled());
        await exported.close();

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
