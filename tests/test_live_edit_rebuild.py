from __future__ import annotations

import pytest
import numpy as np

pytest.importorskip("molsysmt")
import molsysmt as msm
from molsysmt.native import Structures

from molsysviewer import MolSysView
from molsysviewer.demo import demo
from molsysviewer._pyunitwizard import puw

from _edit_helpers import apply_add, apply_append_structures, apply_remove, apply_set


def test_apply_system_edit_reconciles_external_molsysmt_edit():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    view.shapes.add_links(
        atom_pairs=[[0, 1], [1, 2]],
        tag="links",
        skip_digestion=True,
    )
    view.hide(selection=[2], skip_digestion=True)

    old_n_atoms = int(msm.get(view.molsys, element="system", n_atoms=True, skip_digestion=True))
    removed = {0}
    kept = [index for index in range(old_n_atoms) if index not in removed]
    atom_index_map = {old: new for new, old in enumerate(kept)}
    new_molsys = msm.remove(
        view.molsys,
        selection=[0],
        to_form="molsysmt.MolSys",
        skip_digestion=True,
    )

    view.apply_system_edit(new_molsys, atom_index_map=atom_index_map)

    assert view.molsys is new_molsys
    assert view.regions["frag"].atom_indices == (0, 1)
    assert view.atom_mask is not None
    assert len(view.atom_mask) == 21
    assert bool(view.atom_mask[0]) is True
    assert bool(view.atom_mask[1]) is False

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 21

    links_msg = next(
        msg
        for msg in view._message_history
        if msg.get("op") == "add_network_links" and msg.get("options", {}).get("tag") == "links"
    )
    assert links_msg["options"]["atom_pairs"] == [[0, 1]]


def test_apply_system_edit_requires_molecular_system():
    view = demo["dialanine"]

    with pytest.raises(ValueError, match="requires a molecular system"):
        view.apply_system_edit(None)


def test_append_structures_rebuild_preserves_state_and_sets_multiple_structures():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    pocket_layer = view.shapes.add_pocket_surface(
        atom_indices=[0, 1, 2],
        tag="pocket",
        skip_digestion=True,
    )
    pocket_layer.hide(skip_digestion=True)

    apply_append_structures(view, demo["dialanine"]._molsys)  # noqa: SLF001

    assert view.regions["frag"].atom_indices == (0, 1, 2)
    assert view.atom_mask is not None
    assert len(view.atom_mask) == 22
    assert view.atom_mask.all()

    ops = [msg.get("op") for msg in view._message_history]
    assert ops[:2] == ["clear_all", "load_molsys_payload"]

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is True
    assert len(payload_msg["payload"]["structures"]) == 2

    create_region_msg = next(msg for msg in view._message_history if msg.get("op") == "create_region")
    assert create_region_msg["tag"] == "frag"
    assert create_region_msg["atom_indices"] == [0, 1, 2]

    pocket_msg = next(
        msg
        for msg in view._message_history
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1, 2]

    assert {"op": "hide_layer", "tag": "pocket"} in view._message_history
    assert {"op": "hide_region", "tag": "frag"} in view._message_history


def test_load_mode_append_structures_delegates_to_append_path():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys, mode="append_structures", skip_digestion=True)  # noqa: SLF001

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is True
    assert len(payload_msg["payload"]["structures"]) == 2
    assert len(view._load_blocks) == 1  # noqa: SLF001
    assert list(view.regions) == []


def test_load_mode_append_structures_errors_on_empty_view():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    with pytest.raises(ValueError, match="mode='append_structures'"):
        view.load(demo["dialanine"]._molsys, mode="append_structures", skip_digestion=True)  # noqa: SLF001


def test_load_mode_append_structures_supports_topology_only_view():
    topology_only = demo["dialanine"]._molsys.copy()  # noqa: SLF001
    topology_only.structures = Structures(skip_digestion=True)

    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view._molsys = topology_only  # noqa: SLF001
    view.molecular_system = topology_only
    view.selection = "all"
    view.structure_indices = "all"
    view.atom_mask = np.ones(topology_only.topology.get_n_atoms(), dtype=bool)
    view._last_label = "topology"  # noqa: SLF001

    view.load(demo["dialanine"]._molsys, mode="append_structures", skip_digestion=True)  # noqa: SLF001

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is False
    assert len(payload_msg["payload"]["structures"]) == 1


def test_load_mode_auto_replaces_on_empty_view():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys, mode="auto", skip_digestion=True)  # noqa: SLF001

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is False
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 22
    assert len(view._load_blocks) == 1  # noqa: SLF001


def test_load_mode_auto_appends_when_input_has_same_atom_count_and_no_topology():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys.structures.copy(), mode="auto", skip_digestion=True)  # noqa: SLF001

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is True
    assert len(payload_msg["payload"]["structures"]) == 2
    assert len(view._load_blocks) == 1  # noqa: SLF001


