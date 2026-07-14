import process from "node:process";
import { chromium } from "./e2e-browser";

async function run(): Promise<void> {
    const browser = await chromium.launch({ headless: true });
    try {
        await browser.newPage();
    } finally {
        await browser.close();
    }
    console.log("[E2E environment] Chromium and WebGL2 are available");
}

run().catch(error => {
    console.error(error);
    process.exit(1);
});
