"""Reviewable Movie baseline edits on real molecular scene owners."""

import asyncio
import json
import runpy
from pathlib import Path

import pytest
from molsysviewer.interactions import _analysis_signature
from molsysviewer.viewer._movie_seek import _apply_sample, _visibility_commands, _visibility_owners

make_appearance_view = runpy.run_path(str(Path(__file__).with_name("test_movie_appearance.py")))["make_appearance_view"]


@pytest.fixture
def authored():
    with make_appearance_view() as view:
        yield view


def test_review_is_detached_and_acceptance_preserves_keys_scene_and_science(authored):
    recipe = authored.movie.to_dict()
    authored.annotations.add("Later", atom_indices=[1], tag="later")
    scene = authored.export_state()
    scientific = _analysis_signature(authored.interactions.get_analysis("story-hbonds"))
    with pytest.raises(ValueError, match="untracked changes"):
        authored.movie.validate()
    review = authored.movie.review_rebase()
    assert review["can_apply"] and not review["conflicts"]
    assert any(row["domain"] == "annotation" and row["tag"] == "later" for row in review["changes"])
    assert authored.movie.to_dict() == recipe and authored.export_state() == scene
    assert review["candidate"]["tracks"] == recipe["tracks"]
    authored.movie.rebase(json.loads(json.dumps(review)))
    assert authored.movie.to_dict()["tracks"] == recipe["tracks"]
    assert authored.export_state() == scene
    assert _analysis_signature(authored.interactions.get_analysis("story-hbonds")) == scientific
    authored.movie.validate()
    review["candidate"]["baseline"]["scene"]["annotations"].clear()
    assert authored.movie.to_dict()["baseline"]["scene"]["annotations"]


def test_scene_edits_are_named_in_review_and_implicit_track_changes_are_explicit(authored):
    authored.shapes["site"].set_alpha(0.6)
    review = authored.movie.review_rebase()
    assert review["can_apply"]
    assert "sphere-alpha" in review["affected_tracks"]
    assert any(row["domain"] == "shape" and row["tag"] == "site" for row in review["changes"])
    old = authored.movie.evaluate(0)
    authored.movie.rebase(review)
    assert authored.movie.evaluate(0) != old
    assert (
        next(
            row
            for row in authored.movie.evaluate(0)["appearance"]
            if row["domain"] == "shape" and row["property"] == "alpha"
        )["value"]
        == 0.6
    )


@pytest.mark.parametrize("change", ["scene", "recipe", "edit-review", "edit-candidate", "bool-as-number"])
def test_stale_or_edited_reviews_preserve_latest_work(authored, change):
    review = authored.movie.review_rebase()
    if change == "scene":
        authored.annotations.add("User work", atom_indices=[0], tag="work")
    elif change == "recipe":
        authored.movie.set_duration(2000)
    elif change == "edit-review":
        review["changes"].append({"made_up": True})
    elif change == "edit-candidate":
        review["candidate"]["tracks"].clear()
    else:
        review["can_apply"] = 1
    expected, scene = authored.movie.to_dict(), authored.export_state()
    with pytest.raises(ValueError, match="stale or edited"):
        authored.movie.rebase(review)
    assert authored.movie.to_dict() == expected and authored.export_state() == scene


@pytest.mark.parametrize("change", ["missing", "replaced-region", "incompatible-sphere", "color-layer"])
def test_target_conflicts_cannot_silently_drop_or_rebind_tracks(authored, change):
    if change == "missing":
        authored.shapes["site"].delete()
    elif change == "replaced-region":
        authored.regions["site"].delete()
        authored.regions.add(tag="site", atom_indices=[0, 1], representation="ball-and-stick")
    elif change == "incompatible-sphere":
        authored.shapes["site"].delete()
        authored.shapes.links.add_links(atom_pairs=[[0, 1]], tag="site")
    else:
        authored.whole.set_color("#00ff00")
    expected = authored.movie.to_dict()
    review = authored.movie.review_rebase()
    assert not review["can_apply"] and review["conflicts"] and review["candidate"] is None
    with pytest.raises(ValueError, match="has conflicts"):
        authored.movie.rebase(review)
    assert authored.movie.to_dict() == expected


