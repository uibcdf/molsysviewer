from __future__ import annotations

import pytest

from molsysviewer.demo import demo


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def test_import_state_rejects_version_1():
    view = _mute(demo["dialanine"])
    with pytest.raises(ValueError, match="version 1"):
        view.import_state({"version": 1, "regions": []})


def test_round_trip_preserves_region_visual_recipe_and_hidden_state():
    source = _mute(demo["dialanine"])
    styled = source.new_region(atom_indices=[0, 1, 2], tag="styled", skip_digestion=True)
    styled.set_representation("spacefill", skip_digestion=True)
    hidden = source.new_region(atom_indices=[3, 4], tag="hidden", skip_digestion=True)
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
    lower = source.new_region(atom_indices=[0, 1, 2], tag="lower", skip_digestion=True)
    upper = source.new_region(atom_indices=[1, 2, 3], tag="upper", skip_digestion=True)
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
    a = source.new_region(atom_indices=[0, 1], tag="a", skip_digestion=True)
    # Advance the order counter well beyond the number of kept regions, so a
    # plain reconstruction (which bumps the counter once per restored region)
    # cannot coincidentally reach the true high-water mark. Only an explicit
    # restore of the mark makes a post-import region outrank the restored ones.
    for i in range(5):
        dummy = source.new_region(atom_indices=[6, 7], tag=f"dummy{i}", skip_digestion=True)
        dummy.delete(skip_digestion=True)
    b = source.new_region(atom_indices=[2, 3], tag="b", skip_digestion=True)
    top_order = max(a.order, b.order)
    assert top_order >= 6  # the gap the mark must bridge

    state = source.export_state()

    target = _mute(demo["dialanine"])
    target.import_state(state)

    fresh = target.new_region(atom_indices=[4, 5], tag="fresh", skip_digestion=True)
    # A region created after the import must outrank every restored region.
    assert fresh.order > top_order
    assert fresh.order > target.regions["a"].order
    assert fresh.order > target.regions["b"].order


def test_export_filters_transient_overlay_regions():
    source = _mute(demo["dialanine"])
    source.new_region(atom_indices=[0, 1], tag="keep", skip_digestion=True)
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
    a = source.new_region(atom_indices=[0, 1, 2], tag="a", skip_digestion=True)
    b = source.new_region(atom_indices=[2, 3, 4], tag="b", skip_digestion=True)
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
