"""Declared Movie correspondences on real scene and scientific owners."""

import json
import runpy
from copy import deepcopy
from pathlib import Path

import pytest
from molsysviewer.interactions import _analysis_signature
from molsysviewer.viewer._movie_timeline import _MovieTimeline
from molsysviewer.viewer.frontend_requests import FrontendRequestError

import molsysviewer as msv

make_appearance_view = runpy.run_path(str(Path(__file__).with_name("test_movie_appearance.py")))["make_appearance_view"]


@pytest.fixture
def authored():
    with make_appearance_view() as view:
        yield view


def maps_for(recipe):
    references = {
        (track["target"]["domain"], track["target"]["tag"]) for track in recipe["tracks"] if "tag" in track["target"]
    }
    return [{"source": {"domain": d, "tag": t}, "target": {"domain": d, "tag": t}} for d, t in sorted(references)]


def test_import_preserves_keys_scene_science_and_compact_receipt(authored):
    recipe = authored.movie.to_dict()
    authored.annotations.add("Later", atom_indices=[1], tag="later")
    scene = authored.export_state()
    scientific = _analysis_signature(authored.interactions.get_analysis("story-hbonds"))
    review = authored.movie.review_import(recipe)
    assert review["can_apply"] and not review["conflicts"]
    assert review["candidate"]["tracks"] == recipe["tracks"]
    assert authored.movie.to_dict() == recipe and authored.export_state() == scene
    authored.movie.apply_import(json.loads(json.dumps(review)))
    accepted = authored.movie.to_dict()
    assert accepted["tracks"] == recipe["tracks"]
    assert (
        authored.export_state() == scene
        and _analysis_signature(authored.interactions.get_analysis("story-hbonds")) == scientific
    )
    assert accepted["provenance"]["source_sha256"] == review["source_sha256"]
    assert accepted["provenance"]["targets"] == review["targets"]
    assert "provenance" not in authored.movie._timeline.preview_recipe()
    authored.movie.validate()
    second = authored.movie.review_import(accepted)
    assert "source" not in second["candidate"]["provenance"]
    assert len(json.dumps(second["candidate"]["provenance"])) < 5000
    authored.movie.apply_import(second)
    review["candidate"]["tracks"].clear()
    assert authored.movie.to_dict()["tracks"] == recipe["tracks"]


def test_explicit_region_substitution_does_not_remap_same_named_shape(authored):
    recipe = authored.movie.to_dict()
    authored.regions["site"].delete()
    authored.regions.add(tag="pocket", atom_indices=[4, 5], representation="ball-and-stick", alpha=0.6)
    mapping = [{"source": {"domain": "region", "tag": "site"}, "target": {"domain": "region", "tag": "pocket"}}]
    review = authored.movie.review_import(recipe, target_map=mapping)
    assert review["can_apply"] and "target_identity_rebound" in review["warnings"]
    assert "site-alpha" in review["affected_tracks"]
    authored.movie.apply_import(review)
    targets = {track["tag"]: track["target"] for track in authored.movie.to_dict()["tracks"]}
    assert targets["sphere-alpha"] == {"domain": "shape", "tag": "site"}
    assert targets["site-alpha"] == {"domain": "region", "tag": "pocket"}
    assert authored.regions["pocket"].atom_indices == (4, 5)
    authored.movie.validate()


def test_same_name_replacement_requires_explicit_consent(authored):
    recipe = authored.movie.to_dict()
    authored.regions["site"].delete()
    authored.regions.add(tag="site", atom_indices=[4, 5], representation="ball-and-stick")
    before = authored.movie.to_dict()
    review = authored.movie.review_import(recipe)
    assert not review["can_apply"] and any(row["reason"] == "target_replaced" for row in review["conflicts"])
    with pytest.raises(ValueError, match="has conflicts"):
        authored.movie.apply_import(review)
    assert authored.movie.to_dict() == before
    mapping = [{"source": {"domain": "region", "tag": "site"}, "target": {"domain": "region", "tag": "site"}}]
    assert authored.movie.review_import(recipe, target_map=mapping)["can_apply"]


