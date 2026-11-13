import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";
import { withFixtureWorkspace } from "./fixture-workspace";
import { checkStudioLiveCapture } from "./studio-live-capture-scenarios";

async function run() {
    const dir = dirname(fileURLToPath(import.meta.url));
    await withFixtureWorkspace("studio-live-capture", async workspace => {
        const browser = await chromium.launch();
        try {
            const page = await browser.newPage({ viewport: { width: 1200, height: 900 }, acceptDownloads: true });
            await checkStudioLiveCapture(page, dir, workspace);
        } finally { await browser.close(); }
    });
}
run().catch(error => { console.error(error); process.exit(1); });