def test_static_definition_ignores_owned_tracks_and_navigation_but_not_untracked_shape_geometry(authored):
    owners = _visibility_owners(authored, authored.movie._timeline.visibility_targets())
    for at in [1000, 0, 500]:
        sample = authored.movie._timeline.evaluate(at, tracked_visibility=True)
        _apply_sample(
            authored.movie, authored.movie._timeline, sample, _visibility_commands(owners, sample["visibility"])
        )
        authored.movie.validate()
    authored.shapes["site"].delete()
    authored.shapes.add_sphere(center="[2,0,0] angstrom", radius="2 angstrom", tag="site")
    with pytest.raises(ValueError, match="untracked changes"):
        authored.movie.validate()


def test_changed_scene_is_rejected_before_seek_changes_or_frontend_reservation(authored):
    authored.annotations.add("Later", atom_indices=[0], tag="later")
    authored._ready = True
    authored._frontend_capabilities = {"visual_state_capture": [2], "movie_appearance": [1]}
    state = authored.export_state()
    with pytest.raises(ValueError, match="untracked changes"):
        asyncio.run(authored.movie.seek_async(500))
    assert authored.export_state() == state and not authored._frontend_requests._pending


def test_rebase_camera_is_explicit_and_navigation_alone_does_not_redefine_it(authored):
    old = authored.movie.to_dict()["baseline"]["camera"]
    authored.player.go_to_structure(2)
    review = authored.movie.review_rebase()
    assert review["candidate"]["baseline"]["camera"] == old
    assert review["candidate"]["baseline"]["scene"]["view"]["structure_index"] == 2
    explicit = {"position": [0, 0, 20], "target": [0, 0, 0], "up": [0, 1, 0]}
    review = authored.movie.review_rebase(camera=explicit)
    authored.movie.rebase(review)
    assert authored.movie.to_dict()["baseline"]["camera"] == explicit


def test_rebase_does_not_adopt_a_different_molecular_system(authored):
    import molsysviewer as msv

    recipe = authored.movie.to_dict()
    with msv.demo["dialanine"] as source:
        authored.load(source.molsys, mode="replace")
    # Managed editing may retire the old recipe; reinstalling private data is
    # unnecessary here: if retained, the reviewer must report the mismatch.
    if authored.movie._timeline is not None:
        review = authored.movie.review_rebase()
        assert not review["can_apply"]
        assert review["conflicts"][0]["reason"] == "molecular_binding_changed"
    else:
        with pytest.raises(ValueError, match="Set a Movie baseline"):
            authored.movie.review_rebase()
    assert recipe["baseline"]["binding"]["n_atoms"] == 62


def test_rebase_refuses_replaced_named_science_without_rewriting_occurrences(authored):
    authored.interactions.hbonds.get_buch_hbonds(
        name="alternative", structure_indices="all", distance_threshold="0.3 nm"
    )
    analyses = dict(authored.molsys.interactions)
    analyses["story-hbonds"] = analyses.pop("alternative")
    authored.molsys.interactions = analyses
    expected = authored.movie.to_dict()
    review = authored.movie.review_rebase()
    assert not review["can_apply"] and review["candidate"] is None
    assert review["conflicts"]
    with pytest.raises(ValueError, match="has conflicts"):
        authored.movie.rebase(review)
    assert authored.movie.to_dict() == expected


def test_review_summaries_do_not_duplicate_large_scene_arrays(authored):
    authored.layers.add("large", meta={"values": list(range(5000))})
    review = authored.movie.review_rebase()
    row = next(row for row in review["changes"] if row["domain"] == "layer" and row["tag"] == "large")
    assert row["after"]["kind"] == "dict" and row["after"]["sha256"].startswith("sha256:")
    assert len(json.dumps(review["changes"])) < 2000
    assert review["candidate"]["baseline"]["scene"]["layers"][0]["meta"]["values"] == list(range(5000))


def test_review_accepts_json_integer_valued_float_roundtrip(authored):
    def numeric(token):
        value = float(token)
        return int(value) if value.is_integer() else value

    review = json.loads(json.dumps(authored.movie.review_rebase()), parse_float=numeric)
    authored.movie.rebase(review)
    authored.movie.validate()


