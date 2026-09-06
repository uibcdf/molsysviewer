/**
 * An embedded export takes the colour of the surface it was dropped on.
 *
 * A view served from a documentation site reads the page around it and copies
 * what is painted behind its own frame — not the `<body>`, but the first
 * ancestor that paints anything, because containers are what a theme styles.
 * `hostBackgroundColour` in `src/index.ts` is the mechanism; this is the only
 * thing that watches it work.
 *
 * **Why these need a server.** Reading the page around you means touching
 * `window.parent.document`, which is a same-origin access. `file://` gives every
 * local file an opaque origin, so `readableHostDocument` returns `undefined` and
 * the view falls back to the reader's own preference. Served over http the
 * mechanism is reachable; from a file it is not there to test. The server is the
 * object of the test, not scaffolding around it.
 *
 * **Why they moved here from Python** (uibcdf/molsysviewer#81). They used to run
 * `google-chrome --headless --screenshot` against a local server, and on the
 * development machine that navigation never completes: the server records no
 * request at all. They had been skipping behind a canary since, and a test that
 * skips permanently checks nothing. Playwright drives the same browser family
 * over CDP and loads the same URL in 0.2 s (uibcdf/molsysviewer#77).
 *
 * **What is asserted, and why the background.** The dominant colour of the
 * frame, not the molecule. Whether the structure finishes drawing is not
 * reliable under a software rasteriser — the same page measured three times gave
 * 6186, 0 and 6172 lit pixels — so an assertion about the molecule would be a
 * flake generator. The colour behind it is stable.
 *
 * The seven `file://` tests stayed in `tests/test_exported_page_opens_from_disk.py`.
 * They ask a different question — whether the browser *the reader installed*
 * opens the file at all — and this suite's pinned Chromium cannot answer it.
 */
import assert from "node:assert";
import process from "node:process";
import { spawnSync } from "node:child_process";
import { createServer, type Server } from "node:http";
import { readFile } from "node:fs/promises";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import type { Frame, Page } from "playwright";
import { chromium } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));

/** Long enough for a software rasteriser to boot Mol* and settle a theme. */
const SETTLE_TIMEOUT_MS = 90_000;

interface Scenario {
    /** The file the host page is written to, and the URL path it is served at. */
    readonly file: string;
    readonly title: string;
    /** What the view must come out, as [r, g, b]. */
    readonly expected: readonly [number, number, number];
    readonly why: string;
    html(page: string): string;
}

const SCENARIOS: readonly Scenario[] = [
    {
        file: "host-dark.html",
        title: "an embedded view takes the colour of the page around it",
        expected: [26, 26, 26],
        why: "the view did not take the dark host's background",
        // The site's own theme switch is invisible to every media query: it is an
        // attribute on the host's document, and only a same-origin view can read
        // the colour it produces. Copying it is what stops a view being a bright
        // rectangle on a dark documentation page.
        html: page =>
            "<!DOCTYPE html><html data-theme='x'><body style='margin:0;background:#1a1a1a'>"
            + `<iframe src='./${page}' width='400' height='300' `
            + "style='border:none;display:block'></iframe></body></html>",
    },
    {
        file: "host-light.html",
        title: "the same view is light on a light page",
        expected: [255, 255, 255],
        why: "the view did not take the light host's background",
        // Same file, same reader, different page: the answer comes from the host.
        html: page =>
            "<!DOCTYPE html><html data-theme='x'><body style='margin:0;background:#ffffff'>"
            + `<iframe src='./${page}' width='400' height='300' `
            + "style='border:none;display:block'></iframe></body></html>",
    },
    {
        file: "host-container.html",
        title: "the view matches the container it was dropped into",
        expected: [34, 40, 50],
        why: "the view took the page's colour instead of the container's",
        // Reported from MolSysMT's own site. `pydata-sphinx-theme` paints the
        // wrapper around a notebook's HTML output in dark mode --
        // `.cell_output .text_html`, `#222832`, with padding -- over a near-black
        // page. A view that copied the *body* sat inside a rectangle a shade
        // lighter than itself, which is the grey frame the reader sees. The view
        // must come out `#222832`, with no help from the site's own CSS.
        html: page =>
            "<!DOCTYPE html><html data-theme='dark'><head><style>"
            + "body { background:#14181f; margin:0 }"
            + ".cell_output .text_html { background-color:#222832; border-radius:.25rem; padding:.5rem }"
            + "</style></head><body><div class='bd-content'><div class='cell_output'>"
            + `<div class='output text_html'><iframe src='./${page}' `
            + "width='400' height='300' style='border:none;display:block'></iframe>"
            + "</div></div></div></body></html>",
    },
];

