import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function run(): Promise<void> {
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage();
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        page.on("console", message => {
            if (message.type() === "error") errors.push(message.text());
        });
        await page.setContent("<!doctype html><html><body></body></html>");
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.waitForFunction(() => Boolean((window as any).Harness));

        const result = await page.evaluate(
            () => (window as any).Harness.probeStructureDataRelay(),
        );

        // The addressed endpoint received it exactly once...
        assert.equal(result.canvasReceived, 1);
        // ...no panel popup is open, so a panel-addressed relay never landed...
        assert.equal(result.panelReceived, 0);
        // ...the chunk identity survived...
        assert.equal(result.chunkId, 4);
        // ...the binary buffer crossed the seam byte for byte...
        assert.equal(result.bytesMatch, true);
        // ...and the popup's acknowledgement came back through the host.
        assert.equal(result.ackAction, "molsysviewer-structure-data-ack");
        // The same addressed seam carries cancellation before JSON fallback.
        assert.equal(result.cancelReceived, 1);
        assert.equal(result.cancelGeneration, 1);
        assert.equal(result.cancelReason, "fallback-to-json");
        assert.deepEqual(errors, []);
        console.log("[E2E structure-data relay] host relayed buffers and targeted cancellation to the addressed popup");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
