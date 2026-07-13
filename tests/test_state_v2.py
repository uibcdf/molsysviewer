from __future__ import annotations

import pytest

from molsysviewer.demo import demo
from molsysviewer import pyunitwizard as puw


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def test_import_state_rejects_version_1():
    view = _mute(demo["dialanine"])
    with pytest.raises(ValueError, match="version 1"):
        view.import_state({"version": 1, "regions": []})


def test_export_state_v2_captures_scene_objects_layers_and_structured_anchor():
    view = _mute(demo["dialanine"])
    layer = view.layers.add("analysis", kind="mixed", meta={"owner": "lab"}, skip_digestion=True)
    annotation = view.annotations.add(
        "site",
        atom_indices=[0, 1],
        tag="note1",
        layer_tag="analysis",
        label_style={"color": "#123456"},
    )
    annotation.hide(skip_digestion=True)
    measurement = view.measurements.add("distance", [0], [1], tag="distance1")
    measurement.hide(skip_digestion=True)
    shape = view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        color="#FF8800",
        tag="site1",
        layer_tag="analysis",
        skip_digestion=True,
    )
    shape.hide(skip_digestion=True)
    layer.hide(skip_digestion=True)

    state = view.export_state()

    assert state["annotations"][0]["anchor"] == {"type": "atoms", "indices": [0, 1]}
    assert "atom_indices" not in state["annotations"][0]["options"]
    assert state["annotations"][0]["hidden"] is True
    assert state["measurements"][0]["hidden"] is True
    assert state["shapes"][0]["options"]["color"] == 0xFF8800
    assert state["shapes"][0]["options"]["radius"] == 2.0
    assert state["shapes"][0]["layer_tag"] == "analysis"
    assert state["shapes"][0]["hidden"] is True
    assert state["layers"] == [{
        "tag": "analysis",
        "kind": "shape",
        "meta": {"owner": "lab"},
        "provenance": "user",
        "hidden": True,
    }]


def test_scene_objects_and_user_layer_round_trip_as_usable_python_model():
    source = _mute(demo["dialanine"])
    source.layers.add("analysis", kind="mixed", meta={"owner": "lab"}, skip_digestion=True)
    annotation = source.annotations.add(
        "site",
        atom_indices=[0, 1],
        tag="note1",
        layer_tag="analysis",
        label_style={
            "color": "#123456",
            "size_em": 1.4,
            "background": False,
            "background_opacity": 0.35,
        },
    )
    measurement = source.measurements.add(
        "distance",
        [0],
        [1],
        tag="distance1",
        layer_tag="analysis",
    )
    shape = source.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        color="#FF8800",
        tag="site1",
        layer_tag="analysis",
        skip_digestion=True,
    )
    annotation.hide(skip_digestion=True)
    measurement.hide(skip_digestion=True)
    shape.hide(skip_digestion=True)

    target = _mute(demo["dialanine"])
    target.import_state(source.export_state())

    assert target.annotations.get("note1") is not None
    assert target.measurements.get("distance1") is not None
    assert target.shapes.get("site1") is not None
    assert target.measurements.count() == len(target.measurements.tags()) == 1
    assert target.annotations.info("note1")["visible"] is False
    assert target.annotations.info("note1")["style"] == {
        "color": "#123456",
        "size_em": 1.4,
        "background": False,
        "background_opacity": 0.35,
    }
    assert target.measurements.info("distance1")[0]["visible"] is False
    assert target.shapes.info("site1")[0]["visible"] is False
    assert target.shapes.records()[0]["options"]["color"] == 0xFF8800
    assert target.shapes.records()[0]["options"]["radius"] == 2.0
    assert target.layers["analysis"].provenance == "user"
    assert target.layers["analysis"].meta == {"owner": "lab"}

    target.measurements.show("distance1", skip_digestion=True)
    target.measurements.hide("distance1", skip_digestion=True)
    target.shapes.delete("site1", skip_digestion=True)
    assert target.shapes.get("site1") is None


def test_hidden_user_layer_applies_after_its_members_are_restored():
    source = _mute(demo["dialanine"])
    layer = source.layers.add("analysis", skip_digestion=True)
    source.annotations.add("site", atom_indices=[0], tag="note1", layer_tag="analysis")
    layer.hide(skip_digestion=True)

    target = _mute(demo["dialanine"])
    target.import_state(source.export_state())

    assert target.layers["analysis"]._hidden is True  # noqa: SLF001
    assert target.annotations.get("note1")._hidden is True  # noqa: SLF001