def test_load_mode_auto_adds_when_input_has_different_atom_count():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["1TCD"]._molsys, mode="auto", label="protein", skip_digestion=True)  # noqa: SLF001

    assert len(view._load_blocks) == 2  # noqa: SLF001
    assert view._load_blocks[1]["label"] == "protein"  # noqa: SLF001
    assert view._load_blocks[1]["start"] == 22  # noqa: SLF001


def test_add_rebuild_preserves_state_and_expands_atom_payload(monkeypatch):
    monkeypatch.setenv("NUMBA_CACHE_DIR", "/tmp/numba_cache")

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    pocket_layer = view.shapes.add_pocket_surface(
        atom_indices=[0, 1, 2],
        tag="pocket",
        skip_digestion=True,
    )
    pocket_layer.hide(skip_digestion=True)

    apply_add(view, demo["dialanine"]._molsys)  # noqa: SLF001

    assert view.regions["frag"].atom_indices == (0, 1, 2)
    assert view.atom_mask is not None
    assert len(view.atom_mask) == 44
    assert view.atom_mask[:22].all()
    assert not view.atom_mask[22:].any()

    ops = [msg.get("op") for msg in view._message_history]
    assert ops[:2] == ["clear_all", "load_molsys_payload"]

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is False
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 44
    assert len(payload_msg["payload"]["structures"]) == 1

    create_region_msg = next(msg for msg in view._message_history if msg.get("op") == "create_region")
    assert create_region_msg["tag"] == "frag"
    assert create_region_msg["atom_indices"] == [0, 1, 2]

    pocket_msg = next(
        msg
        for msg in view._message_history
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1, 2]

    assert {"op": "hide_layer", "tag": "pocket"} in view._message_history
    assert {"op": "hide_region", "tag": "frag"} in view._message_history

    visibility_msg = next(msg for msg in reversed(view._message_history) if msg.get("op") == "update_visibility")
    assert visibility_msg["options"]["visible_atom_indices"] == list(range(22))


def test_set_rebuild_updates_group_name_and_preserves_hidden_state():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    pocket_layer = view.shapes.add_pocket_surface(
        atom_indices=[0, 1, 2],
        tag="pocket",
        skip_digestion=True,
    )
    pocket_layer.hide(skip_digestion=True)

    apply_set(view, element="group", selection=[0], group_name="ACE2")

    assert view.regions["frag"].atom_indices == (0, 1, 2)

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["payload"]["atoms"]["residue_name"][:5] == ["ACE2"] * 5

    assert {"op": "hide_layer", "tag": "pocket"} in view._message_history
    assert {"op": "hide_region", "tag": "frag"} in view._message_history


def test_set_rebuild_updates_coordinates_with_quantity():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    original_payload = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    original_first = original_payload["payload"]["structures"][0]["coordinates"][0]

    apply_set(
        view,
        element="atom",
        selection=[0],
        coordinates=puw.quantity([[[0.1, 0.2, 0.3]]], "nm"),
    )

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    updated_first = payload_msg["payload"]["structures"][0]["coordinates"][0]

    assert updated_first != original_first
    assert updated_first == pytest.approx([1.0, 2.0, 3.0])
    assert view.regions["frag"].atom_indices == (0, 1, 2)
    assert {"op": "hide_region", "tag": "frag"} in view._message_history


def test_load_first_block_does_not_create_automatic_regions():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys, label="first", skip_digestion=True)  # noqa: SLF001

    assert list(view.regions) == []
    assert view._empty is False  # noqa: SLF001
    assert view._load_blocks == [  # noqa: SLF001
        {
            "index": 0,
            "label": "first",
            "n_atoms": 22,
            "start": 0,
            "stop": 22,
            "region_tag": None,
        }
    ]


def test_second_additive_load_backfills_first_region_and_creates_second():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys, label="first", skip_digestion=True)  # noqa: SLF001
    view.load(demo["dialanine"]._molsys, label="second", skip_digestion=True)  # noqa: SLF001

    assert set(view.regions) == {"first", "second"}
    assert view.regions["first"].atom_indices == tuple(range(22))
    assert view.regions["second"].atom_indices == tuple(range(22, 44))
    assert [block["region_tag"] for block in view._load_blocks] == ["first", "second"]  # noqa: SLF001


def test_third_additive_load_creates_only_new_automatic_region():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys, skip_digestion=True)  # noqa: SLF001
    view.load(demo["dialanine"]._molsys, skip_digestion=True)  # noqa: SLF001
    view.load(demo["dialanine"]._molsys, skip_digestion=True)  # noqa: SLF001

    assert set(view.regions) == {"Load1", "Load2", "Load3"}
    assert view.regions["Load1"].atom_indices == tuple(range(22))
    assert view.regions["Load2"].atom_indices == tuple(range(22, 44))
    assert view.regions["Load3"].atom_indices == tuple(range(44, 66))


