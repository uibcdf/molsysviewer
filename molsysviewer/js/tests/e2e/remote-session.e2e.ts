import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
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

function waitForPrefixedJson(lines: ReturnType<typeof createInterface>, prefix: string): Promise<Record<string, any>> {
    return new Promise((resolveValue, rejectValue) => {
        const onLine = (line: string) => {
            if (!line.startsWith(prefix)) return;
            cleanup();
            resolveValue(JSON.parse(line.slice(prefix.length)));
        };
        const onClose = () => {
            cleanup();
            rejectValue(new Error(`Python bridge ended before ${prefix}`));
        };
        const cleanup = () => {
            lines.off("line", onLine);
            lines.off("close", onClose);
        };
        lines.on("line", onLine);
        lines.on("close", onClose);
    });
}

function assertHardwareRenderer(session: Record<string, any>): void {
    assert.equal(session.webgl2, true, "the render worker must expose WebGL2");
    assert.equal(session.software_rendering, false, `software renderer is not server-rendering evidence: ${session.renderer}`);
    assert.equal(typeof session.renderer, "string");
    assert.ok(session.renderer.length > 0, "the render worker must report its renderer");
    assert.doesNotMatch(session.renderer, /swiftshader|llvmpipe|softpipe|software rasterizer/i);

    const expected = process.env.MSV_EXPECTED_GPU_REGEX;
    if (!expected) return;
    let pattern: RegExp;
    try {
        pattern = new RegExp(expected, "i");
    } catch (error) {
        throw new Error(`MSV_EXPECTED_GPU_REGEX is invalid: ${expected}`, { cause: error });
    }
    assert.match(
        session.renderer,
        pattern,
        `renderer does not match the site certification pattern ${expected}`,
    );
}

