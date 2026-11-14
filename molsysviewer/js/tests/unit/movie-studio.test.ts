import assert from "node:assert/strict";
import test from "node:test";
import { ownMovieIntent } from "../../src/messages/movie-studio-intent";
import { PopupReplayLog } from "../../src/messages/popup-replay-log";
import { MoviePanel, type MoviePanelState } from "../../src/ui/panels/movie-panel";
import type { PanelContext } from "../../src/ui/panels/types";

const state: MoviePanelState = { op: "set_movie_state", revision: 1, version: 2, duration_ms: 500,
    n_tracks: 1, system_loaded: true, live_available: true, busy: null, job_id: null };

function editor(onAction: (...args: any[]) => void = () => {}) {
    return new MoviePanel({ onAction, setBadge: () => {} } as unknown as PanelContext) as any;
}

test("Movie intentions belong to the authenticated panel and its actual canvas", () => {
    const draft = { event: "interaction_context_action", action: "movie_start", request_id: "new-plan",
        _studio_owner_endpoint_id: "forged-owner", _capture_endpoint_id: "forged-canvas", duration_ms: 1000 };
    assert.deepEqual(ownMovieIntent(draft, "panel-real", "canvas-real"), {
        ...draft, _studio_owner_endpoint_id: "panel-real", _capture_endpoint_id: "canvas-real",
    });
    assert.equal(draft._capture_endpoint_id, "forged-canvas", "connector ownership must not mutate the caller draft");
    const ordinary = { event: "visual_state_snapshot", _capture_endpoint_id: "actual-receiver" };
    assert.equal(ownMovieIntent(ordinary, "owner", "canvas"), ordinary);
});

test("Movie editor pages and request identifiers are not replayed into later popup owners", () => {
    const log = new PopupReplayLog();
    log.record({ op: "set_movie_state", request_id: "old-owner", editor: { tracks: [] } } as any);
    assert.deepEqual(log.snapshot("canvas"), []);
    assert.deepEqual(log.snapshot("panel"), []);
});

test("Movie transport rejection releases controls without discarding the form draft", () => {
    const panel = editor(() => { throw new Error("Session disconnected"); });
    panel.setState(state); panel.tag = "draft camera";
    panel.submit("movie_set_key");
    assert.equal(panel.pending, null); assert.equal(panel.tag, "draft camera");
    assert.equal(panel.message, "Session disconnected");
});

test("Unrelated action replies preserve unsaved duration and removed-track drafts", () => {
    const panel = editor(); panel.setState(state);
    panel.duration = "8"; panel.durationTouched = true;
    panel.submit("movie_seek");
    panel.updateStudioAction({ request_id: panel.pending, domain: "movie", ok: true });
    panel.setState({ ...state, revision: 2 });
    assert.equal(panel.duration, "8"); assert.equal(panel.durationTouched, true);
    panel.selected = "removed"; panel.tag = "kept draft"; panel.request = "fresh-page";
    panel.setState({ ...state, revision: 2, request_id: "fresh-page", editor: { offset: 0, tracks: [], track: null } });
    assert.equal(panel.selected, ""); assert.equal(panel.tag, "kept draft");
    panel.submit("movie_set_duration");
    panel.updateStudioAction({ request_id: panel.pending, domain: "movie", ok: true });
    panel.setState({ ...state, revision: 3, duration_ms: 8000 });
    assert.equal(panel.durationTouched, false); assert.equal(panel.duration, "8");
});

test("An external Python edit requires review before applying a kept Movie draft", () => {
    const panel = editor(); panel.setState(state);
    panel.markDraft(); panel.tag = "old-scene draft"; panel.replace = true;
    panel.setState({ ...state, revision: 2 });
    assert.equal(panel.editable, false); assert.equal(panel.staleDraft, true);
    panel.submit("movie_seek");
    panel.updateStudioAction({ request_id: panel.pending, domain: "movie", ok: true });
    assert.equal(panel.staleDraft, true); assert.equal(panel.replace, true);
    panel.useKeptDraft();
    assert.equal(panel.editable, true); assert.equal(panel.tag, "old-scene draft");
});

test("Choosing a discrete Movie property resets continuous easing to its admitted hold semantics", () => {
    const panel = editor(); panel.easing = "ease-in"; panel.property = "visible";
    panel.defaultValue(); assert.equal(panel.easing, "linear");
});

test("Codec intentions require the Python owner's capability and retain an explicit draft", () => {
    const panel = editor(); panel.setState(state); panel.codec = "av1";
    assert.equal("codec" in panel.exportOptions(), false, "An older owner must not silently ignore a new choice");
    panel.setState({ ...state, codec_selection: 1 });
    assert.equal(panel.exportOptions().codec, "av1");
    panel.setState({ ...state, codec_selection: 2 });
    assert.equal("codec" in panel.exportOptions(), false, "Unknown policy versions are not declared compatible");
    assert.equal(panel.codec, "av1", "The form draft survives unrelated summaries");
});
