import assert from "node:assert/strict";
import test from "node:test";
import { waitForImageAssets } from "../../src/plugin/image-assets";

function assetPass() {
    let area = false, search = false;
    const areaTexture = { getWidth: () => area ? 160 : 1, getHeight: () => area ? 560 : 1 };
    const searchTexture = { getWidth: () => search ? 66 : 1, getHeight: () => search ? 33 : 1 };
    const pass: any = { props: { postprocessing: { antialiasing: { name: "smaa" } } },
        drawPass: { antialiasing: { smaa: { supported: true, weightsRenderable: { values: {
            tArea: { ref: { value: areaTexture } }, tSearch: { ref: { value: searchTexture } },
        } } } } } };
    return { pass, loadedArea() { area = true; }, loaded() { area = search = true; } };
}

test("image readiness waits for the actual native texture dimensions without drawing", async () => {
    const f = assetPass(); let complete = false;
    const pending = waitForImageAssets(f.pass).then(() => { complete = true; });
    await Promise.resolve(); assert.equal(complete, false);
    f.loadedArea(); await new Promise(resolve => setTimeout(resolve, 20));
    assert.equal(complete, false, "one uploaded asset and a 1x1 placeholder are not readiness");
    f.loaded(); await pending; assert.equal(complete, true);
    await waitForImageAssets(f.pass);
});

test("image asset cancellation and controller retirement reject without waiting for the deadline", async () => {
    for (const index of [0, 1]) {
        const f = assetPass(), caller = new AbortController(), lifetime = new AbortController();
        const signals = [caller.signal, lifetime.signal];
        const pending = waitForImageAssets(f.pass, signals);
        const rejected = assert.rejects(pending, { name: "AbortError" });
        [caller, lifetime][index].abort(); await rejected;
        f.loaded(); await assert.rejects(waitForImageAssets(f.pass, signals), { name: "AbortError" });
    }
});

test("image readiness times out explicitly and refuses an unqualified private seam", async () => {
    const f = assetPass();
    await assert.rejects(waitForImageAssets(f.pass, [], 10), /PNG was not rendered/);
    delete f.pass.drawPass.antialiasing.smaa.weightsRenderable;
    await assert.rejects(waitForImageAssets(f.pass), /Unqualified native SMAA texture/);
    delete f.pass.drawPass.antialiasing.smaa;
    await assert.rejects(waitForImageAssets(f.pass), /Unqualified native SMAA image-asset/);
});

test("other native antialiasing modes and unsupported SMAA do not wait or change settings", async () => {
    const f = assetPass(); f.pass.props.postprocessing.antialiasing.name = "fxaa";
    await waitForImageAssets(f.pass); assert.equal(f.pass.props.postprocessing.antialiasing.name, "fxaa");
    f.pass.props.postprocessing.antialiasing.name = "smaa";
    f.pass.drawPass.antialiasing.smaa.supported = false; await waitForImageAssets(f.pass);
    assert.equal(f.pass.drawPass.antialiasing.smaa.supported, false);
});