def test_add_updates_load_blocks_without_creating_automatic_regions():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys, label="first", skip_digestion=True)  # noqa: SLF001
    apply_add(view, demo["dialanine"]._molsys, label="second")  # noqa: SLF001

    assert list(view.regions) == []
    assert len(view._load_blocks) == 2  # noqa: SLF001
    assert view._load_blocks[0]["label"] == "first"  # noqa: SLF001
    assert view._load_blocks[1]["label"] == "second"  # noqa: SLF001
    assert view._load_blocks[1]["start"] == 22  # noqa: SLF001
    assert view._load_blocks[1]["stop"] == 44  # noqa: SLF001


def test_consecutive_live_edits_keep_replay_state_consistent(monkeypatch):
    monkeypatch.setenv("NUMBA_CACHE_DIR", "/tmp/numba_cache")

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    pocket_layer = view.shapes.add_pocket_surface(
        atom_indices=[0, 1, 2],
        tag="pocket",
        skip_digestion=True,
    )
    pocket_layer.hide(skip_digestion=True)

    apply_set(view, element="group", selection=[0], group_name="ACE2")
    apply_append_structures(view, demo["dialanine"]._molsys)  # noqa: SLF001
    apply_remove(view, selection=[0])

    ops = [msg.get("op") for msg in view._message_history]
    assert ops == [
        "clear_all",
        "load_molsys_payload",
        "hide_layer",
        "create_region",
        "set_region_representation",
        "hide_region",
        "add_pocket_surface",
        "update_visibility",
    ]

    payload_msg = next(msg for msg in view._message_history if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is True
    assert len(payload_msg["payload"]["structures"]) == 2
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 21
    assert payload_msg["payload"]["atoms"]["residue_name"][:5] == ["ACE2"] * 5

    create_region_msg = next(msg for msg in view._message_history if msg.get("op") == "create_region")
    assert create_region_msg["atom_indices"] == [0, 1]
    assert view.regions["frag"].atom_indices == (0, 1)

    pocket_msg = next(
        msg
        for msg in view._message_history
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1]

    visibility_msg = next(msg for msg in reversed(view._message_history) if msg.get("op") == "update_visibility")
    assert visibility_msg["options"]["visible_atom_indices"] == list(range(21))



def test_remove_rebuild_drops_fully_orphaned_scene_objects_and_regions():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.new_region(atom_indices=[0], tag="orphan-region", skip_digestion=True)
    view.shapes.add_pocket_surface(atom_indices=[0], tag="orphan-shape", skip_digestion=True)
    view.annotations.add_annotation(text="orphan", atom_indices=[0], tag="orphan-label", skip_digestion=True)
    view.measurements.add_distance([0], [1], tag="orphan-distance", skip_digestion=True)

    apply_remove(view, selection=[0])

    assert "orphan-region" not in list(view.regions)
    assert "orphan-shape" not in view.shapes.tags(skip_digestion=True)
    assert "orphan-label" not in view.annotations.tags
    assert "orphan-distance" not in view.measurements.tags(skip_digestion=True)
    assert "orphan-shape" not in view._scene_objects  # noqa: SLF001
    assert "orphan-label" not in view._scene_objects  # noqa: SLF001
    assert "orphan-distance" not in view._scene_objects  # noqa: SLF001

    assert not any(msg.get("tag") == "orphan-region" for msg in view._message_history)  # noqa: SLF001
    assert not any(
        msg.get("options", {}).get("tag") in {"orphan-shape", "orphan-label", "orphan-distance"}
        for msg in view._message_history  # noqa: SLF001
    )


def test_export_messages_after_live_edit_chain_remain_replay_safe(monkeypatch):
    monkeypatch.setenv("NUMBA_CACHE_DIR", "/tmp/numba_cache")

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    pocket_layer = view.shapes.add_pocket_surface(
        atom_indices=[0, 1, 2],
        tag="pocket",
        skip_digestion=True,
    )
    pocket_layer.hide(skip_digestion=True)

    apply_set(view, element="group", selection=[0], group_name="ACE2")
    apply_append_structures(view, demo["dialanine"]._molsys)  # noqa: SLF001
    apply_remove(view, selection=[0])

    exported = view._clean_message_history()  # noqa: SLF001

    assert [msg.get("op") for msg in exported] == [
        "clear_all",
        "load_molsys_payload",
        "hide_layer",
        "create_region",
        "set_region_representation",
        "hide_region",
        "add_pocket_surface",
    ]

    payload_msg = next(msg for msg in exported if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is True
    assert len(payload_msg["payload"]["structures"]) == 2
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 21

    region_msg = next(msg for msg in exported if msg.get("op") == "create_region")
    assert region_msg["atom_indices"] == [0, 1]

    pocket_msg = next(
        msg
        for msg in exported
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1]

    assert not any(msg.get("op") == "update_visibility" for msg in exported)


def test_remove_rebuild_remaps_regions_shapes_and_visibility():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    pocket_layer = view.shapes.add_pocket_surface(
        atom_indices=[0, 1, 2],
        mouth_atom_indices=[[0, 1], [2, 3]],
        tag="pocket",
        skip_digestion=True,
    )
    pocket_layer.hide(skip_digestion=True)

    view.shapes.add_links(
        atom_pairs=[[0, 1], [2, 3]],
        tag="links",
        skip_digestion=True,
    )
    view.shapes.add_pocket_surface(
        atom_indices=[0],
        tag="dropme",
        skip_digestion=True,
    )

    view.hide(selection=[2], skip_digestion=True)
    view.whole.hide(skip_digestion=True)

    apply_remove(view, selection=[0])

    assert view.regions["frag"].atom_indices == (0, 1)
    assert view.atom_mask is not None
    assert len(view.atom_mask) == 21
    assert bool(view.atom_mask[0]) is True
    assert bool(view.atom_mask[1]) is False

    ops = [msg.get("op") for msg in view._message_history]
    assert ops[:3] == ["clear_all", "load_molsys_payload", "hide_global"]

    create_region_msg = next(msg for msg in view._message_history if msg.get("op") == "create_region")
    assert create_region_msg["tag"] == "frag"
    assert create_region_msg["atom_indices"] == [0, 1]

    pocket_msg = next(
        msg
        for msg in view._message_history
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1]
    assert pocket_msg["options"]["mouth_atom_indices"] == [[0], [1, 2]]

    links_msg = next(
        msg
        for msg in view._message_history
        if msg.get("op") == "add_network_links" and msg.get("options", {}).get("tag") == "links"
    )
    assert links_msg["options"]["atom_pairs"] == [[1, 2]]

    assert {"op": "hide_layer", "tag": "pocket"} in view._message_history
    assert not any(
        msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "dropme"
        for msg in view._message_history
    )

    visibility_msg = next(msg for msg in reversed(view._message_history) if msg.get("op") == "update_visibility")
    assert visibility_msg["options"]["visible_atom_indices"] == [
        0,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
    ]


def test_remove_rebuild_remaps_and_replays_per_atom_colors():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    n_atoms = view.molsys.get_n_atoms()
    view.whole.set_color_by_values(
        values=list(range(n_atoms)),
        element="atom",
        palette=[0x111111, 0xEEEEEE],
        skip_digestion=True,
    )
    original_colors = dict(view._atom_color_map)  # noqa: SLF001

    apply_remove(view, selection=[0])

    expected_colors = {
        old_index - 1: color
        for old_index, color in original_colors.items()
        if old_index != 0
    }
    assert view._atom_color_map == expected_colors  # noqa: SLF001

    color_msg = next(msg for msg in view._message_history if msg.get("op") == "set_atom_colors")
    assert color_msg["replace"] is True
    assert color_msg["atom_indices"] == list(expected_colors.keys())
    assert color_msg["colors"] == list(expected_colors.values())


def test_remove_rebuild_remaps_dynamic_shape_frame_indices():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.shapes.add_sphere(
        structures_atom_indices=[[0, 1], [2, 3]],
        tag="moving-site",
        skip_digestion=True,
    )
    view.shapes.links.add_hbonds(
        structures=[[[0, 1], [2, 3]], None],
        tag="moving-hbonds",
        skip_digestion=True,
    )

    apply_remove(view, selection=[0])

    sphere_msg = next(
        msg
        for msg in view._shape_history  # noqa: SLF001
        if msg.get("op") == "add_sphere" and msg.get("options", {}).get("tag") == "moving-site"
    )
    assert sphere_msg["options"]["structures_atom_indices"] == [[0], [1, 2]]

    hbonds_msg = next(
        msg
        for msg in view._shape_history  # noqa: SLF001
        if msg.get("op") == "add_hbonds" and msg.get("options", {}).get("tag") == "moving-hbonds"
    )
    assert hbonds_msg["options"]["structures_atom_pairs"] == [[[1, 2]], None]


def test_remove_rebuild_drops_dynamic_shape_when_all_frames_are_orphaned():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.shapes.add_sphere(
        structures_atom_indices=[[0], None],
        tag="orphan-site",
        skip_digestion=True,
    )

    apply_remove(view, selection=[0])

    assert not any(
        msg.get("op") == "add_sphere" and msg.get("options", {}).get("tag") == "orphan-site"
        for msg in view._shape_history  # noqa: SLF001
    )
    assert "orphan-site" not in view._scene_objects  # noqa: SLF001
