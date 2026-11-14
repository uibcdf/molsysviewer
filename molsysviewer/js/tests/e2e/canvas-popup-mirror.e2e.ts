import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "./e2e-browser";
import { withFixtureWorkspace } from "./fixture-workspace";
import { checkCanvasPopupMirror } from "./canvas-popup-mirror-scenarios";

const dir = dirname(fileURLToPath(import.meta.url));

async function run() {
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage({ viewport: { width: 1100, height: 720 } });
        await checkCanvasPopupMirror(page, dir);
    } finally { await browser.close(); }
}

withFixtureWorkspace("canvas-popup-mirror", run).catch(error => { console.error(error); process.exit(1); });