function serve(directory: string): Promise<{ server: Server; port: number }> {
    const server = createServer(async (request, response) => {
        // Only the export and the host pages live here, and only this suite asks.
        const name = decodeURIComponent((request.url ?? "/").split("?")[0]).replace(/^\/+/, "");
        try {
            const body = await readFile(join(directory, name));
            response.writeHead(200, {
                "Content-Type": name.endsWith(".html") ? "text/html; charset=utf-8" : "application/octet-stream",
            });
            response.end(body);
        } catch {
            response.writeHead(404).end("not found");
        }
    });
    return new Promise(resolveServer => {
        server.listen(0, "127.0.0.1", () => {
            resolveServer({ server, port: (server.address() as any).port });
        });
    });
}

/** The colour the runtime says it applied, once it stops changing. */
async function reportedBackground(frame: Frame, expected: number): Promise<number | undefined> {
    const deadline = Date.now() + SETTLE_TIMEOUT_MS;
    let last: number | undefined;
    while (Date.now() < deadline) {
        last = await frame.evaluate(() => {
            const controller = (window as any).__molsysviewerDocsController;
            const value = controller?.plugin?.canvas3d?.props?.renderer?.backgroundColor;
            return typeof value === "number" ? value : undefined;
        });
        // Settled on the right answer: stop early. Settled on a wrong one: keep
        // waiting, and let the pixels below report it rather than this loop.
        if (last === expected) break;
        await new Promise(r => setTimeout(r, 250));
    }
    // The renderer clears every frame; give the last applied colour one to land.
    await new Promise(r => setTimeout(r, 1000));
    return last;
}

/** The most common exact RGB in a PNG, counted by the browser that made it. */
async function dominantColour(page: Page, png: Buffer): Promise<{ rgb: number[]; share: number }> {
    return page.evaluate(async (dataUrl: string) => {
        const image = new Image();
        await new Promise((done, failed) => {
            image.onload = () => done(null);
            image.onerror = () => failed(new Error("the screenshot did not decode"));
            image.src = dataUrl;
        });
        const canvas = document.createElement("canvas");
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        const context = canvas.getContext("2d")!;
        context.drawImage(image, 0, 0);
        const { data } = context.getImageData(0, 0, canvas.width, canvas.height);

        const counts = new Map<number, number>();
        for (let index = 0; index < data.length; index += 4) {
            const key = (data[index] << 16) | (data[index + 1] << 8) | data[index + 2];
            counts.set(key, (counts.get(key) ?? 0) + 1);
        }
        let best = -1;
        let bestCount = -1;
        for (const [key, count] of counts) {
            if (count > bestCount) {
                best = key;
                bestCount = count;
            }
        }
        return {
            rgb: [(best >> 16) & 255, (best >> 8) & 255, best & 255],
            share: bestCount / (data.length / 4),
        };
    }, `data:image/png;base64,${png.toString("base64")}`);
}

const hex = (colour: number | undefined) =>
    colour === undefined ? "none" : `#${colour.toString(16).padStart(6, "0")}`;

