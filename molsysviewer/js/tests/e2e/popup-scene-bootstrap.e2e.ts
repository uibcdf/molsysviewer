import assert from "node:assert/strict";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";
import { checkMovingCapture } from "./moving-capture-scenarios";

async function run() {
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        await checkMovingCapture(page, dirname(fileURLToPath(import.meta.url)), "bootstrap");
        assert.deepEqual(errors, [], "popup bootstrap/retry must not raise page errors");
    } finally { await browser.close(); }
}

run().catch(error => { console.error(error); process.exit(1); });