@pytest.mark.parametrize("initially_hidden", [False, True])
def test_layer_gate_is_reversible_and_member_tracks_compose(authored, initially_hidden):
    camera = authored.movie.to_dict()["baseline"]["camera"]
    authored.layers.add("story")
    authored.shapes["site"].set_layer_tag("story")
    authored.shapes.add_sphere(center="[0,0,0] angstrom", radius="1 angstrom", tag="other", layer_tag="story").hide()
    if initially_hidden:
        authored.layers["story"].hide()
    authored.movie.set_baseline(1000, camera=camera)
    authored.movie.add_track(
        {
            "tag": "gate",
            "target": {"domain": "layer", "tag": "story"},
            "property": "visible",
            "keys": [{"time_ms": 200, "value": True}, {"time_ms": 500, "value": False}],
        }
    )
    authored.movie.add_track(
        {
            "tag": "member",
            "target": {"domain": "shape", "tag": "other"},
            "property": "visible",
            "keys": [{"time_ms": 300, "value": True}],
        }
    )
    owners = _visibility_owners(authored, authored.movie._timeline.visibility_targets())
    observations = {}
    for at in [0, 400, 800, 0, 400, 0]:
        sample = authored.movie._timeline.evaluate(at, tracked_visibility=True)
        commands = _visibility_commands(owners, sample["visibility"], authored.movie._timeline)
        _apply_sample(authored.movie, authored.movie._timeline, sample, commands)
        observed = (authored.shapes["site"]._hidden, authored.shapes["other"]._hidden)
        if at in observations:
            assert observed == observations[at]
        observations[at] = observed
        authored.movie.validate()
    assert observations[0] == (initially_hidden, True)
    assert observations[400] == (False, False)
    assert observations[800] == (True, True)


def test_visible_layer_preserves_untracked_hidden_member_on_reverse_seek(authored, tmp_path):
    camera = authored.movie.to_dict()["baseline"]["camera"]
    authored.layers.add("story")
    authored.shapes["site"].set_layer_tag("story")
    authored.shapes.add_sphere(center="[0,0,0] angstrom", radius="1 angstrom", tag="other", layer_tag="story").hide()
    authored.movie.set_baseline(1000, camera=camera)
    authored.movie.add_track(
        {
            "tag": "gate",
            "target": {"domain": "layer", "tag": "story"},
            "property": "visible",
            "keys": [{"time_ms": 500, "value": False}],
        }
    )
    owners = _visibility_owners(authored, authored.movie._timeline.visibility_targets())
    for at in [0, 1000, 0]:
        sample = authored.movie._timeline.evaluate(at, tracked_visibility=True)
        commands = _visibility_commands(owners, sample["visibility"], authored.movie._timeline)
        assert all(command.__self__ is not authored.shapes["other"] for command in commands)
        _apply_sample(
            authored.movie,
            authored.movie._timeline,
            sample,
            _visibility_commands(owners, sample["visibility"], authored.movie._timeline),
        )
        assert authored.shapes["other"]._hidden
        authored.movie.validate()
    import molsysviewer as msv

    path = tmp_path / "gate.msv"
    authored.save_session(path)
    with msv.load_session(path) as restored:
        owners = _visibility_owners(restored, restored.movie._timeline.visibility_targets())
        for at in [0, 1000, 0]:
            sample = restored.movie._timeline.evaluate(at, tracked_visibility=True)
            _apply_sample(
                restored.movie,
                restored.movie._timeline,
                sample,
                _visibility_commands(owners, sample["visibility"], restored.movie._timeline),
            )
            assert restored.shapes["other"]._hidden
            restored.movie.validate()
    # Ordinary layer show still shows every member; only Movie adds the gate.
    authored.layers["story"].hide()
    authored.layers["story"].show()
    assert not authored.shapes["other"]._hidden


def test_interaction_visibility_does_not_change_its_static_definition(authored):
    authored.movie.add_track(
        {
            "tag": "hide-contacts",
            "target": {"domain": "interaction", "tag": "contacts"},
            "property": "visible",
            "keys": [{"time_ms": 500, "value": False}],
        }
    )
    owners = _visibility_owners(authored, authored.movie._timeline.visibility_targets())
    for at in [1000, 0, 1000]:
        sample = authored.movie._timeline.evaluate(at, tracked_visibility=True)
        _apply_sample(
            authored.movie,
            authored.movie._timeline,
            sample,
            _visibility_commands(owners, sample["visibility"], authored.movie._timeline),
        )
        authored.movie.validate()
