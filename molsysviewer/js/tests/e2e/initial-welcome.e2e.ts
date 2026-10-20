import assert from "node:assert/strict";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { Page } from "playwright";

import { chromium } from "./e2e-browser";
import { mountCanvasPopupFixture } from "./canvas-popup-fixture";
import { PythonFixtureBridge } from "./python-fixture-bridge";
import { fixtureEnvironment, withFixtureWorkspace } from "./fixture-workspace";

const dir = dirname(fileURLToPath(import.meta.url));

async function observeInitialRender(page: Page) {
    await page.evaluate(() => {
        const w = window as any;
        const selector = '[data-molsysviewer-welcome-card="true"]';
        w.__initialWelcomeInsertions = 0;
        const count = (records: MutationRecord[]) => {
            for (const record of records) for (const node of record.addedNodes) {
                if (!(node instanceof Element)) continue;
                if (node.matches(selector)) w.__initialWelcomeInsertions++;
                w.__initialWelcomeInsertions += node.querySelectorAll(selector).length;
            }
        };
        w.__initialWelcomeObserver = new MutationObserver(count);
        w.__initialWelcomeObserver.observe(document.getElementById("notebook"), { childList: true, subtree: true });
        w.__countPendingWelcomeRecords = () => count(w.__initialWelcomeObserver.takeRecords());

        // Observe the real factory result without substituting any Mol* or
        // scientific operation. The widget boot publishes its imported module
        // before invoking render(), so this also sees constructor-time inserts.
        let runtime: any;
        Object.defineProperty(w, "__molsysviewer_anywidget_runtime__", {
            configurable: true,
            get: () => runtime,
            set(value) {
                runtime = value;
                const C = value?.module?.MolSysViewerController;
                if (!C) return;
                const create = C.create;
                C.create = async function (...args: any[]) {
                    const controller = await create.apply(this, args);
                    w.__initialWelcomeController = controller;
                    controller.plugin.canvas3d.didDraw.subscribe(() => {
                        if (controller.getStructureData()?.elementCount > 0
                            && controller.plugin.canvas3d.reprCount.value > 0) {
                            w.__initialMolecularFrameDrawn = true;
                        }
                    });
                    return controller;
                };
            },
        });
    });
}

async function checkInitialView(page: Page, workspace: string, args: string[], expected: "molecular" | "empty" | "failed") {
    const bridge = new PythonFixtureBridge(resolve(dir, "initial_welcome_fixture.py"), resolve(dir, "../../../.."),
        90000, { args, env: fixtureEnvironment(workspace) });
    let release: (() => Promise<void>) | undefined;
    try {
        release = await mountCanvasPopupFixture(page, bridge, {
            trajectoryLabel: null,
            beforeRender: observeInitialRender,
        });
        await page.waitForFunction(() => !!(window as any).__initialWelcomeController);
        const welcome = page.locator('[data-molsysviewer-welcome-card="true"]');
        if (expected === "molecular") {
            await page.waitForFunction(() => (window as any).__initialMolecularFrameDrawn === true);
            const observed = await page.evaluate(() => {
                const w = window as any;
                w.__countPendingWelcomeRecords();
                return {
                    insertions: w.__initialWelcomeInsertions,
                    atoms: w.__initialWelcomeController.getStructureData().elementCount,
                    prepared: w.__popupWidgetModel.get("has_molecular_system"),
                    initialMessageCount: w.__popupWidgetModel.get("initial_messages").length,
                };
            });
            assert.equal(observed.prepared, true, "Python declares the initial molecular input");
            assert.equal(observed.initialMessageCount, 0, "the real ready handshake supplies molecular data later");
            assert.ok(observed.atoms > 3000, "the real TcTIM molecular system rendered");
            assert.equal(observed.insertions, 0, "Welcome never enters the DOM before the first molecular frame");
            assert.equal(await welcome.count(), 0);

            await page.evaluate(async () => {
                await (window as any).__initialWelcomeController.handleMessage({ op: "clear_all" }, { throwOnError: true });
            });
            assert.equal(await welcome.count(), 1, "explicit clear restores the empty-state entry card");
        } else {
            await welcome.waitFor({ state: "visible" });
            assert.equal(await welcome.count(), 1, `${expected} initial view offers Welcome`);
            assert.equal(await page.evaluate(() => !!(window as any).__initialWelcomeController.getStructureData()), false);
            if (expected === "failed") {
                assert.equal(await page.evaluate(() => (window as any).__popupWidgetModel.get("has_molecular_system")), true,
                    "failure cleanup is tested after a genuinely declared initial load");
            }
        }
        console.log(`[E2E initial Welcome] ${expected} ${args.join(" ") || "bundled TcTIM / binary"}: passed`);
    } finally {
        await page.evaluate(() => {
            (window as any).__initialWelcomeObserver?.disconnect();
            (window as any).__popupWidgetDispose?.();
        }).catch(() => {});
        await release?.();
        await bridge.close();
    }
}

async function run(workspace: string) {
    const browser = await chromium.launch();
    try {
        const page = await browser.newPage();
        const errors: string[] = [];
        page.on("pageerror", error => errors.push(String(error)));
        const molecularArgs = process.env.E2E_INITIAL_WELCOME_PDB_ID === "1" ? ["--pdb-id"] : [];
        await checkInitialView(page, workspace, molecularArgs, "molecular");
        await checkInitialView(page, workspace, [...molecularArgs, "--json"], "molecular");
        await checkInitialView(page, workspace, ["--invalid"], "failed");
        await checkInitialView(page, workspace, ["--empty"], "empty");
        assert.deepEqual(errors, []);
    } finally {
        await browser.close();
    }
}

withFixtureWorkspace("initial-welcome", run).catch(error => { console.error(error); process.exit(1); });