def test_scientific_rebinding_reports_both_associations_without_editing_analysis(authored):
    recipe = authored.movie.to_dict()
    authored.interactions.hbonds.get_buch_hbonds(
        name="alternative", structure_indices="all", distance_threshold="0.3 nm"
    )
    authored.interactions["contacts"].delete()
    authored.interactions.add("alternative", tag="replacement")
    signature = _analysis_signature(authored.interactions.get_analysis("alternative"))
    mapping = [
        {
            "source": {"domain": "interaction", "tag": "contacts"},
            "target": {"domain": "interaction", "tag": "replacement"},
        }
    ]
    review = authored.movie.review_import(recipe, target_map=mapping)
    assert review["can_apply"] and "scientific_target_rebound" in review["warnings"]
    association = next(row for row in review["targets"] if row["track"] == "interaction-colour")
    assert association["source_identity"]["analysis_name"] == "story-hbonds"
    assert association["target_identity"]["analysis_name"] == "alternative"
    authored.movie.apply_import(review)
    assert _analysis_signature(authored.interactions.get_analysis("alternative")) == signature


def test_new_binding_requires_declared_targets_and_new_to_old_frame_map(authored):
    recipe = authored.movie.to_dict()
    with authored.extract(structure_indices=[2, 0, 1]) as target:
        scene = target.export_state()
        report = target.movie.review_import(recipe)
        assert not report["can_apply"]
        assert {row["reason"] for row in report["conflicts"]} >= {"structure_map_required", "target_map_required"}
        report = target.movie.review_import(recipe, target_map=maps_for(recipe), structure_index_map=[2, 0, 1])
        assert report["can_apply"]
        assert "molecular_binding_rebound" in report["warnings"]
        assert "camera_world_coordinates_unchanged" in report["warnings"]
        target.movie.apply_import(report)
        assert target.movie.evaluate(0)["structure_index"] == 1
        assert target.movie.evaluate(500)["structure_index"] == 0
        assert target.export_state() == scene
        target.movie.validate()
        for a, b in zip(recipe["tracks"], target.movie.to_dict()["tracks"], strict=True):
            if a["target"]["domain"] != "structure":
                assert a == b


@pytest.mark.parametrize(
    "indices,reason", [([0, None, None], "unmapped_structure"), ([0, 2, 2], "ambiguous_structure")]
)
def test_missing_or_ambiguous_referenced_frames_are_conflicts(authored, indices, reason):
    before = authored.movie.to_dict()
    report = authored.movie.review_import(before, structure_index_map=indices)
    assert not report["can_apply"] and report["candidate"] is None
    assert any(row["reason"] == reason and row["source_indices"] == [2] for row in report["conflicts"])
    assert authored.movie.to_dict() == before


@pytest.mark.parametrize(
    "edit", ["source", "options", "candidate", "bool", "scene", "recipe", "foreign", "superseded", "clear", "legacy"]
)
def test_stale_edited_foreign_and_expired_tickets_preserve_work(authored, edit):
    recipe = authored.movie.to_dict()
    report = authored.movie.review_import(recipe)
    if edit == "source":
        report["source"]["tracks"].clear()
    elif edit == "options":
        report["options"]["camera"] = recipe["baseline"]["camera"]
    elif edit == "candidate":
        report["candidate"]["tracks"].clear()
    elif edit == "bool":
        report["can_apply"] = 1
    elif edit == "scene":
        authored.annotations.add("New work", atom_indices=[0], tag="new")
    elif edit == "recipe":
        authored.movie.set_duration(2000)
    elif edit == "foreign":
        with make_appearance_view() as other:
            report = other.movie.review_import(recipe)
    elif edit == "superseded":
        authored.movie.review_import(recipe)
    elif edit == "clear":
        authored.movie.clear()
    else:
        authored.movie.from_dict({"molsysmovie_version": 1, "keyframes": []})
    expected, scene = authored.movie.to_dict(), authored.export_state()
    with pytest.raises(ValueError, match="stale or edited|expired"):
        authored.movie.apply_import(report)
    assert authored.movie.to_dict() == expected and authored.export_state() == scene