async function run(): Promise<void> {
    const bridge = spawn(
        process.env.PYTHON || "python",
        [resolve(__dirname, "remote-session-bridge.py")],
        { stdio: ["pipe", "pipe", "inherit"] },
    );
    const lines = createInterface({ input: bridge.stdout });
    let browser: Awaited<ReturnType<typeof chromium.launch>> | null = null;
    try {
        const session = await waitForPrefixedJson(lines, "MSV_REMOTE_SESSION=");
        assertHardwareRenderer(session);

        browser = await chromium.launch();
        const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        page.on("console", message => {
            if (message.type() === "error") errors.push(message.text());
        });
        await page.goto(session.client_url, { waitUntil: "domcontentloaded" });
        try {
            await page.waitForFunction(() => {
                const runtime = (window as any).__molsysviewerRemoteClient;
                return runtime?.video?.readyState >= 2
                    && runtime?.video?.videoWidth > 0
                    && runtime?.peerConnection?.()?.connectionState === "connected";
            }, undefined, { timeout: 30_000 });
        } catch (error) {
            const client = await page.evaluate(() => {
                const runtime = (window as any).__molsysviewerRemoteClient;
                const peer = runtime?.peerConnection?.();
                return {
                    runtime: !!runtime,
                    socket: runtime?.socket?.readyState,
                    connectionState: peer?.connectionState,
                    iceConnectionState: peer?.iceConnectionState,
                    signalingState: peer?.signalingState,
                    videoReadyState: runtime?.video?.readyState,
                    videoWidth: runtime?.video?.videoWidth,
                    status: document.querySelector('[data-molsysviewer-remote-status]')?.textContent,
                };
            });
            bridge.stdin.write("stop\n");
            const backend = await waitForPrefixedJson(lines, "MSV_REMOTE_RESULT=");
            throw new Error(`remote peer timeout: ${JSON.stringify({ client, backend, errors })}`, { cause: error });
        }

        const video = await page.evaluate(async () => {
            const runtime = (window as any).__molsysviewerRemoteClient;
            const reports = await runtime.peerConnection().getStats();
            let framesDecoded = 0;
            reports.forEach((report: any) => {
                if (report.type === "inbound-rtp" && report.kind === "video") {
                    framesDecoded = Math.max(framesDecoded, Number(report.framesDecoded || 0));
                }
            });
            return {
                width: runtime.video.videoWidth,
                height: runtime.video.videoHeight,
                framesDecoded,
                localCanvasCount: document.querySelectorAll("canvas").length,
            };
        });
        assert.equal(video.width, 1920);
        assert.equal(video.height, 1080);
        assert.ok(video.framesDecoded > 0, "the browser must decode live video frames");
        assert.equal(video.localCanvasCount, 0, "the remote client must not initialize Mol*/WebGL");

        const peerBeforeWorkerRecovery = await page.evaluate(() => {
            const runtime = (window as any).__molsysviewerRemoteClient;
            (window as any).__molsysviewerPeerBeforeWorkerRecovery = runtime.peerConnection();
            return runtime.peerConnection()?.connectionState;
        });
        assert.equal(peerBeforeWorkerRecovery, "connected");
        const recoveryPromise = waitForPrefixedJson(lines, "MSV_REMOTE_WORKER_RECOVERED=");
        bridge.stdin.write("kill-worker\n");
        const recovery = await recoveryPromise;
        assert.equal(recovery.state, "recovered");
        assert.notEqual(recovery.pid, recovery.previous_pid);
        await page.waitForFunction(() => {
            const runtime = (window as any).__molsysviewerRemoteClient;
            const peer = runtime.peerConnection?.();
            return peer
                && peer !== (window as any).__molsysviewerPeerBeforeWorkerRecovery
                && peer.connectionState === "connected"
                && runtime.video.readyState >= 2
                && runtime.video.videoWidth === 1920
                && runtime.video.videoHeight === 1080;
        }, undefined, { timeout: 45_000 });

        await page.evaluate(() => {
            const runtime = (window as any).__molsysviewerRemoteClient;
            (window as any).__molsysviewerSocketBeforeReconnect = runtime.socket;
            runtime.socket.close(4000, "E2E reconnect probe");
        });
        try {
            await page.waitForFunction(() => {
                const runtime = (window as any).__molsysviewerRemoteClient;
                return runtime.socket !== (window as any).__molsysviewerSocketBeforeReconnect
                    && runtime.socket.readyState === WebSocket.OPEN
                    && runtime.video.readyState >= 2
                    && runtime.peerConnection?.()?.connectionState === "connected";
            }, undefined, { timeout: 30_000 });
        } catch (error) {
            const client = await page.evaluate(() => {
                const runtime = (window as any).__molsysviewerRemoteClient;
                const peer = runtime.peerConnection?.();
                return {
                    socketReadyState: runtime.socket?.readyState,
                    socketChanged: runtime.socket !== (window as any).__molsysviewerSocketBeforeReconnect,
                    peerConnectionState: peer?.connectionState,
                    peerIceState: peer?.iceConnectionState,
                    videoReadyState: runtime.video?.readyState,
                    status: document.querySelector('[data-molsysviewer-remote-status]')?.textContent,
                    statusKind: document.querySelector('[data-molsysviewer-remote-status]')?.getAttribute('data-molsysviewer-remote-status'),
                };
            });
            bridge.stdin.write("stop\n");
            const backend = await waitForPrefixedJson(lines, "MSV_REMOTE_RESULT=");
            const { worker_peer_diagnostics: workerPeerDiagnostics, ...backendSummary } = backend;
            throw new Error(`remote reconnect timeout: ${JSON.stringify({
                client,
                backend: backendSummary,
                workerPeer: {
                    connectionState: workerPeerDiagnostics?.connectionState,
                    iceConnectionState: workerPeerDiagnostics?.iceConnectionState,
                    signalingState: workerPeerDiagnostics?.signalingState,
                },
                errors,
            })}`, { cause: error });
        }

        await page.evaluate(() => {
            (window as any).__molsysviewerRemoteClient.workbench.panel.setExpanded(true);
        });
        await page.locator('[data-molsysviewer-group-panel-tab="whole"]').click();
        await page.locator('[data-molsysviewer-whole-presence="true"]').waitFor({ timeout: 5_000 });
        const representation = page.locator('select[data-molsysviewer-whole-representation="true"]');
        await representation.selectOption("spacefill");
        await page.waitForFunction(() =>
            (document.querySelector('select[data-molsysviewer-whole-representation="true"]') as HTMLSelectElement | null)?.value === "spacefill"
        );
        await page.locator('[data-molsysviewer-whole-visibility="hide"]').click();
        await page.locator('[data-molsysviewer-whole-visibility="show"]').waitFor({ timeout: 5_000 });
        await page.locator('[data-molsysviewer-whole-visibility="show"]').click();
        await page.locator('[data-molsysviewer-whole-visibility="hide"]').waitFor({ timeout: 5_000 });
        await page.evaluate(() => {
            (window as any).__molsysviewerRemoteClient.workbench.panel.setExpanded(false);
        });

        const trajectorySlider = page.locator('[data-molsysviewer-trajectory-frame="true"]');
        await trajectorySlider.waitFor({ state: "visible", timeout: 5_000 });
        await trajectorySlider.evaluate((element: HTMLInputElement) => {
            element.value = "7";
            element.dispatchEvent(new Event("input", { bubbles: true }));
            element.dispatchEvent(new Event("change", { bubbles: true }));
        });
        await page.waitForFunction(() =>
            (window as any).__molsysviewerRemoteClient.workbench.trajectory.currentFrame === 7
        );
        await page.locator('[data-molsysviewer-trajectory-step="next"]').click();
        await page.waitForFunction(() =>
            (window as any).__molsysviewerRemoteClient.workbench.trajectory.currentFrame === 8
        );

        await page.evaluate(() => {
            (window as any).__molsysviewerRemoteClient.workbench.panel.setExpanded(true);
        });
        await page.locator('[data-molsysviewer-group-panel-tab="export"]').click();
        const downloadPromise = page.waitForEvent("download", { timeout: 30_000 });
        await page.getByRole("button", { name: "Download PNG Image" }).click();
        const download = await downloadPromise;
        assert.equal(download.suggestedFilename(), "molsysviewer.png");
        const downloadStream = await download.createReadStream();
        assert.ok(downloadStream, "remote PNG download must expose a byte stream");
        const pngHeader = await new Promise<Buffer>((resolveHeader, rejectHeader) => {
            downloadStream!.once("data", chunk => resolveHeader(Buffer.from(chunk).subarray(0, 8)));
            downloadStream!.once("error", rejectHeader);
        });
        assert.deepEqual([...pngHeader], [137, 80, 78, 71, 13, 10, 26, 10]);

        const htmlDownloadPromise = page.waitForEvent("download", { timeout: 30_000 });
        await page.getByRole("button", { name: "Download Standalone HTML View" }).click();
        const htmlDownload = await htmlDownloadPromise;
        assert.equal(htmlDownload.suggestedFilename(), "molsysviewer.html");
        const htmlPath = await htmlDownload.path();
        assert.ok(htmlPath, "remote HTML download must have a completed temporary file");
        const html = await readFile(htmlPath!, "utf8");
        assert.match(html.slice(0, 200), /<!doctype html>/i);
        assert.match(html, /MolSysViewer/);
        await page.evaluate(() => {
            (window as any).__molsysviewerRemoteClient.workbench.panel.setExpanded(false);
        });

        const viewport = page.locator('[aria-label="Remote molecular viewport"]');
        const box = await viewport.boundingBox();
        assert.ok(box);

        await page.mouse.move(box!.x + box!.width * 0.45, box!.y + box!.height * 0.5);
        await page.mouse.down();
        await page.mouse.move(box!.x + box!.width * 0.6, box!.y + box!.height * 0.58, { steps: 4 });
        await page.mouse.up();
        await page.waitForTimeout(500);

        let picked = false;
        for (const y of [0.4, 0.5, 0.6]) {
            for (const x of [0.35, 0.45, 0.5, 0.55, 0.65]) {
                await page.mouse.click(box!.x + box!.width * x, box!.y + box!.height * y);
                await page.waitForTimeout(120);
                picked = await page.evaluate(() =>
                    (window as any).__molsysviewerRemoteClient.workbench.activeSelectionAtomCount > 0
                );
                if (picked) break;
            }
            if (picked) break;
        }
        assert.ok(picked, "remote pointer input must produce an authoritative molecular selection");

        await page.locator('[data-molsysviewer-upload-input="true"]').setInputFiles({
            name: "uploaded.pdb",
            mimeType: "chemical/x-pdb",
            buffer: Buffer.from(UPLOAD_PDB),
        });
        await page.locator('[data-molsysviewer-upload-status="loaded"]').waitFor({ timeout: 30_000 });
        await page.waitForFunction(() =>
            document.querySelector('[data-molsysviewer-upload-status="loaded"]')?.textContent?.includes("4 atoms")
        );

        bridge.stdin.write("stop\n");
        const result = await waitForPrefixedJson(lines, "MSV_REMOTE_RESULT=");
        const {
            active_selection_count: activeSelectionCount,
            worker_peer_diagnostics: workerPeerDiagnostics,
            ...lifecycle
        } = result;
        assert.equal(activeSelectionCount, 0, "replacing the molecular system must clear stale selection indices");
        assert.ok(
            workerPeerDiagnostics?.stats?.some((item: any) =>
                item.type === "outbound-rtp" && Number(item.framesEncoded ?? item.framesSent ?? 0) > 0
            ),
            `render worker must encode video frames: ${JSON.stringify(workerPeerDiagnostics)}`,
        );
        assert.deepEqual(lifecycle, {
            video_connected: true,
            input_channel_open: true,
            worker_input_received: true,
            whole_visible: true,
            whole_representation: null,
            trajectory_frame: 0,
            n_atoms: 4,
            label: "uploaded",
            service_failure: null,
            worker_host_failure: null,
            worker_recovery_count: 1,
            worker_recovery_state: "recovered",
        });
        await page.waitForFunction(() =>
            document.querySelector('[data-molsysviewer-remote-status]')?.getAttribute('data-molsysviewer-remote-status') === "disconnected",
            undefined,
            { timeout: 5_000 },
        );
        assert.deepEqual(errors, []);
        console.log("[E2E remote-session] 1080p video, workbench, trajectory, PNG/HTML export, upload, camera and authoritative picking passed");
    } finally {
        await browser?.close();
        if (!bridge.killed) bridge.kill("SIGTERM");
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
