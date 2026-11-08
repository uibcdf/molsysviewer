import assert from "node:assert/strict";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";
import { checkMovingCapture } from "./moving-capture-scenarios";

async function run() {
    const browser = await chromium.launch();
    try {
        let page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
        const context = page.context(), errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        await checkMovingCapture(page, dirname(fileURLToPath(import.meta.url)), "lifetimes");
        page = await context.newPage();
        page.on("pageerror", error => errors.push(String(error)));
        await checkMovingCapture(page, dirname(fileURLToPath(import.meta.url)), "freeze");
        assert.deepEqual(errors, [], "capture lifecycle must not raise page errors");
    } finally { await browser.close(); }
}

run().catch(error => { console.error(error); process.exit(1); });