def test_old_v2_document_without_additive_scene_object_keys_imports_cleanly():
    target = _mute(demo["dialanine"])
    target.import_state({"version": 2, "regions": [], "annotations": [], "measurements": [], "selections": []})

    assert target.shapes.count() == 0
    assert target.layers.count() == 0


def test_import_clears_scene_history_and_does_not_grow_replay_history():
    source = _mute(demo["dialanine"])
    source.annotations.add("site", atom_indices=[0], tag="note1")
    state = source.export_state()

    target = _mute(demo["dialanine"])
    target.regions.add(atom_indices=[0], tag="temporary", skip_digestion=True)
    assert target.history.can_undo() is True

    target.import_state(state)
    first_size = len(target._message_history)  # noqa: SLF001
    assert target.history.can_undo() is False
    target.import_state(state)

    assert len(target._message_history) == first_size  # noqa: SLF001
    assert target.history.can_undo() is False


def test_import_suspends_checkpoints_while_rebuilding_regions(monkeypatch):
    source = _mute(demo["dialanine"])
    region = source.regions.add(atom_indices=[0, 1], tag="site", skip_digestion=True)
    region.set_representation("spacefill", skip_digestion=True)
    state = source.export_state()
    target = _mute(demo["dialanine"])
    calls = 0
    original = target.export_state

    def counted_export_state():
        nonlocal calls
        calls += 1
        return original()

    monkeypatch.setattr(target, "export_state", counted_export_state)

    target.import_state(state)

    assert calls == 0


def test_stored_tag_high_water_gap_is_restored_before_new_allocations():
    state = {
        "version": 2,
        "regions": [],
        "annotations": [],
        "measurements": [],
        "selections": [],
        "tag_high_water_marks": {"measurement": 12},
    }
    target = _mute(demo["dialanine"])

    target.import_state(state)
    created = target.measurements.add("distance", [0], [1])

    assert created.tag == "measurement13"


def test_missing_anchors_restore_as_broken_manageable_objects():
    state = {
        "version": 2,
        "annotations": [{
            "op": "add_label",
            "tag": "note1",
            "options": {"tag": "note1", "text": "lost"},
            "anchor": {"type": "atoms", "indices": [999]},
        }],
        "measurements": [{
            "op": "add_distance_measurement",
            "tag": "distance1",
            "options": {"tag": "distance1", "picks_atom_indices": [[0], [999]]},
        }],
        "regions": [],
        "selections": [],
    }
    target = _mute(demo["dialanine"])

    target.import_state(state)

    assert target.annotations.get("note1").broken is True
    assert target.measurements.get("distance1").broken is True
    assert target.annotations.info("note1")["broken"] is True
    assert target.measurements.info("distance1")[0]["broken"] is True
    assert "999" in target.annotations.info("note1")["broken_reason"]
    target.annotations.delete("note1", skip_digestion=True)
    target.measurements.delete("distance1", skip_digestion=True)


def test_import_conflict_policy_is_domain_scoped_and_rename_rewrites_layer_membership():
    source = _mute(demo["dialanine"])
    source.layers.add("analysis", skip_digestion=True)
    source.annotations.add("incoming", atom_indices=[0], tag="site1", layer_tag="analysis")
    state = source.export_state()

    target = _mute(demo["dialanine"])
    target.layers.add("analysis", skip_digestion=True)
    target.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="site1",
        skip_digestion=True,
    )
    target.annotations.add("existing", atom_indices=[1], tag="site1")

    with pytest.raises(ValueError, match="layer tag 'analysis'"):
        target.import_state(state, clear_first=False)

    target.import_state(state, clear_first=False, on_conflict="rename")

    assert target.annotations.get("site1_2") is not None
    assert target.annotations.get("site1_2").layer_tag == "analysis_2"
    assert target.shapes.get("site1") is not None


def test_conflict_raise_is_preflighted_before_any_scene_mutation():
    source = _mute(demo["dialanine"])
    source.whole.set_representation("spacefill", skip_digestion=True)
    source.annotations.add("incoming", atom_indices=[0], tag="site1")
    state = source.export_state()

    target = _mute(demo["dialanine"])
    target.whole.set_representation("ball-and-stick", skip_digestion=True)
    target.annotations.add("existing", atom_indices=[1], tag="site1")
    before = target.export_state()

    with pytest.raises(ValueError, match="annotation tag 'site1'"):
        target.import_state(state, clear_first=False)

    assert target.export_state() == before


