import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));

const UPLOAD_PDB = `ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
`;

function waitForJson(lines: ReturnType<typeof createInterface>, prefix: string): Promise<any> {
    return new Promise((resolveValue, rejectValue) => {
        const lineHandler = (line: string) => {
            if (!line.startsWith(prefix)) return;
            cleanup();
            resolveValue(JSON.parse(line.slice(prefix.length)));
        };
        const closeHandler = () => {
            cleanup();
            rejectValue(new Error(`Python bridge ended before ${prefix}`));
        };
        const cleanup = () => {
            lines.off("line", lineHandler);
            lines.off("close", closeHandler);
        };
        lines.on("line", lineHandler);
        lines.on("close", closeHandler);
    });
}

function requestBridge(
    bridge: ReturnType<typeof spawn>,
    lines: ReturnType<typeof createInterface>,
    command: string,
    prefix: string,
): Promise<any> {
    const response = waitForJson(lines, prefix);
    bridge.stdin.write(`${command}\n`);
    return response;
}

async function run() {
    const bridge = spawn(
        process.env.PYTHON || "python",
        [resolve(__dirname, "remote-client-rendering-bridge.py")],
        { stdio: ["pipe", "pipe", "inherit"] },
    );
    const lines = createInterface({ input: bridge.stdout });
    let browser: Awaited<ReturnType<typeof chromium.launch>> | null = null;
    try {
        const session = await waitForJson(lines, "MSV_CLIENT_RENDER_SESSION=");
        browser = await chromium.launch();
        const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        page.on("console", message => {
            if (message.type() === "error") errors.push(message.text());
        });
        await page.goto(session.client_url, { waitUntil: "domcontentloaded" });
        await page.waitForFunction(() => {
            const runtime = (window as any).__molsysviewerRemoteClient;
            const canvas = document.querySelector("canvas") as HTMLCanvasElement | null;
            return runtime?.socket?.readyState === WebSocket.OPEN
                && canvas !== null && canvas.width > 0 && canvas.height > 0;
        }, undefined, { timeout: 30_000 });
        const surface = await page.evaluate(async () => {
            await document.fonts.ready;
            const fontStyle = document.querySelector<HTMLStyleElement>("#molsysviewer-font-varela");
            return {
                canvases: document.querySelectorAll("canvas").length,
                videos: document.querySelectorAll("video").length,
                webgl2: !!document.querySelector("canvas")?.getContext("webgl2"),
                embeddedVarela: fontStyle?.textContent?.includes("data:font/woff2;base64,") === true,
                varelaLoaded: document.fonts.check('12px "Varela Round"'),
                externalFontLinks: document.querySelectorAll('link[href*="fonts.googleapis.com"]').length,
                status: document.querySelector('[data-molsysviewer-remote-status]')?.getAttribute(
                    "data-molsysviewer-remote-status",
                ),
            };
        });
        assert.equal(surface.canvases, 1);
        assert.equal(surface.videos, 0, "client rendering must not create a remote video viewport");
        assert.equal(surface.webgl2, true);
        assert.equal(surface.embeddedVarela, true);
        assert.equal(surface.varelaLoaded, true);
        assert.equal(surface.externalFontLinks, 0);
        assert.equal(surface.status, "ready");

        await page.evaluate(() => {
            const runtime = (window as any).__molsysviewerRemoteClient;
            (window as any).__molsysviewerClientRenderSocketBeforeReconnect = runtime.socket;
            runtime.socket.close(4000, "E2E client-render reconnect probe");
        });
        await page.waitForFunction(() => {
            const runtime = (window as any).__molsysviewerRemoteClient;
            return runtime.socket !== (window as any).__molsysviewerClientRenderSocketBeforeReconnect
                && runtime.socket.readyState === WebSocket.OPEN
                && runtime.registered === true
                && document.querySelectorAll("canvas").length === 1;
        }, undefined, { timeout: 30_000 });

        const cameraBefore = await requestBridge(
            bridge,
            lines,
            "camera",
            "MSV_CLIENT_RENDER_CAMERA=",
        );
        assert.ok(cameraBefore, "Python must observe the initial client camera snapshot");
        const canvasBox = await page.locator("canvas").boundingBox();
        assert.ok(canvasBox, "the local Mol* canvas must have a visible bounding box");
        await page.mouse.move(
            canvasBox.x + canvasBox.width * 0.5,
            canvasBox.y + canvasBox.height * 0.5,
        );
        await page.mouse.down();
        await page.mouse.move(
            canvasBox.x + canvasBox.width * 0.68,
            canvasBox.y + canvasBox.height * 0.57,
            { steps: 12 },
        );
        await page.mouse.up();
        await page.waitForTimeout(700);
        const cameraAfter = await requestBridge(
            bridge,
            lines,
            "camera",
            "MSV_CLIENT_RENDER_CAMERA=",
        );
        assert.notDeepEqual(cameraAfter, cameraBefore, "local canvas drag must update Python camera state");

        let pickedSelectionCount = 0;
        for (const y of [0.4, 0.5, 0.6]) {
            for (const x of [0.35, 0.45, 0.5, 0.55, 0.65]) {
                await page.mouse.click(
                    canvasBox.x + canvasBox.width * x,
                    canvasBox.y + canvasBox.height * y,
                );
                await page.waitForTimeout(100);
                const selection = await requestBridge(
                    bridge,
                    lines,
                    "selection-count",
                    "MSV_CLIENT_RENDER_SELECTION=",
                );
                pickedSelectionCount = selection.count;
                if (pickedSelectionCount > 0) break;
            }
            if (pickedSelectionCount > 0) break;
        }
        assert.ok(pickedSelectionCount > 0, "local canvas click must produce an authoritative molecular pick");

        await page.locator('[data-molsysviewer-group-panel-toggle="true"]').click();
        await page.locator('[data-molsysviewer-group-panel-tab="whole"]').click();
        const representation = page.locator('select[data-molsysviewer-whole-representation="true"]');
        await representation.waitFor({ state: "visible", timeout: 10_000 });
        await representation.selectOption("spacefill");
        await page.waitForFunction(() =>
            (document.querySelector('select[data-molsysviewer-whole-representation="true"]') as HTMLSelectElement | null)?.value
                === "spacefill"
        );
        await page.locator('[data-molsysviewer-group-panel-tab="system"]').click();
        const groupItem = page.locator('[data-molsysviewer-group-item="true"]').first();
        await groupItem.waitFor({ state: "visible", timeout: 10_000 });
        await groupItem.click();
        await page.locator('[data-molsysviewer-group-panel-tab="selection"]').click();
        await page.locator('[data-molsysviewer-active-selection-card="true"]').waitFor({
            state: "visible",
            timeout: 10_000,
        });

        const trajectorySlider = page.locator('[data-molsysviewer-trajectory-frame="true"]');
        await trajectorySlider.waitFor({ state: "visible", timeout: 10_000 });
        await trajectorySlider.fill("7");
        await page.waitForFunction(() =>
            (document.querySelector('[data-molsysviewer-trajectory-frame="true"]') as HTMLInputElement | null)?.value
                === "7"
        );
        await page.locator('[data-molsysviewer-trajectory-step="next"]').click();
        await page.waitForFunction(() =>
            (document.querySelector('[data-molsysviewer-trajectory-frame="true"]') as HTMLInputElement | null)?.value
                === "8"
        );

        await page.locator('[data-molsysviewer-group-panel-tab="export"]').click();
        const pngDownloadPromise = page.waitForEvent("download", { timeout: 30_000 });
        await page.locator('[data-molsysviewer-export-image="true"]').click();
        const pngDownload = await pngDownloadPromise;
        assert.equal(pngDownload.suggestedFilename(), "molsysviewer.png");
        const pngStream = await pngDownload.createReadStream();
        assert.ok(pngStream, "local PNG download must expose a byte stream");
        const pngHeader = await new Promise<Buffer>((resolveHeader, rejectHeader) => {
            pngStream!.once("data", chunk => resolveHeader(Buffer.from(chunk).subarray(0, 8)));
            pngStream!.once("error", rejectHeader);
        });
        assert.deepEqual([...pngHeader], [137, 80, 78, 71, 13, 10, 26, 10]);
        // Reading one chunk leaves the artifact attached to the browser, and closing the
        // browser then rejects that pending read as an unhandled `TargetClosedError` --
        // after every assertion has passed and the suite has printed that it did. Node
        // turns the rejection into a non-zero exit, so the runner reported a failure for
        // a suite that succeeded.
        pngStream!.destroy();

        const htmlDownloadPromise = page.waitForEvent("download", { timeout: 30_000 });
        await page.locator('[data-molsysviewer-export-html="true"]').click();
        const htmlDownload = await htmlDownloadPromise;
        assert.equal(htmlDownload.suggestedFilename(), "molsysviewer.html");
        const htmlStream = await htmlDownload.createReadStream();
        assert.ok(htmlStream, "canonical HTML download must expose a byte stream");
        const htmlPrefix = await new Promise<string>((resolvePrefix, rejectPrefix) => {
            htmlStream!.once("data", chunk => resolvePrefix(Buffer.from(chunk).subarray(0, 64).toString("utf8")));
            htmlStream!.once("error", rejectPrefix);
        });
        assert.match(htmlPrefix.toLowerCase(), /<!doctype html>/);
        htmlStream!.destroy();

        const preUploadState = await requestBridge(
            bridge,
            lines,
            "state",
            "MSV_CLIENT_RENDER_STATE=",
        );
        assert.equal(preUploadState.n_atoms, 62);
        assert.ok(preUploadState.selection_count > 0);
        assert.equal(preUploadState.trajectory_frame, 8);
        assert.equal(preUploadState.whole_representation, "spacefill");

        await page.locator('[data-molsysviewer-upload-input="true"]').setInputFiles({
            name: "client-upload.pdb",
            mimeType: "chemical/x-pdb",
            buffer: Buffer.from(UPLOAD_PDB),
        });
        await page.locator('[data-molsysviewer-upload-status="loaded"]').waitFor({
            state: "visible",
            timeout: 30_000,
        });
        assert.match(
            await page.locator('[data-molsysviewer-upload-status="loaded"]').innerText(),
            /client-upload\.pdb: 4 atoms · 1 frame/,
        );

        bridge.stdin.write("stop\n");
        const result = await waitForJson(lines, "MSV_CLIENT_RENDER_RESULT=");
        const {
            active_selection_count: activeSelectionCount,
            trajectory_frame: trajectoryFrame,
            ...lifecycle
        } = result;
        assert.equal(activeSelectionCount, 0, "replacement upload must clear the stale selection");
        assert.equal(trajectoryFrame, 0, "replacement upload must reset the trajectory frame");
        assert.deepEqual(lifecycle, {
            ready: true,
            structure_complete: true,
            n_atoms: 4,
            registrations: 2,
            whole_representation: null,
            service_failure: null,
        });
        await page.waitForFunction(() =>
            document.querySelector('[data-molsysviewer-remote-status]')?.getAttribute(
                "data-molsysviewer-remote-status",
            ) === "disconnected",
            undefined,
            { timeout: 5_000 },
        );
        assert.deepEqual(errors, []);
        console.log("[E2E remote-client-rendering] local WebGL, reconnect, actions, exports and upload passed");
    } finally {
        await browser?.close();
        if (!bridge.killed) bridge.kill("SIGTERM");
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
