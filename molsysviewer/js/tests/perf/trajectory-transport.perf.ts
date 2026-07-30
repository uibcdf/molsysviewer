import assert from "node:assert";
import { spawnSync } from "node:child_process";
import { createReadStream, readFileSync, rmSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium, type Page } from "playwright";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CASE = process.env.MOLSYSVIEWER_TRAJECTORY_PERF_CASE ?? "pentalanine-5000";
const PYTHON = process.env.PYTHON ?? "python";
const SCRIPT = resolve(__dirname, "../../../../devtools/benchmarks/trajectory_transport_baseline.py");
const EXTERNAL_PAYLOAD_PATH = process.env.MOLSYSVIEWER_TRAJECTORY_PAYLOAD;
const PAYLOAD_PATH = EXTERNAL_PAYLOAD_PATH
    ? resolve(EXTERNAL_PAYLOAD_PATH)
    : resolve(tmpdir(), `molsysviewer-trajectory-${process.pid}.json`);

type HeapSnapshot = {
    used: number;
    total: number;
};

async function heapSnapshot(page: Page): Promise<HeapSnapshot> {
    return page.evaluate(() => {
        const memory = (performance as Performance & {
            memory?: { usedJSHeapSize: number; totalJSHeapSize: number };
        }).memory;
        return {
            used: memory?.usedJSHeapSize ?? 0,
            total: memory?.totalJSHeapSize ?? 0,
        };
    });
}

function median(values: number[]): number {
    const ordered = [...values].sort((left, right) => left - right);
    return ordered[Math.floor(ordered.length / 2)];
}

