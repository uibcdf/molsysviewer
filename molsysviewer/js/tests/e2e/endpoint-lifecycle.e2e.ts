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
            () => (window as any).Harness.probePopupReconstruction(),
        );

        assert.equal(result.oldEndpointClosed, true);
        assert.equal(result.endpointChanged, true);
        assert.equal(result.replacementSessionId, "e2e-new-session");
        assert.equal(result.closeNotificationMatched, true);

        // R2's promise is a lifecycle, not only message validation: the replaced
        // popup must stop being able to act. The second assertion is the control
        // that gives the first one meaning — without it, "refused" also passes
        // for a message that was merely malformed.
        assert.equal(result.staleSessionCommandAccepted, false,
            "a popup from the replaced session still had its command accepted");
        assert.equal(result.currentSessionCommandAccepted, true,
            "the probe's command was refused even for the current session, so the "
            + "assertion above proves nothing");
        assert.deepEqual(errors, []);
        console.log("[E2E endpoint lifecycle] reconstruction revoked the old popup and authenticated a fresh session");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
