"""Reviewed legacy migration on real scenes and exact rounded-step boundaries."""

import json
import math
import os
import subprocess
from copy import deepcopy
from pathlib import Path

import molsysmt as msm
import pytest
from molsysviewer.viewer._movie_legacy import _rounded_structure, compile_legacy
from molsysviewer.viewer._movie_timeline import _MovieTimeline

import molsysviewer as msv

BEGIN = {"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]}
END = {"position": [30, 0, 0], "target": [0, 0, 0], "up": [0, 1, 0]}


@pytest.fixture
def view():
    with msv.new_view(msm.systems["pentalanine"]["traj_pentalanine.h5msm"], structure_indices=[4999, 0, 73]) as value:
        value.regions.add(tag="site", atom_indices=[0, 1], representation="ball-and-stick")
        value.shapes.add_sphere(center="[0, 0, 0] angstrom", radius="1 angstrom", tag="site")
        value.movie.set_baseline(1000, camera=BEGIN)
        yield value


def recipe(easing="linear", reverse=False, start=0, end=1000):
    return deepcopy(
        {
            "molsysmovie_version": 1,
            "keyframes": [
                {"time_ms": start, "camera": BEGIN, "structure_index": 2 if reverse else 0, "easing": easing},
                {"time_ms": end, "camera": END, "structure_index": 0 if reverse else 2},
            ],
        }
    )


@pytest.mark.parametrize("easing", ["linear", "ease-in", "ease-out", "ease-in-out"])
@pytest.mark.parametrize("reverse", [False, True])
def test_rounded_sweeps_include_intermediate_frames_and_exact_float_boundaries(view, easing, reverse):
    source = recipe(easing, reverse, start=100)
    scene, original = view.export_state(), view.movie.to_dict()
    report = view.movie.review_import(source)
    assert report["can_apply"] and not report["conflicts"]
    assert view.export_state() == scene and view.movie.to_dict() == original
    candidate = report["candidate"]
    assert candidate["camera_interpolation"] == "cartesian-constant-up@1"
    events = next(t["keys"] for t in candidate["tracks"] if t["property"] == "index")
    assert [e["value"] for e in events] == ([2, 1, 0] if reverse else [0, 1, 2])
    assert events[0]["time_ms"] == 0
    view.movie.apply_import(report)
    times = [0, 99, 100, 1000, *range(101, 1000, 7)]
    for key in events[1:]:
        at = key["time_ms"]
        times += [math.nextafter(at, 0), at, math.nextafter(at, math.inf)]
    # This Python control is complemented by the actual legacy renderer in
    # movie-handler.test.ts, consuming the shared public-migration fixture.
    left = {**source["keyframes"][0], "easing": easing}
    for at in reversed(times):
        assert view.movie.evaluate(at)["structure_index"] == _rounded_structure(at, left, source["keyframes"][1])
    assert view.movie.evaluate(0)["camera"] == BEGIN
    source["keyframes"][0]["camera"]["position"][0] = -20
    report["candidate"]["tracks"].clear()
    assert view.movie.evaluate(0)["camera"] == BEGIN


def test_all_intermediate_structures_need_unique_nonconsecutive_correspondence(view):
    source = recipe()
    report = view.movie.review_import(source, structure_index_map=[2, 0, 1])
    assert report["can_apply"]
    view.movie.apply_import(report)
    assert [view.movie.evaluate(t)["structure_index"] for t in [0, 250, 500, 750, 1000]] == [1, 2, 2, 0, 0]
    for mapping, reason in [([0, None, 2], "unmapped_structure"), ([0, 1, 1], "ambiguous_structure")]:
        report = view.movie.review_import(source, structure_index_map=mapping)
        assert not report["can_apply"] and any(c["reason"] == reason for c in report["conflicts"])
    assert any(
        c.get("source_indices") == [1]
        for c in view.movie.review_import(source, structure_index_map=[0, None, 2])["conflicts"]
    )


def test_untyped_visibility_requires_a_declared_domain_and_retains_destination_initial_state(view):
    source = {
        "molsysmovie_version": 1,
        "keyframes": [{"time_ms": 0}, {"time_ms": 500, "layer_visibility": {"site": False}}],
    }
    report = view.movie.review_import(source, camera=BEGIN)
    assert not report["can_apply"] and report["conflicts"][0]["reason"] == "legacy_target_map_required"
    mapping = [{"source": {"domain": "legacy", "tag": "site"}, "target": {"domain": "region", "tag": "site"}}]
    report = view.movie.review_import(source, camera=BEGIN, target_map=mapping)
    assert report["can_apply"] and report["affected_tracks"] == ["legacy-visible-0"]
    assert "legacy_initial_visibility_from_destination" in report["warnings"]
    assert report["targets"][0]["source_identity"] == {}
    view.movie.apply_import(report)
    for at, expected in ((499, True), (500, False)):
        visibility = {(row["domain"], row["tag"]): row["visible"] for row in view.movie.evaluate(at)["visibility"]}
        assert visibility["region", "site"] is expected
        assert visibility["shape", "site"] is True


@pytest.mark.parametrize(
    "defect,reason",
    [
        ("partial-camera", "legacy_partial_camera_channel"),
        ("partial-structure", "legacy_partial_structure_channel"),
        ("varying-up", "incompatible_legacy_scene_or_path"),
        ("singular-path", "incompatible_legacy_scene_or_path"),
        ("camera-override", "legacy_camera_override_changes_path"),
        ("one-key", "legacy_requires_multiple_keyframes"),
        ("event-budget", "legacy_structure_event_limit"),
    ],
)
def test_unsupported_profiles_are_named_conflicts_without_mutating_the_scene_or_plan(view, defect, reason):
    source, options = recipe(), {}
    if defect == "partial-camera":
        source["keyframes"][1].pop("camera")
    elif defect == "partial-structure":
        source["keyframes"][1].pop("structure_index")
    elif defect == "varying-up":
        source["keyframes"][1]["camera"] = {**END, "up": [0, 0, 1]}
    elif defect == "singular-path":
        source["keyframes"][1]["camera"] = {**END, "position": [0, 0, -30]}
    elif defect == "camera-override":
        options["camera"] = END
    elif defect == "one-key":
        source["keyframes"].pop()
    elif defect == "event-budget":
        source["keyframes"][1]["structure_index"] = 100_000
    before, scene = view.movie.to_dict(), view.export_state()
    report = view.movie.review_import(source, **options)
    assert not report["can_apply"] and report["candidate"] is None
    assert reason in {c["reason"] for c in report["conflicts"]}
    with pytest.raises(ValueError, match="has conflicts"):
        view.movie.apply_import(report)
    assert view.movie.to_dict() == before and view.export_state() == scene


@pytest.mark.parametrize("edit", ["scene", "plan", "review", "source"])
def test_review_is_detached_and_uses_the_existing_stale_ticket_boundary(view, edit):
    source = recipe()
    review = view.movie.review_import(source)
    before = view.movie.to_dict()
    if edit == "scene":
        view.regions["site"].hide()
    elif edit == "plan":
        view.movie.set_duration(1500)
        before = view.movie.to_dict()
    elif edit == "review":
        review["candidate"]["duration_ms"] += 1
    else:
        source["keyframes"].clear()
        view.movie.apply_import(review)
        assert view.movie.evaluate(500)["structure_index"] == 1
        return
    with pytest.raises(ValueError, match="stale|expired"):
        view.movie.apply_import(review)
    assert view.movie.to_dict() == before


def test_legacy_provenance_and_compiled_steps_survive_session_and_subsequent_v2_import(view, tmp_path):
    view.movie.apply_import(view.movie.review_import(recipe(), structure_index_map=[2, 0, 1]))
    accepted = view.movie.to_dict()
    receipt = accepted["provenance"]
    assert receipt["schema"] == "molsysviewer.movie_import@2" and receipt["source_binding"] is None
    assert receipt["source_version"] == 1
    path = tmp_path / "legacy.msv"
    view.save_session(path)
    with msv.load_session(path) as restored:
        assert restored.movie.to_dict() == accepted
        assert restored.movie.evaluate(500) == view.movie.evaluate(500)
        restored.movie.validate()
        assert "provenance" not in restored.movie._timeline.preview_recipe()
        report = restored.movie.review_import(accepted)
        assert report["can_apply"] and report["candidate"]["provenance"]["source_version"] == 2
        assert report["candidate"]["tracks"] == accepted["tracks"]
        assert "source" not in report["candidate"]["provenance"]


@pytest.mark.parametrize("field,value", [("source_version", 2), ("source_binding", {}), ("source_version", True)])
def test_legacy_receipt_cannot_invent_origin_or_version(view, field, value):
    candidate = view.movie.review_import(recipe())["candidate"]
    candidate["provenance"][field] = value
    with pytest.raises(ValueError):
        _MovieTimeline(candidate)


def test_short_time_domain_coalesces_unrepresentable_events():
    source = recipe(end=math.ulp(0.0))
    compiled = compile_legacy(source, None)
    events = next(t["keys"] for t in compiled["tracks"] if t["property"] == "index")
    assert events == [{"time_ms": 0.0, "value": 0}, {"time_ms": math.ulp(0.0), "value": 2}]


def test_large_declared_source_indices_are_not_rounded_by_adding_half(view):
    source = recipe()
    a, b = 2**53 - 2, 2**53 - 1
    source["keyframes"][0]["structure_index"] = a
    source["keyframes"][1]["structure_index"] = b
    review = view.movie.review_import(source, structure_index_map=[a, None, b])
    assert review["can_apply"]
    view.movie.apply_import(review)
    # At the final binary64 integer, floor(value + .5) can yield 2**53,
    # which was never a source index. The compiled final event must remain b.
    assert view.movie.evaluate(1000)["structure_index"] == 2
    events = next(track["keys"] for track in review["candidate"]["tracks"] if track["property"] == "index")
    assert events[0]["value"] == 0 and events[-1]["value"] == 2


def test_legacy_prototype_tag_cannot_gain_a_new_visibility_effect(view):
    view.regions.add(tag="__proto__", atom_indices=[3, 4])
    source = recipe()
    source["keyframes"][0]["layer_visibility"] = {"__proto__": False}
    mapping = [{"source": {"domain": "legacy", "tag": "__proto__"}, "target": {"domain": "region", "tag": "__proto__"}}]
    report = view.movie.review_import(source, target_map=mapping)
    assert not report["can_apply"] and report["candidate"] is None
    assert {"reason": "legacy_unsupported_visibility_tag", "tag": "__proto__"} in report["conflicts"]


@pytest.mark.parametrize(
    "defect", ["boolean-time", "boolean-index", "nan", "unordered", "invalid-visibility", "unknown-field"]
)
def test_malformed_legacy_data_does_not_replace_a_valid_review(view, defect):
    valid = view.movie.review_import(recipe())
    source = recipe()
    if defect == "boolean-time":
        source["keyframes"][0]["time_ms"] = False
    elif defect == "boolean-index":
        source["keyframes"][0]["structure_index"] = True
    elif defect == "nan":
        source["keyframes"][1]["time_ms"] = math.nan
    elif defect == "unordered":
        source["keyframes"].reverse()
    elif defect == "invalid-visibility":
        source["keyframes"][0]["layer_visibility"] = {"site": 1}
    else:
        source["extra"] = True
    with pytest.raises(ValueError):
        view.movie.review_import(source)
    view.movie.apply_import(valid)
    assert view.movie.evaluate(500)["structure_index"] == 1


def test_legacy_maps_are_typed_explicit_and_one_to_one(view):
    source = recipe()
    source["keyframes"][0]["layer_visibility"] = {"site": False}
    source_ref = {"domain": "legacy", "tag": "site"}
    target_ref = {"domain": "region", "tag": "site"}
    mapping = [{"source": source_ref, "target": target_ref}]
    for invalid in [
        mapping * 2,
        [{"source": target_ref, "target": target_ref}],
        mapping + [{"source": {"domain": "legacy", "tag": "unused"}, "target": {"domain": "shape", "tag": "site"}}],
    ]:
        with pytest.raises(ValueError):
            view.movie.review_import(source, target_map=invalid)
    missing = [{"source": source_ref, "target": {"domain": "region", "tag": "missing"}}]
    report = view.movie.review_import(source, target_map=missing)
    assert not report["can_apply"] and report["conflicts"][0]["reason"] == "target_missing"
    candidate = view.movie.review_import(source, target_map=mapping)["candidate"]
    for mutate in [
        lambda p: p["targets"][0]["source_identity"].update(uid="invented"),
        lambda p: p["target_map"].clear(),
    ]:
        changed = deepcopy(candidate)
        mutate(changed["provenance"])
        with pytest.raises(ValueError):
            _MovieTimeline(changed)


def test_shared_renderer_fixture_is_the_public_migration_result(view):
    path = Path(__file__).parents[1] / "molsysviewer/js/tests/fixtures/movie-legacy-oracle.json"
    fixture = json.loads(path.read_text())
    for case in fixture:
        report = view.movie.review_import(case["legacy"])
        assert report["can_apply"]
        # Scientific binding/scene are deliberately not synthesized as legacy
        # source identity. Only the independently comparable channels are kept.
        assert report["candidate"]["tracks"] == case["tracks"]
        assert report["candidate"]["camera_interpolation"] == case["camera_interpolation"]


def test_documented_legacy_review_runs_headlessly():
    page = Path(__file__).parents[1] / "docs/content/user/movie/timeline.md"
    section = page.read_text().split("### Reviewing a legacy recipe", 1)[1]
    example = section.split("```python\n", 1)[1].split("```", 1)[0]
    exec(compile(example, str(page), "exec"), {"__name__": "movie_legacy_documentation"})


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_MOVIE_BROWSER_TEST") != "1",
    reason="Explicit real Mol*/Chromium legacy migration receiving is required.",
)
def test_native_reviewed_legacy_movie():
    """Receive migration separately; movie-seek's existing timeout stays visible."""
    js = Path(__file__).parents[1] / "molsysviewer/js"
    subprocess.run(["node", "tests/e2e/movie-legacy.e2e.js"], cwd=js, check=True, timeout=180)
