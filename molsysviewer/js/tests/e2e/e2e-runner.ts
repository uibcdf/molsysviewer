import { withFixtureWorkspace, fixtureEnvironment } from "./fixture-workspace";
import { spawn } from "node:child_process";
import process from "node:process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium as playwrightChromium, type BrowserServer } from "playwright";
import { e2eLaunchOptions, failOrExplicitlySkip } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SUITES = [
    "context-menu",
    "controls-visibility",
    "studio-usability",
    "studio-list-workflows",
    "annotations-interaction",
    "annotations-subpanel",
    "array-native-load",
    "coordinate-edits",
    "composite-load",
    "popup-channel",
    "endpoint-lifecycle",
    "panel-popup-welcome",
    "structure-data-relay",
    "widget-seam",
    "broken-anchors",
    "export-replay",
    "exported-page-colour",
    "exported-page-framing",
    "global-reprs-across-loads",
    "group-panel-interaction",
    "hierarchy-interaction",
    "history-coalescing",
    "measurements-interaction",
    "measures-subpanel",
    "interactions-subpanel",
    "interactions-geometry",
    "interactions-calculation",
    "range-selection",
    "qt-live-reload",
    "region-hide",
    "region-subpanel",
    "remote-client-rendering",
    "remote-input",
    "remote-session",
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
const SERVER_GPU_SUITES = new Set<string>(["remote-session"]);
const REMOTE_SUITES = new Set<string>(["remote-client-rendering", "remote-input", "remote-session"]);

function suitesForLane(argument: string | undefined): readonly string[] {
    const lane = argument ?? "--lane=all";
    if (lane === "--lane=all") return SUITES;
    if (lane === "--lane=core") return SUITES.filter(suite => !REMOTE_SUITES.has(suite));
    if (lane === "--lane=portable") return SUITES.filter(suite => !SERVER_GPU_SUITES.has(suite));
    if (lane === "--lane=remote-portable") {
        return SUITES.filter(suite => REMOTE_SUITES.has(suite) && !SERVER_GPU_SUITES.has(suite));
    }
    if (lane === "--lane=server-gpu") return SUITES.filter(suite => SERVER_GPU_SUITES.has(suite));
    throw new Error(`unknown E2E lane ${lane}; choose --lane=all, --lane=core, --lane=portable, --lane=remote-portable or --lane=server-gpu`);
}

function runSuite(name: string, endpoint: string, workspace: string): Promise<void> {
    const timeoutMs = Number(process.env.E2E_SUITE_TIMEOUT_MS ?? 180_000);
    return new Promise((resolveSuite, rejectSuite) => {
        const child = spawn(process.execPath, [resolve(__dirname, `${name}.e2e.js`)], {
            env: { ...fixtureEnvironment(workspace), E2E_WS_ENDPOINT: endpoint },
            stdio: "inherit",
        });
        let timedOut = false;
        const timeout = setTimeout(() => {
            timedOut = true;
            child.kill("SIGKILL");
        }, timeoutMs);
        child.once("error", error => {
            clearTimeout(timeout);
            rejectSuite(error);
        });
        child.once("exit", (code, signal) => {
            clearTimeout(timeout);
            if (timedOut) {
                rejectSuite(new Error(`${name} exceeded ${timeoutMs} ms`));
                return;
            }
            if (code === 0) {
                resolveSuite();
                return;
            }
            rejectSuite(new Error(`${name} failed with code ${code ?? "null"}${signal ? ` (${signal})` : ""}`));
        });
    });
}

async function run(workspace: string): Promise<void> {
    const laneSuites = suitesForLane(process.argv[2]);
    const selection = process.argv.find(argument => argument.startsWith("--suites="))?.slice("--suites=".length).split(",");
    if (selection && (selection.some(name => !laneSuites.includes(name)) || new Set(selection).size !== selection.length)) {
        throw new Error("--suites must name distinct suites included in the selected lane");
    }
    const suites = selection ? laneSuites.filter(name => selection.includes(name)) : laneSuites;
    let server: BrowserServer;
    try {
        server = await playwrightChromium.launchServer(e2eLaunchOptions());
    } catch (error) {
        failOrExplicitlySkip("shared Chromium launch failed", error);
    }

    try {
        for (const [index, suite] of suites.entries()) {
            console.log(`[E2E runner:${process.argv[2] ?? "--lane=all"}] ${index + 1}/${suites.length} ${suite}`);
            await runSuite(suite, server.wsEndpoint(), workspace);
        }
        console.log(`[E2E runner:${process.argv[2] ?? "--lane=all"}] ${suites.length}/${suites.length} suites passed`);
    } finally {
        await server.close();
    }
}

withFixtureWorkspace("run", run).catch(error => {
    console.error(error);
    process.exit(1);
});