async function run(): Promise<void> {
    if (!EXTERNAL_PAYLOAD_PATH) {
        const generated = spawnSync(
            PYTHON,
            [SCRIPT, "emit-payload", "--case", CASE, "--output", PAYLOAD_PATH],
            { encoding: "utf8" },
        );
        if (generated.status !== 0) {
            throw new Error(
                `Payload generation failed (${generated.status}):\n${generated.stderr || generated.stdout}`,
            );
        }
    }

    const payloadBytes = statSync(PAYLOAD_PATH).size;
    const encoded = readFileSync(PAYLOAD_PATH, "utf8");
    const nodeParseStarted = performance.now();
    const nodeMessage = JSON.parse(encoded);
    const nodeParseMs = performance.now() - nodeParseStarted;
    const expectedAtoms = nodeMessage.payload.atoms.atom_id.length;
    const expectedFrames = nodeMessage.payload.structures.length;
    assert.ok(expectedAtoms > 0, "benchmark payload must contain atoms");
    assert.ok(expectedFrames > 1, "trajectory benchmark must contain multiple frames");

    const server = createServer((request, response) => {
        if (request.url !== "/payload.json") {
            response.writeHead(404).end();
            return;
        }
        response.writeHead(200, {
            "Content-Type": "application/json",
            "Content-Length": payloadBytes,
            "Cache-Control": "no-store",
            "Access-Control-Allow-Origin": "*",
        });
        createReadStream(PAYLOAD_PATH).pipe(response);
    });
    await new Promise<void>((resolveReady, reject) => {
        server.once("error", reject);
        server.listen(0, "127.0.0.1", () => resolveReady());
    });
    const address = server.address();
    if (!address || typeof address === "string") {
        throw new Error("Could not determine benchmark server port");
    }
    const payloadUrl = `http://127.0.0.1:${address.port}/payload.json`;

    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        args: [
            "--no-sandbox",
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
            "--enable-precise-memory-info",
            "--js-flags=--expose-gc",
        ],
    });

    try {
        const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
        await page.setContent('<div id="root" style="width:1280px;height:900px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "../e2e/harness.bundle.js") });
        await page.waitForFunction(() => Boolean((window as unknown as { Harness?: unknown }).Harness));
        await page.evaluate(async () => {
            const browserWindow = window as unknown as {
                Harness: { createController(target: string): Promise<unknown> };
                __controller?: unknown;
            };
            browserWindow.__controller = await browserWindow.Harness.createController("root");
        });

        const heapBefore = await heapSnapshot(page);
        const fetchMs = await page.evaluate(async url => {
            const started = performance.now();
            const response = await fetch(url, { cache: "no-store" });
            if (!response.ok) throw new Error(`Payload fetch failed: ${response.status}`);
            (window as unknown as { __payloadText?: string }).__payloadText = await response.text();
            return performance.now() - started;
        }, payloadUrl);
        const heapAfterFetch = await heapSnapshot(page);

        const browserParseMs = await page.evaluate(() => {
            const browserWindow = window as unknown as {
                __payloadText?: string;
                __trajectoryMessage?: Record<string, unknown>;
            };
            if (!browserWindow.__payloadText) throw new Error("Payload text is missing");
            const started = performance.now();
            browserWindow.__trajectoryMessage = JSON.parse(browserWindow.__payloadText);
            const elapsed = performance.now() - started;
            delete browserWindow.__payloadText;
            return elapsed;
        });
        const heapAfterParse = await heapSnapshot(page);

        const loadProfile = await page.evaluate(async expectedAtomCount => {
            const browserWindow = window as unknown as {
                __controller: {
                    handleMessage(message: Record<string, unknown>): Promise<void>;
                    getStructureData(): { elementCount: number } | undefined;
                };
                __trajectoryMessage?: Record<string, unknown>;
            };
            if (!browserWindow.__trajectoryMessage) throw new Error("Parsed payload is missing");
            const memory = () => (performance as Performance & {
                memory?: { usedJSHeapSize: number };
            }).memory?.usedJSHeapSize ?? 0;
            let peakHeap = memory();
            const sampler = setInterval(() => {
                peakHeap = Math.max(peakHeap, memory());
            }, 5);
            const started = performance.now();
            try {
                await browserWindow.__controller.handleMessage(browserWindow.__trajectoryMessage);
            } finally {
                clearInterval(sampler);
            }
            peakHeap = Math.max(peakHeap, memory());
            const elapsed = performance.now() - started;
            const actualAtoms = browserWindow.__controller.getStructureData()?.elementCount ?? 0;
            if (actualAtoms !== expectedAtomCount) {
                throw new Error(`Mol* loaded ${actualAtoms} atoms; expected ${expectedAtomCount}`);
            }
            delete browserWindow.__trajectoryMessage;
            return { elapsed, peakHeap };
        }, expectedAtoms);
        const heapAfterLoad = await heapSnapshot(page);

        const frameIndices = [
            0,
            expectedFrames - 1,
            Math.floor(expectedFrames / 2),
            1,
            expectedFrames - 2,
            Math.floor(expectedFrames / 4),
            Math.floor((expectedFrames * 3) / 4),
            2,
            expectedFrames - 3,
            0,
        ];
        const frameChangeSamplesMs = await page.evaluate(async indices => {
            const controller = (window as unknown as {
                __controller: {
                    handleMessage(message: Record<string, unknown>): Promise<void>;
                };
            }).__controller;
            const samples: number[] = [];
            for (const index of indices) {
                const started = performance.now();
                await controller.handleMessage({ op: "set_trajectory_frame", index });
                samples.push(performance.now() - started);
            }
            return samples;
        }, frameIndices);

        console.log(JSON.stringify({
            schemaVersion: 1,
            case: CASE,
            atoms: expectedAtoms,
            frames: expectedFrames,
            payloadBytes,
            timingsMs: {
                nodeJsonParse: nodeParseMs,
                browserFetchText: fetchMs,
                browserJsonParse: browserParseMs,
                molstarLoad: loadProfile.elapsed,
                frameChangeMedian: median(frameChangeSamplesMs),
                frameChangeMax: Math.max(...frameChangeSamplesMs),
            },
            browserJsHeapMb: {
                before: heapBefore.used / 1024 / 1024,
                afterFetch: heapAfterFetch.used / 1024 / 1024,
                afterParse: heapAfterParse.used / 1024 / 1024,
                sampledPeakDuringMolstarLoad: loadProfile.peakHeap / 1024 / 1024,
                afterLoad: heapAfterLoad.used / 1024 / 1024,
            },
            limitations: [
                "Browser memory is V8 JS heap only; native Mol*, WebGL and GPU allocations are excluded.",
                "Local HTTP fetch approximates the Qt payload-ref decode path, not AnyWidget comm transfer.",
            ],
        }));
    } finally {
        await browser.close();
        await new Promise<void>(resolveClosed => server.close(() => resolveClosed()));
        if (!EXTERNAL_PAYLOAD_PATH) rmSync(PAYLOAD_PATH, { force: true });
    }
}

run().catch(error => {
    console.error(error);
    if (!EXTERNAL_PAYLOAD_PATH) rmSync(PAYLOAD_PATH, { force: true });
    process.exit(1);
});