def test_round_trip_preserves_region_visual_recipe_and_hidden_state():
    source = _mute(demo["dialanine"])
    styled = source.regions.add(atom_indices=[0, 1, 2], tag="styled", skip_digestion=True)
    styled.set_representation("spacefill", skip_digestion=True)
    hidden = source.regions.add(atom_indices=[3, 4], tag="hidden", skip_digestion=True)
    hidden.set_representation("cartoon", skip_digestion=True)
    hidden.hide(skip_digestion=True)

    state = source.export_state()

    target = _mute(demo["dialanine"])
    target.import_state(state)

    assert set(target.regions.keys()) == {"styled", "hidden"}
    assert target.regions["styled"].representation == "spacefill"
    assert target.regions["styled"].uid == styled.uid
    assert target.regions["styled"].order == styled.order
    assert target.regions["hidden"]._hidden is True  # noqa: SLF001


def test_round_trip_preserves_whole_representation_and_visibility():
    source = _mute(demo["dialanine"])
    source.whole.set_representation("spacefill", skip_digestion=True)
    source.whole.hide(skip_digestion=True)

    state = source.export_state()
    assert state["whole"]["representation"] == "spacefill"
    assert state["whole"]["visible"] is False

    target = _mute(demo["dialanine"])
    target.import_state(state)

    assert target.whole.representation == "spacefill"
    assert target.whole.visible is False


def test_round_trip_preserves_overlap_colour_winner_via_order():
    source = _mute(demo["dialanine"])
    lower = source.regions.add(atom_indices=[0, 1, 2], tag="lower", skip_digestion=True)
    upper = source.regions.add(atom_indices=[1, 2, 3], tag="upper", skip_digestion=True)
    # lower.order < upper.order, so upper wins on the shared atoms {1, 2}.
    lower.set_color_by_values([0.0, 0.0, 0.0], element="atom",
                              palette=[0xAA0000, 0xAA0000], skip_digestion=True)
    upper.set_color_by_values([0.0, 0.0, 0.0], element="atom",
                              palette=[0x0000BB, 0x0000BB], skip_digestion=True)
    assert source._atom_color_map[1] == 0x0000BB  # noqa: SLF001  (upper wins)

    state = source.export_state()

    target = _mute(demo["dialanine"])
    target.import_state(state)

    # The winner in the overlap zone survives the round trip.
    assert target._atom_color_map[1] == 0x0000BB  # noqa: SLF001
    assert target._atom_color_map[2] == 0x0000BB  # noqa: SLF001
    assert target._atom_color_map[0] == 0xAA0000  # noqa: SLF001  (only lower)
    assert target._atom_color_map[3] == 0x0000BB  # noqa: SLF001  (only upper)


def test_import_restores_order_high_water_mark():
    source = _mute(demo["dialanine"])
    a = source.regions.add(atom_indices=[0, 1], tag="a", skip_digestion=True)
    # Advance the order counter well beyond the number of kept regions, so a
    # plain reconstruction (which bumps the counter once per restored region)
    # cannot coincidentally reach the true high-water mark. Only an explicit
    # restore of the mark makes a post-import region outrank the restored ones.
    for i in range(5):
        dummy = source.regions.add(atom_indices=[6, 7], tag=f"dummy{i}", skip_digestion=True)
        dummy.delete(skip_digestion=True)
    b = source.regions.add(atom_indices=[2, 3], tag="b", skip_digestion=True)
    top_order = max(a.order, b.order)
    assert top_order >= 6  # the gap the mark must bridge

    state = source.export_state()

    target = _mute(demo["dialanine"])
    target.import_state(state)

    fresh = target.regions.add(atom_indices=[4, 5], tag="fresh", skip_digestion=True)
    # A region created after the import must outrank every restored region.
    assert fresh.order > top_order
    assert fresh.order > target.regions["a"].order
    assert fresh.order > target.regions["b"].order


def test_export_filters_transient_overlay_regions():
    source = _mute(demo["dialanine"])
    source.regions.add(atom_indices=[0, 1], tag="keep", skip_digestion=True)
    # A transient focus overlay registers as a region internally; it must not
    # survive a round trip as a manageable region.
    source.styles.focus(atom_indices=[2, 3], representation="spacefill", skip_digestion=True)

    state = source.export_state()

    exported_tags = {r["tag"] for r in state["regions"]}
    assert "keep" in exported_tags
    assert not any(source._TRANSIENT_REGION_TAG.fullmatch(t) for t in exported_tags)  # noqa: SLF001

    target = _mute(demo["dialanine"])
    target.import_state(state)
    assert not any(target._TRANSIENT_REGION_TAG.fullmatch(t) for t in target.regions)  # noqa: SLF001