async function run() {
    console.log("[E2E exported-page-colour] Scenario: an export copies the surface it sits on");

    const python = spawnSync(
        process.env.PYTHON_BIN || "python",
        [resolve(__dirname, "exported-page-colour-bridge.py")],
        { encoding: "utf8", cwd: resolve(__dirname, "../../../..") },
    );
    assert.strictEqual(python.status, 0, python.stderr || python.stdout);
    const exported = JSON.parse(python.stdout);
    console.log(`[E2E exported-page-colour]   exported ${exported.page} to ${exported.directory}`);

    for (const scenario of SCENARIOS) {
        writeFileSync(join(exported.directory, scenario.file), scenario.html(exported.page), "utf8");
    }

    const { server, port } = await serve(exported.directory);
    const browser = await chromium.launch({ headless: true });
    // One context per suite is the shared browser's contract, so the three
    // scenarios are three navigations of one page rather than three pages.
    const page = await browser.newPage({ viewport: { width: 400, height: 300 } });
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(String(error)));

    try {
        for (const scenario of SCENARIOS) {
            const [r, g, b] = scenario.expected;
            const wanted = (r << 16) | (g << 8) | b;

            await page.goto(`http://127.0.0.1:${port}/${scenario.file}`);

            const element = await page.locator("iframe").elementHandle();
            assert.ok(element, `${scenario.title}: the host page has no iframe`);
            const frame = await element.contentFrame();
            assert.ok(frame, `${scenario.title}: the iframe never produced a document`);

            await frame.waitForFunction(
                () => !!(window as any).__molsysviewerDocsController?.plugin?.canvas3d,
                undefined,
                { timeout: SETTLE_TIMEOUT_MS },
            );
            const reported = await reportedBackground(frame, wanted);

            const measured = await dominantColour(page, await element.screenshot({ type: "png" }));
            console.log(
                `[E2E exported-page-colour]   ${scenario.title}: `
                + `reported ${hex(reported)}, sampled #${measured.rgb
                    .map(part => part.toString(16).padStart(2, "0")).join("")} `
                + `over ${(measured.share * 100).toFixed(0)}% of the frame`,
            );

            // The decision, exactly. This is the mechanism the suite exists for, and
            // it is the assertion a runtime that ignored its host fails first.
            assert.strictEqual(
                reported,
                wanted,
                `${scenario.why}: the runtime applied ${hex(reported)} where `
                + `${hex(wanted)} was wanted.`,
            );

            // The frame really is that colour, and not a sliver of one.
            assert.ok(
                measured.share > 0.5,
                `${scenario.title}: no colour covers half the frame -- the most common `
                + `is rgb(${measured.rgb.join(", ")}) at ${(measured.share * 100).toFixed(0)}%, `
                + "so the canvas is probably not what was sampled.",
            );

            // And it reached the screen, to within one unit per channel.
            //
            // The unit is measured, not defensive. Over ten runs the runtime reported
            // `#1a1a1a` every single time, and the frame sampled `#1b1b1b` in eight of
            // them and `#1a1a1a` in two -- one under the runner's shared browser
            // server, one from a standalone launch, so it follows neither the launch
            // path nor a stale build; both of those were guessed and both were wrong.
            // `#ffffff` and `#222832` came out exact in all ten. Whatever moves the
            // last bit of a dark clear colour, it is not the mechanism under test, and
            // asserting equality here would buy a flake and no information.
            //
            // The exact assertion above is where a real regression lands: a view that
            // ignores its host reports Mol*'s own background instead, which was
            // `#fcfbf9` when that mutation was run -- wrong by more than two hundred.
            for (let channel = 0; channel < 3; channel += 1) {
                assert.ok(
                    Math.abs(measured.rgb[channel] - scenario.expected[channel]) <= 1,
                    `${scenario.why}: it sampled rgb(${measured.rgb.join(", ")}) where `
                    + `rgb(${scenario.expected.join(", ")}) was wanted, and the runtime `
                    + `reports having applied ${hex(reported)}.`,
                );
            }
        }

        assert.deepStrictEqual(errors, [], "the exported page raised errors while taking its colour");
        console.log("[E2E exported-page-colour]   all three surfaces were copied");
    } finally {
        await browser.close();
        await new Promise(done => server.close(() => done(null)));
    }

    console.log("[E2E exported-page-colour] passed");
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
