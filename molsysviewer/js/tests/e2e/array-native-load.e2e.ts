import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "./e2e-browser";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function run(): Promise<void> {
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage({ viewport: { width: 900, height: 700 } });
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        page.on("console", message => {
            if (message.type() === "error") errors.push(message.text());
        });
        await page.setContent(
            '<!doctype html><html><body><div id="root" style="width:800px;height:600px"></div></body></html>',
        );
        await page.addScriptTag({ path: resolve(__dirname, "harness.bundle.js") });
        await page.waitForFunction(() => Boolean((window as any).Harness));

        const result = await page.evaluate(async () => {
            const harness = (window as any).Harness;
            const controller = await harness.createController("root");
            return harness.loadArrayNativeFixture(controller);
        });

        assert.deepEqual(result, {
            atomCount: 3,
            frameCount: 2,
            firstAtomX: 0,
            events: [
                "structure_data_begin_ack",
                "structure_data_chunk_ack",
                "structure_data_chunk_ack",
                "structure_data_complete",
            ],
        });
        assert.deepEqual(errors, []);
        console.log("[E2E array-native] typed buffers created a 3-atom, 2-structure Mol* trajectory");
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
