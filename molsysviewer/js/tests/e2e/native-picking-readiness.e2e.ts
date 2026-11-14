import assert from 'node:assert/strict';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from "./e2e-browser";
import { withFixtureWorkspace } from './fixture-workspace';
const dir = dirname(fileURLToPath(import.meta.url));
async function run() {
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage({ viewport: { width: 700, height: 550 } });
        await page.setContent('<!doctype html><body></body>');
        await page.addScriptTag({ path: resolve(dir, 'harness.bundle.js') });
        const result = await page.evaluate(() => (window as any).Harness.probeNativePickingReadiness());
        for (const observed of [result.primary, result.peer]) {
            assert.ok(observed.before);
            assert.deepEqual(observed.during, observed.before);
            assert.deepEqual(observed.resolved, observed.before);
            assert.deepEqual(observed.after, observed.before);
            assert.equal(observed.cameraUnchanged, true);
            assert.equal(observed.cameraTransition, false);
        }
        assert.deepEqual(result.witness, result.primary.before);
        assert.equal(result.witnessCameraUnchanged, true);
        console.log('[E2E native picking] pending/synchronous reads, unchanged cameras and independent-view disposal pass');
    } finally { await browser.close(); }
}
withFixtureWorkspace('native-picking-readiness', run).catch(error => { console.error(error); process.exit(1); });
