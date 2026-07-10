import assert from "node:assert";
import test from "node:test";

import { MolSysViewerController } from "../../src/managers/viewer-controller";

test("viewer controller does not rebuild System chrome for non-invalidating messages", async () => {
    const controller = Object.create(MolSysViewerController.prototype) as MolSysViewerController & {
        state: { hideRegion(message: unknown): Promise<void> };
        syncStripOverlaysForMessage(message: unknown): void;
        refreshPanelWorkspaceChrome(): void;
    };
    let chromeRefreshes = 0;
    let stripSyncs = 0;

    controller.state = {
        async hideRegion(_message: unknown) {},
    };
    controller.syncStripOverlaysForMessage = (_message: unknown) => {
        stripSyncs += 1;
    };
    controller.refreshPanelWorkspaceChrome = () => {
        chromeRefreshes += 1;
    };

    const originalWarn = console.warn;
    console.warn = () => {};
    try {
        await controller.handleMessage({ op: "__does_not_exist__" } as never);
        await controller.handleMessage({ op: "hide_region", tag: "site" });
    } finally {
        console.warn = originalWarn;
    }

    assert.strictEqual(chromeRefreshes, 0);
    assert.strictEqual(stripSyncs, 2);
});
