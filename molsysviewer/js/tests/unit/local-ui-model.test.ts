import assert from "node:assert/strict";
import test from "node:test";
import { createLocalUiModel } from "../../src/ui/local-ui-model";

test("historical projections restore modern controls without changing panel layout", () => {
    for (const [viewer, controls] of [["integrated", "minimal"], ["classic", "classic"], ["standard", "compact"]]) {
        const model = createLocalUiModel({ viewer_mode: viewer, controls_mode: controls, panel_mode_style: "integrated" });
        assert.equal(model.get("viewer_mode"), "standard");
        assert.equal(model.get("controls_mode"), "compact");
        assert.equal(model.get("panel_mode_style"), "integrated");
    }
});

test("saved popup preferences use canonical modes and retain Cinema", () => {
    let saved: Record<string, unknown> | undefined;
    const model = createLocalUiModel({}, values => { saved = values; });
    model.set("viewer_mode", "cinema");
    model.set("controls_mode", "cinema");
    model.save_changes();
    assert.equal(saved?.viewer_mode, "cinema");
    assert.equal(saved?.controls_mode, "cinema");
    model.set("viewer_mode", "integrated");
    model.set("controls_mode", "minimal");
    model.save_changes();
    assert.equal(saved?.viewer_mode, "standard");
    assert.equal(saved?.controls_mode, "compact");
    assert.equal(saved?.panel_mode_style, "integrated");
});