def test_failed_review_preserves_previous_ticket_and_detaches_original_input(authored):
    recipe = authored.movie.to_dict()
    report = authored.movie.review_import(recipe)
    bad = deepcopy(recipe)
    bad["tracks"][0]["keys"][0]["value"] = float("nan")
    with pytest.raises(ValueError):
        authored.movie.review_import(bad)
    recipe["tracks"].clear()
    authored.movie.apply_import(report)
    assert authored.movie.to_dict()["tracks"]


@pytest.mark.parametrize("field", ["_seek_request", "_playback", "_export_job"])
def test_active_movie_operations_refuse_review_and_acceptance(authored, field):
    before = authored.movie.to_dict()
    report = authored.movie.review_import(before)
    setattr(authored.movie, field, object())
    try:
        for action in [lambda: authored.movie.review_import(before), lambda: authored.movie.apply_import(report)]:
            with pytest.raises(FrontendRequestError, match="movie_operation_pending"):
                action()
    finally:
        setattr(authored.movie, field, None)
    assert authored.movie.to_dict() == before
    authored.movie.apply_import(report)


@pytest.mark.parametrize(
    "mapping",
    [
        [{"source": {"domain": "region", "tag": "site"}, "target": {"domain": "shape", "tag": "site"}}],
        [{"source": {"domain": "region", "tag": "site"}, "target": {"domain": "region", "tag": "site"}}] * 2,
        [{"source": {"domain": "region", "tag": "unused"}, "target": {"domain": "region", "tag": "site"}}],
        {"site": "pocket"},
    ],
)
def test_invalid_or_unused_maps_are_rejected_atomically(authored, mapping):
    before = authored.movie.to_dict()
    with pytest.raises(ValueError):
        authored.movie.review_import(before, target_map=mapping)
    assert authored.movie.to_dict() == before


@pytest.mark.parametrize("indices", [[0], [0, 1, 3], [0, True, 2], [0, 1, 1.5]])
def test_invalid_structure_maps_are_rejected_with_or_without_digest(authored, indices):
    before = authored.movie.to_dict()
    for skip in [False, True]:
        with pytest.raises(ValueError):
            authored.movie.review_import(before, structure_index_map=indices, skip_digestion=skip)
    assert authored.movie.to_dict() == before


def test_explicit_baseline_camera_keeps_authored_camera_keys(authored):
    camera = {"position": [0, 0, 20], "target": [0, 0, 0], "up": [0, 1, 0]}
    authored.movie.add_track(
        {
            "tag": "camera",
            "target": {"domain": "camera"},
            "property": "pose",
            "keys": [{"time_ms": 1000, "value": camera}],
        }
    )
    recipe = authored.movie.to_dict()
    new = {**camera, "position": [0, 0, 40]}
    report = authored.movie.review_import(recipe, camera=new)
    assert report["can_apply"] and "camera" in report["affected_tracks"]
    assert report["candidate"]["tracks"] == recipe["tracks"]
    assert report["candidate"]["baseline"]["camera"] == new
    assert any(row["domain"] == "camera" and row["after"] == new for row in report["changes"])
    authored.movie.apply_import(report)
    assert authored.movie.evaluate(0)["camera"] == new


def test_import_receipt_survives_edits_rebase_and_session_without_aliases(authored, tmp_path):
    authored.movie.apply_import(authored.movie.review_import(authored.movie.to_dict()))
    provenance = authored.movie.to_dict()["provenance"]
    authored.movie.set_duration(2000)
    authored.movie.rebase(authored.movie.review_rebase())
    assert authored.movie.to_dict()["provenance"] == provenance
    path = tmp_path / "movie-import.msv"
    authored.save_session(path)
    with msv.load_session(path) as restored:
        assert restored.movie.to_dict() == authored.movie.to_dict()
        assert restored.movie.evaluate(500) == authored.movie.evaluate(500)
        restored.movie.validate()
        restored.movie.to_dict()["provenance"]["targets"].clear()
        assert restored.movie.to_dict()["provenance"] == provenance


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_sha256", "bad"),
        ("source_version", True),
        ("target_map", {}),
        ("structure_index_map", [0]),
        ("warnings", [True]),
        ("targets", [{"op": "bad"}]),
    ],
)
def test_invalid_persisted_provenance_is_rejected(authored, field, value):
    candidate = authored.movie.review_import(authored.movie.to_dict())["candidate"]
    candidate["provenance"][field] = value
    with pytest.raises(ValueError):
        _MovieTimeline(candidate)