def test_import_restores_boolean_region_in_topological_order():
    source = _mute(demo["dialanine"])
    a = source.regions.add(atom_indices=[0, 1, 2], tag="a", skip_digestion=True)
    b = source.regions.add(atom_indices=[2, 3, 4], tag="b", skip_digestion=True)
    union = a.union(b, tag="union", skip_digestion=True)
    assert union.provenance["operands"] == [a.uid, b.uid]

    state = source.export_state()
    # Force the dependent to be listed before its operands; import must reorder.
    state["regions"].sort(key=lambda r: 0 if r["tag"] == "union" else 1)

    target = _mute(demo["dialanine"])
    target.import_state(state)

    assert set(target.regions.keys()) == {"a", "b", "union"}
    assert target.regions["union"].provenance["operands"] == [a.uid, b.uid]


def test_import_raises_on_missing_operand():
    view = _mute(demo["dialanine"])
    state = {
        "version": 2,
        "regions": [
            {
                "uid": "region-uid-99",
                "tag": "orphan",
                "provenance": {"kind": "boolean", "op": "or", "operands": ["region-uid-1"]},
                "atom_indices": [0, 1],
                "order": 1,
            }
        ],
    }
    with pytest.raises(ValueError, match="missing operand"):
        view.import_state(state)


def test_import_raises_on_dependency_cycle():
    view = _mute(demo["dialanine"])
    state = {
        "version": 2,
        "regions": [
            {"uid": "u1", "tag": "a", "atom_indices": [0],
             "provenance": {"kind": "boolean", "op": "or", "operands": ["u2"]}, "order": 1},
            {"uid": "u2", "tag": "b", "atom_indices": [1],
             "provenance": {"kind": "boolean", "op": "or", "operands": ["u1"]}, "order": 2},
        ],
    }
    with pytest.raises(ValueError, match="cycle"):
        view.import_state(state)


def test_pre_phase1_v2_document_still_imports_cleanly():
    # The new keys (shapes, layers, tag_high_water_marks) and the structured anchor are
    # ADDITIVE: a session saved before this phase must still load. That is what keeps the
    # format at v2 instead of forcing a v3 migration of every document in the wild.
    #
    # This is deliberately a hand-written document, not one produced by export_state():
    # a round-trip test would silently start passing the *new* format the moment the
    # writer changes, which is exactly the regression it is meant to catch.
    view = demo["dialanine"]
    old_document = {
        "version": 2,
        "annotations": [
            {
                "op": "add_label",
                "tag": "legacy",
                "options": {
                    "text": "old",
                    "tag": "legacy",
                    "layer_tag": "legacy",
                    "atom_indices": [0],  # flat anchor, pre-anchor-object
                },
            }
        ],
        "measurements": [],
        "selections": [],
        "regions": [],
        "whole": {
            "representation": None,
            "preset": None,
            "params": {},
            "visible": True,
            "color_scheme": None,
            "color_layer": {},
        },
        "active_selection": {"atom_indices": []},
        "order_high_water_mark": 0,
        "uid_high_water_mark": 0,
        # no "shapes", no "layers", no "tag_high_water_marks"
    }

    view.import_state(old_document)

    assert view.annotations.tags() == ["legacy"]
    assert view.shapes.tags() == []                       # absent key -> empty, not an error
    assert view.annotations.info("legacy")["n_atoms"] == 1  # the flat anchor was understood
    view.annotations.hide("legacy")                        # and the object is manageable
    assert view.annotations.info("legacy")["visible"] is False


def test_broken_measurement_reports_no_value_not_a_stale_one():
    # Contract S7: a stale number is the worst outcome in this codebase. An error is loud, a
    # missing value is visible, but a believable wrong one ends up in a figure and in a paper.
    #
    # Restoring a measurement onto a structure that cannot produce it must NOT surface the
    # number that was computed on the *other* structure.
    source = demo["181L"]
    source.measurements.add_distance([0], [1400], tag="far")
    original = source.measurements.info("far")[0]["value"]
    assert original is not None
    document = source.export_state()

    target = demo["dialanine"]          # 22 atoms: atom 1400 does not exist here
    target.import_state(document)

    restored = target.measurements.info("far")[0]
    assert restored["broken"] is True
    assert restored["value"] is None, "the stale value from the other structure survived"


def test_a_restored_measurement_is_usable_not_merely_present():
    source = _mute(demo["dialanine"])
    source.measurements.add_distance([0], [10], tag="d1")
    original = source.measurements.info("d1")[0]
    document = source.export_state()

    target = _mute(demo["dialanine"])
    target.import_state(document)

    restored = target.measurements.info("d1")[0]
    assert restored["broken"] is False
    assert restored["value"] == original["value"]
