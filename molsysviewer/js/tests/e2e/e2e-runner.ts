import { spawn } from "node:child_process";
import process from "node:process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium as playwrightChromium, type BrowserServer } from "playwright";
import { e2eLaunchOptions, failOrExplicitlySkip } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SUITES = [
    "annotations-interaction",
    "annotations-subpanel",
    "array-native-load",
    "popup-channel",
    "endpoint-lifecycle",
    "panel-popup-welcome",
    "structure-data-relay",
    "widget-seam",
    "broken-anchors",
    "export-replay",
    "exported-page-framing",
    "global-reprs-across-loads",
    "group-panel-interaction",
    "hierarchy-interaction",
    "history-coalescing",
    "measurements-interaction",
    "measures-subpanel",
    "range-selection",
    "qt-live-reload",
    "region-hide",
    "region-subpanel",
    "selection-subpanel",
    "layers-subpanel",
    "shape-trajectory",
    "shapes-subpanel",
    "workflow-integration",
    "scientific-workflow",
    "scene-contracts",
    "scene-object-identity",
    "scene-object-panel-roundtrip",
    "bioassembly-chain-identity",
    "trajectory-plot",
    "movie-playback",
] as const;

function runSuite(name: string, endpoint: string): Promise<void> {
    const timeoutMs = Number(process.env.E2E_SUITE_TIMEOUT_MS ?? 180_000);
    return new Promise((resolveSuite, rejectSuite) => {
        const child = spawn(process.execPath, [resolve(__dirname, `${name}.e2e.js`)], {
            env: { ...process.env, E2E_WS_ENDPOINT: endpoint },
            stdio: "inherit",
        });
        const timeout = setTimeout(() => {
            child.kill("SIGKILL");
            rejectSuite(new Error(`${name} exceeded ${timeoutMs} ms`));
        }, timeoutMs);
        child.once("error", error => {
            clearTimeout(timeout);
            rejectSuite(error);
        });
        child.once("exit", (code, signal) => {
            clearTimeout(timeout);
            if (code === 0) {
                resolveSuite();
                return;
            }
            rejectSuite(new Error(`${name} failed with code ${code ?? "null"}${signal ? ` (${signal})` : ""}`));
        });
    });
}

async function run(): Promise<void> {
    let server: BrowserServer;
    try {
        server = await playwrightChromium.launchServer(e2eLaunchOptions());
    } catch (error) {
        failOrExplicitlySkip("shared Chromium launch failed", error);
    }

    try {
        for (const [index, suite] of SUITES.entries()) {
            console.log(`[E2E runner] ${index + 1}/${SUITES.length} ${suite}`);
            await runSuite(suite, server.wsEndpoint());
        }
        console.log(`[E2E runner] ${SUITES.length}/${SUITES.length} suites passed`);
    } finally {
        await server.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