def test_legacy_reader_is_retained_without_claiming_a_lossy_conversion(authored):
    before = authored.movie.to_dict()
    legacy = {"molsysmovie_version": 1, "keyframes": [{"time_ms": 0}, {"time_ms": 1000}]}
    with pytest.raises(ValueError, match="version-2 recipe"):
        authored.movie.review_import(legacy)
    assert authored.movie.to_dict() == before
    authored.movie.from_dict(legacy)
    assert authored.movie.to_dict() == legacy


@pytest.mark.parametrize("change", ["missing", "shape-kind", "colour-layer"])
def test_missing_or_incompatible_targets_are_not_silently_dropped(authored, change):
    recipe = authored.movie.to_dict()
    if change == "missing":
        authored.shapes["site"].delete()
    elif change == "shape-kind":
        authored.shapes["site"].delete()
        authored.shapes.links.add_links(atom_pairs=[[0, 1]], tag="site")
    else:
        authored.whole.set_color("#ff0000")
    scene = authored.export_state()
    review = authored.movie.review_import(recipe, target_map=maps_for(recipe))
    assert not review["can_apply"] and review["conflicts"] and review["candidate"] is None
    with pytest.raises(ValueError, match="has conflicts"):
        authored.movie.apply_import(review)
    assert authored.movie.to_dict() == recipe and authored.export_state() == scene


def test_documented_import_example_runs_headlessly():
    page = Path(__file__).parents[1] / "docs/content/user/movie/timeline.md"
    section = page.read_text().split("### Reviewing a recipe for a prepared scene", 1)[1]
    example = section.split("```python\n", 1)[1].split("```", 1)[0]
    exec(compile(example, str(page), "exec"), {"__name__": "movie_import_documentation"})


def test_matching_local_uid_does_not_establish_molecular_region_correspondence(authored):
    recipe = authored.movie.to_dict()
    scene = authored.export_state()
    region = next(row for row in scene["regions"] if row["tag"] == "site")
    uid = region["uid"]
    region["atom_indices"] = [4, 5]
    authored.import_state(scene)
    assert authored.regions["site"].uid == uid and authored.regions["site"].atom_indices == (4, 5)
    review = authored.movie.review_import(recipe)
    assert not review["can_apply"] and any(row["reason"] == "target_replaced" for row in review["conflicts"])
    mapping = [{"source": {"domain": "region", "tag": "site"}, "target": {"domain": "region", "tag": "site"}}]
    review = authored.movie.review_import(recipe, target_map=mapping)
    assert review["can_apply"]
    row = next(row for row in review["targets"] if row["track"] == "site-alpha")
    assert row["source_identity"]["uid"] == row["target_identity"]["uid"]
    assert row["source_identity"]["definition_sha256"] != row["target_identity"]["definition_sha256"]


def test_region_identity_keeps_dependency_definitions(authored):
    from molsysviewer.viewer._movie_import import _identity

    left = authored.regions.add("atom_index < 2", tag="left")
    right = authored.regions.add("atom_index >= 2 and atom_index < 4", tag="right")
    left.set_mode("dynamic")
    right.set_mode("dynamic")
    derived = left.union(right, tag="derived")
    before = authored.export_state()
    old = next(row for row in before["regions"] if row["uid"] == derived.uid)
    assert old["mode"] == "dynamic" and "atom_indices" not in old
    after = deepcopy(before)
    operand = next(row for row in after["regions"] if row["uid"] == left.uid)
    operand["selection"] = "atom_index < 5"
    # Compare two real exported definitions with one declared operand edit;
    # no coordinates, detector outputs or renderer state are substituted.
    assert _identity(before, "region", old) != _identity(after, "region", old)
