import assert from "node:assert";
import test from "node:test";
import { MolSysViewerController } from "../src/managers/viewer-controller";

function makeBuilder() {
    const updates: Array<{ ref: any; next: any }> = [];
    return {
        updates,
        to(ref: any) {
            return {
                update(fn: (old: any) => any) {
                    const next = fn({ state: {} });
                    updates.push({ ref, next });
                    return this;
                },
            };
        },
        commit: async () => ({}),
    };
}

// Minimal plugin mock that satisfies the parts touched by handleShowHideRegion.
function makePluginMock() {
    const builder = makeBuilder();
    return {
        state: {
            data: {
                build: () => builder,
            },
        },
        __builder: builder,
    };
}

// Forcing access despite private constructor; runtime allows it.
function makeController() {
    const plugin: any = makePluginMock();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const controller: any = new (MolSysViewerController as any)(plugin, {} as any, undefined);
    return { controller, plugin };
}

test("hide_region updates isHidden via state update", async () => {
    const { controller, plugin } = makeController();
    const tag = "region1";
    const reprRef = "repr1";
    controller.regionIndex.set(tag, {
        component: undefined,
        representations: [reprRef],
        atomIndices: [],
    });

    await controller.handleShowHideRegion({ tag } as any, true);

    const updates = plugin.__builder.updates ?? [];
    const hasHideUpdate = updates.some((u: any) => u.ref === reprRef && u.next?.state?.isHidden === true);
    assert.ok(hasHideUpdate, "Expected hide to set isHidden=true on representation");
});
