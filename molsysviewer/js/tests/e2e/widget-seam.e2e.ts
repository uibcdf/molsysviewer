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
        await page.setContent("<!doctype html><html><body></body></html>");
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.waitForFunction(() => Boolean((window as any).Harness));

        const result = await page.evaluate(
            () => (window as any).Harness.probeWidgetSeam(),
        );

        // The bootstrap handshake must stay outside the envelope, or it would
        // deadlock: the adapter does not exist yet when it is sent.
        assert.equal(result.readyRaw, true, "ready must leave raw");
        // With popout disabled the binary path is advertised.
        assert.equal(result.readyAdvertisesBinary, true, "ready must advertise binary capability");
        // Ordinary browser->Python traffic is enveloped.
        assert.equal(result.outboundEnveloped, true, "outbound events must be enveloped");
        // A valid projection IS unwrapped and reaches the controller. Without
        // this the isolation check below would hold vacuously.
        assert.equal(result.projectionApplied, true, "a valid projection must reach the controller");
        // A projection for another session must never reach the controller.
        assert.equal(result.foreignSessionApplied, false, "a foreign session must not be applied");

        console.log("[E2E widget seam] real render(): raw ready, enveloped outbound, session isolation held");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
