import { spawnSync } from "node:child_process";
import { createReadStream, readFileSync, rmSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

type RepresentativeHarness = Pick<
    typeof import("../e2e/harness"),
    "createController" | "profileRepresentativeArrayNativeLoad"
>;

const __dirname = dirname(fileURLToPath(import.meta.url));
const CASE = process.env.MOLSYSVIEWER_SCALE_CASE ?? "small";
const STRUCTURES = Number(process.env.MOLSYSVIEWER_SCALE_STRUCTURES ?? "1");
const PYTHON = process.env.PYTHON ?? "python";
const EMITTER = resolve(__dirname, "../../../../devtools/benchmarks/representative_scale_gate.py");
const MATRIX = (process.env.MOLSYSVIEWER_SCALE_MATRIX ?? `${CASE}:${STRUCTURES}`)
    .split(",")
    .filter(Boolean)
    .map(item => {
        const [caseName, structuresText] = item.split(":");
        const structures = Number(structuresText);
        if (!caseName || !Number.isInteger(structures) || structures <= 0) {
            throw new Error(`invalid representative-scale matrix item ${JSON.stringify(item)}`);
        }
        return { caseName, structures };
    });

function median(values: number[]): number | null {
    if (!values.length) return null;
    const ordered = [...values].sort((a, b) => a - b);
    return ordered[Math.floor(ordered.length / 2)];
}

type ProcessMemory = { totalMb: number; gpuMb: number; rendererMb: number };

function processTreeMemory(rootPid: number): ProcessMemory | null {
    try {
        const pending = [rootPid];
        const seen = new Set<number>();
        let total = 0;
        let gpu = 0;
        let renderer = 0;
        while (pending.length) {
            const pid = pending.pop()!;
            if (seen.has(pid)) continue;
            seen.add(pid);
            const childrenText = readFileSync(`/proc/${pid}/task/${pid}/children`, "utf8").trim();
            if (childrenText) pending.push(...childrenText.split(/\s+/).map(Number));
            const residentPages = Number(readFileSync(`/proc/${pid}/statm`, "utf8").split(/\s+/)[1]);
            const rss = residentPages * 4096;
            const command = readFileSync(`/proc/${pid}/cmdline`, "utf8").replaceAll("\0", " ");
            total += rss;
            if (command.includes("--type=gpu-process")) gpu += rss;
            if (command.includes("--type=renderer")) renderer += rss;
        }
        const mib = 1024 * 1024;
        return { totalMb: total / mib, gpuMb: gpu / mib, rendererMb: renderer / mib };
    } catch {
        return null;
    }
}

async function runCase(
    browser: Awaited<ReturnType<typeof chromium.connect>>,
    browserPid: number,
    caseName: string,
    structures: number,
) {
    const fixtureDir = join(tmpdir(), `molsysviewer-scale-${process.pid}-${caseName}-${structures}`);
    const emitted = spawnSync(PYTHON, [
        EMITTER,
        "--case", caseName,
        "--structures", String(structures),
        "--emit-directory", fixtureDir,
    ], { encoding: "utf8" });
    if (emitted.status !== 0) {
        throw new Error(`representative fixture generation failed:\n${emitted.stderr || emitted.stdout}`);
    }
    const pythonPreparation = JSON.parse(emitted.stdout.split("\n").filter(Boolean).at(-1)!);
    const manifest = JSON.parse(readFileSync(join(fixtureDir, "manifest.json"), "utf8"));
    const files = [manifest.metadata, ...manifest.arrays];
    const server = createServer((request, response) => {
        const filename = request.url?.slice(1) ?? "";
        if (!files.includes(filename)) {
            response.writeHead(404).end();
            return;
        }
        const path = join(fixtureDir, filename);
        response.writeHead(200, {
            "Content-Type": filename.endsWith(".json") ? "application/json" : "application/octet-stream",
            "Content-Length": statSync(path).size,
            "Cache-Control": "no-store",
            "Access-Control-Allow-Origin": "*",
        });
        createReadStream(path).pipe(response);
    });
    await new Promise<void>((resolveReady, reject) => {
        server.once("error", reject);
        server.listen(0, "127.0.0.1", resolveReady);
    });
    const address = server.address();
    if (!address || typeof address === "string") throw new Error("benchmark server has no port");
    const base = `http://127.0.0.1:${address.port}`;

    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const processMemoryBefore = processTreeMemory(browserPid);
    let processMemoryPeak = processMemoryBefore;
    const memorySampler = setInterval(() => {
        const sample = processTreeMemory(browserPid);
        if (!sample) return;
        if (!processMemoryPeak || sample.totalMb > processMemoryPeak.totalMb) {
            processMemoryPeak = sample;
        }
    }, 25);
    let output: Record<string, unknown> | undefined;
    try {
        await page.setContent('<div id="root" style="width:1280px;height:900px"></div>');
        await page.addScriptTag({ path: resolve(__dirname, "../e2e/harness.bundle.js") });
        await page.waitForFunction(() => Boolean(
            (window as Window & { Harness?: RepresentativeHarness }).Harness,
        ));
        const report = await page.evaluate(async ({ metadataUrl, arrayUrls }) => {
            const harness = (window as Window & { Harness?: RepresentativeHarness }).Harness!;
            const controller = await harness.createController("root");
            const measured = await harness.profileRepresentativeArrayNativeLoad(
                controller, metadataUrl, arrayUrls,
            );
            controller.dispose();
            const runtime = globalThis as typeof globalThis & { gc?: () => void };
            runtime.gc?.();
            await new Promise(resolve => setTimeout(resolve, 100));
            const afterDispose = (performance as any).memory?.usedJSHeapSize ?? 0;
            return { ...measured, jsHeapMb: { ...measured.jsHeapMb, afterDispose: afterDispose / 1024 / 1024 } };
        }, {
            metadataUrl: `${base}/${manifest.metadata}`,
            arrayUrls: manifest.arrays.map((name: string) => `${base}/${name}`),
        });
        const positions = report.timingsMs.frameFirstVisits.map((_, index) => index);
        const unvisitedPositions = positions.filter(
            index => report.timingsMs.frameFirstVisits[index],
        );
        const revisitedPositions = positions.filter(
            index => !report.timingsMs.frameFirstVisits[index],
        );
        const unvisitedFrames = unvisitedPositions.map(
            index => report.timingsMs.frameChanges[index],
        );
        report.timingsMs.unvisitedFrameMedian = median(unvisitedFrames);
        report.timingsMs.unvisitedFrameMax = unvisitedFrames.length
            ? Math.max(...unvisitedFrames)
            : null;
        report.timingsMs.revisitedFrameMedian = median(
            revisitedPositions.map(index => report.timingsMs.frameChanges[index]),
        );
        report.timingsMs.unvisitedFrameCommitMedian = median(
            unvisitedPositions.map(index => report.timingsMs.frameChangeCommits[index]),
        );
        report.timingsMs.revisitedFrameCommitMedian = median(
            revisitedPositions.map(index => report.timingsMs.frameChangeCommits[index]),
        );
        output = {
            schemaVersion: 1,
            case: caseName,
            structures,
            pythonPreparation,
            browser: report,
            limitations: [
                "JS heap excludes Mol* native, WebGL and GPU allocations; process-tree RSS is reported separately.",
                "SwiftShader process RSS is not hardware-GPU VRAM evidence.",
                "Fixture generation is MolSysMT-owned and reported separately.",
            ],
        };
    } finally {
        await page.close();
        clearInterval(memorySampler);
        await new Promise<void>(resolveClosed => server.close(() => resolveClosed()));
        rmSync(fixtureDir, { recursive: true, force: true });
    }
    if (!output) throw new Error("representative scale case produced no report");
    output.browserProcessRssMb = {
        before: processMemoryBefore,
        peak: processMemoryPeak,
        afterPageClose: processTreeMemory(browserPid),
    };
    console.log(JSON.stringify(output));
}

async function run() {
    const browserServer = await chromium.launchServer({
        headless: true,
        executablePath: process.env.PW_CHROMIUM_BIN || "/usr/bin/google-chrome",
        args: [
            "--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader", "--enable-precise-memory-info",
            "--js-flags=--expose-gc",
        ],
    });
    const browser = await chromium.connect(browserServer.wsEndpoint());
    try {
        for (const { caseName, structures } of MATRIX) {
            await runCase(browser, browserServer.process().pid, caseName, structures);
        }
    } finally {
        await browser.close();
        await browserServer.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
