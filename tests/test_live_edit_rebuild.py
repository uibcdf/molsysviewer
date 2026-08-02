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

    view.regions.add(
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

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 21

    links_msg = next(
        msg
        for msg in view._test_message_log
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

    region = view.regions.add(
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

    ops = [msg.get("op") for msg in view._test_message_log]
    assert ops[:2] == ["clear_all", "load_molsys_payload"]

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is True
    assert len(payload_msg["payload"]["structures"]) == 2

    create_region_msg = next(msg for msg in view._test_message_log if msg.get("op") == "create_region")
    assert create_region_msg["tag"] == "frag"
    assert create_region_msg["atom_indices"] == [0, 1, 2]

    pocket_msg = next(
        msg
        for msg in view._test_message_log
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1, 2]

    assert {"op": "hide_layer", "tag": "pocket", "kind": "shape"} in view._test_message_log
    assert {"op": "hide_region", "tag": "frag"} in view._test_message_log


def test_load_mode_append_structures_delegates_to_append_path():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys, mode="append_structures", skip_digestion=True)  # noqa: SLF001

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
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

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is False
    assert len(payload_msg["payload"]["structures"]) == 1


def test_load_mode_auto_replaces_on_empty_view():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys, mode="auto", skip_digestion=True)  # noqa: SLF001

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is False
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 22
    assert len(view._load_blocks) == 1  # noqa: SLF001


def test_load_mode_auto_appends_when_input_has_same_atom_count_and_no_topology():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(demo["dialanine"]._molsys.structures.copy(), mode="auto", skip_digestion=True)  # noqa: SLF001

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
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

    region = view.regions.add(
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

    ops = [msg.get("op") for msg in view._test_message_log]
    assert ops[:2] == ["clear_all", "load_molsys_payload"]

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is False
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 44
    assert len(payload_msg["payload"]["structures"]) == 1

    create_region_msg = next(msg for msg in view._test_message_log if msg.get("op") == "create_region")
    assert create_region_msg["tag"] == "frag"
    assert create_region_msg["atom_indices"] == [0, 1, 2]

    pocket_msg = next(
        msg
        for msg in view._test_message_log
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1, 2]

    assert {"op": "hide_layer", "tag": "pocket", "kind": "shape"} in view._test_message_log
    assert {"op": "hide_region", "tag": "frag"} in view._test_message_log

    visibility_msg = next(msg for msg in reversed(view._test_message_log) if msg.get("op") == "update_visibility")
    assert visibility_msg["options"]["visible_atom_indices"] == list(range(22))


def test_set_rebuild_updates_group_name_and_preserves_hidden_state():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.regions.add(
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

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    assert payload_msg["payload"]["atoms"]["residue_name"][:5] == ["ACE2"] * 5

    assert {"op": "hide_layer", "tag": "pocket", "kind": "shape"} in view._test_message_log
    assert {"op": "hide_region", "tag": "frag"} in view._test_message_log


def test_apply_system_edit_replays_visual_region_as_bare_create_then_style():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.regions.add(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        alpha=0.4,
        skip_digestion=True,
    )

    apply_set(view, element="group", selection=[0], group_name="ACE2")

    region_ops = [
        msg for msg in view._test_message_log  # noqa: SLF001
        if msg.get("tag") == "frag"
        and msg.get("op") in {"create_region", "set_region_representation"}
    ]
    assert [msg["op"] for msg in region_ops] == ["create_region", "set_region_representation"]

    create_msg = region_ops[0]
    assert create_msg["atom_indices"] == [0, 1, 2]
    assert "representation" not in create_msg
    assert "params" not in create_msg

    style_msg = region_ops[1]
    assert style_msg["representation"] == "ball-and-stick"
    assert style_msg["params"] == {"alpha": 0.4}


def test_set_rebuild_updates_coordinates_with_quantity():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.regions.add(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    original_payload = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    original_first = original_payload["payload"]["structures"][0]["coordinates"][0]

    apply_set(
        view,
        element="atom",
        selection=[0],
        coordinates=puw.quantity([[[0.1, 0.2, 0.3]]], "nm"),
    )

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    updated_first = payload_msg["payload"]["structures"][0]["coordinates"][0]

    assert updated_first != original_first
    assert updated_first == pytest.approx([1.0, 2.0, 3.0])
    assert view.regions["frag"].atom_indices == (0, 1, 2)
    assert {"op": "hide_region", "tag": "frag"} in view._test_message_log


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

    region = view.regions.add(
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

    ops = [msg.get("op") for msg in view._test_message_log]
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

    payload_msg = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")
    assert payload_msg["multiple_structures"] is True
    assert len(payload_msg["payload"]["structures"]) == 2
    assert len(payload_msg["payload"]["atoms"]["atom_id"]) == 21
    assert payload_msg["payload"]["atoms"]["residue_name"][:5] == ["ACE2"] * 5

    create_region_msg = next(msg for msg in view._test_message_log if msg.get("op") == "create_region")
    assert create_region_msg["atom_indices"] == [0, 1]
    assert view.regions["frag"].atom_indices == (0, 1)

    pocket_msg = next(
        msg
        for msg in view._test_message_log
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1]

    visibility_msg = next(msg for msg in reversed(view._test_message_log) if msg.get("op") == "update_visibility")
    assert visibility_msg["options"]["visible_atom_indices"] == list(range(21))



def test_remove_rebuild_drops_orphaned_regions_and_shapes_but_keeps_anchored_objects_broken():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.regions.add(atom_indices=[0], tag="orphan-region", skip_digestion=True)
    view.shapes.add_pocket_surface(atom_indices=[0], tag="orphan-shape", skip_digestion=True)
    view.annotations.add_annotation(text="orphan", atom_indices=[0], tag="orphan-label", skip_digestion=True)
    view.measurements.add_distance([0], [1], tag="orphan-distance", skip_digestion=True)

    apply_remove(view, selection=[0])

    assert "orphan-region" not in list(view.regions)
    assert "orphan-shape" not in view.shapes.tags(skip_digestion=True)
    assert "orphan-label" in view.annotations.tags()
    assert "orphan-distance" in view.measurements.tags(skip_digestion=True)
    assert ("shape", "orphan-shape") not in view._scene_objects  # noqa: SLF001
    assert view.annotations.info("orphan-label")["broken"] is True
    assert view.measurements.info("orphan-distance")["broken"] is True

    assert not any(msg.get("tag") == "orphan-region" for msg in view._test_message_log)  # noqa: SLF001
    assert not any(
        msg.get("options", {}).get("tag") in {"orphan-shape", "orphan-label", "orphan-distance"}
        for msg in view._test_message_log  # noqa: SLF001
    )


def test_an_annotation_whose_anchor_is_deleted_survives_as_broken_not_as_nothing():
    view = demo["dialanine"]
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[attr-defined]
    last_atom = int(view.molsys.get_n_atoms()) - 1
    view.annotations.add("terminal", atom_indices=[last_atom], tag="a1")

    apply_remove(view, selection=[last_atom])

    assert "a1" in view.annotations.tags()
    record = view.annotations.info("a1")
    assert record["broken"] is True
    assert str(last_atom) in record["broken_reason"]
    document_record = next(item for item in view.export_state()["annotations"] if item["tag"] == "a1")
    assert document_record["broken"] is True
    assert document_record["broken_reason"] == record["broken_reason"]
    summary = next(
        msg for msg in reversed(sent) if msg.get("op") == "set_annotation_summaries"
    )["annotations"][0]
    assert summary["broken"] is True
    assert summary["broken_reason"] == record["broken_reason"]

    view.annotations.set_anchor("a1", atom_indices=[0])
    healed = view.annotations.info("a1")
    assert healed["broken"] is False
    assert healed["broken_reason"] is None
    healed_record = next(item for item in view.annotations.records() if item["tag"] == "a1")
    assert healed_record["broken"] is False
    assert healed_record["broken_reason"] is None


def test_a_partially_remapped_measurement_never_reports_the_old_number():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.measurements.add_distance([0, 1, 2, 3, 4], [10, 11, 12], tag="c1")
    stale_value = view.measurements.info("c1")["value"]

    apply_remove(view, selection=[3, 4])

    record = view.measurements.info("c1")
    assert record["broken"] is False
    assert record["value"] is not None
    assert record["value"] != stale_value

    view.measurements.add_distance([0, 1, 2], [8, 9, 10], tag="expected")
    assert record["value"] == view.measurements.info("expected")["value"]


def test_a_destroyed_measurement_anchor_serializes_without_a_stale_value():
    view = demo["dialanine"]
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[attr-defined]
    last_atom = int(view.molsys.get_n_atoms()) - 1
    view.measurements.add_distance([0], [last_atom], tag="d1")
    stale_value = view.measurements.info("d1")["value"]
    assert stale_value is not None

    apply_remove(view, selection=[last_atom])

    record = view.measurements.info("d1")
    assert record["broken"] is True
    assert record["value"] is None
    document_record = next(item for item in view.export_state()["measurements"] if item["tag"] == "d1")
    assert document_record["broken"] is True
    assert "value" not in document_record["options"]
    assert "value_series" not in document_record["options"]
    summary = next(
        msg for msg in reversed(sent) if msg.get("op") == "set_measurement_summaries"
    )["measurements"][0]
    assert summary["broken"] is True
    assert summary["value"] is None


def test_a_broken_object_becomes_valid_again_after_undo_snapshot_restore():
    source = demo["dialanine"]
    source.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    last_atom = int(source.molsys.get_n_atoms()) - 1
    source.measurements.add_distance([0], [last_atom], tag="d1")
    original_value = source.measurements.info("d1")["value"]
    pre_edit_snapshot = source.export_state()

    apply_remove(source, selection=[last_atom])
    assert source.measurements.info("d1")["broken"] is True

    restored = demo["dialanine"]
    restored.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    restored.import_state(pre_edit_snapshot)
    record = restored.measurements.info("d1")
    assert record["broken"] is False
    assert record["value"] == original_value


def test_canonical_export_after_live_edit_chain_reflects_current_state(monkeypatch):
    monkeypatch.setenv("NUMBA_CACHE_DIR", "/tmp/numba_cache")

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.regions.add(
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

    exported = view._build_export_messages()  # noqa: SLF001
    ops = [msg.get("op") for msg in exported]

    assert ops.count("load_molsys_payload") == 1
    assert ops.count("create_region") == 1
    assert "set_region_representation" not in ops
    assert "hide_region" in ops
    assert "add_pocket_surface" in ops
    assert "hide_layer" in ops
    assert ops.index("create_region") < ops.index("hide_region")
    assert ops.index("add_pocket_surface") < ops.index("hide_layer")

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

    visibility = next(msg for msg in exported if msg.get("op") == "update_visibility")
    assert visibility["options"]["visible_atom_indices"] == view.visible_atom_indices


def test_remove_rebuild_remaps_regions_shapes_and_visibility():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.regions.add(
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

    ops = [msg.get("op") for msg in view._test_message_log]
    assert ops[:3] == ["clear_all", "load_molsys_payload", "hide_whole"]

    create_region_msg = next(msg for msg in view._test_message_log if msg.get("op") == "create_region")
    assert create_region_msg["tag"] == "frag"
    assert create_region_msg["atom_indices"] == [0, 1]

    pocket_msg = next(
        msg
        for msg in view._test_message_log
        if msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "pocket"
    )
    assert pocket_msg["options"]["atom_indices"] == [0, 1]
    assert pocket_msg["options"]["mouth_atom_indices"] == [[0], [1, 2]]

    links_msg = next(
        msg
        for msg in view._test_message_log
        if msg.get("op") == "add_network_links" and msg.get("options", {}).get("tag") == "links"
    )
    assert links_msg["options"]["atom_pairs"] == [[1, 2]]

    assert {"op": "hide_layer", "tag": "pocket", "kind": "shape"} in view._test_message_log
    assert not any(
        msg.get("op") == "add_pocket_surface" and msg.get("options", {}).get("tag") == "dropme"
        for msg in view._test_message_log
    )

    visibility_msg = next(msg for msg in reversed(view._test_message_log) if msg.get("op") == "update_visibility")
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

    color_msg = next(msg for msg in view._test_message_log if msg.get("op") == "set_atom_colors")
    assert color_msg["replace"] is True
    assert color_msg["atom_indices"] == list(expected_colors.keys())
    assert color_msg["colors"] == list(expected_colors.values())


def test_remove_rebuild_preserves_hidden_styled_whole():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.set_representation("cartoon", skip_digestion=True)
    view.whole.hide(skip_digestion=True)

    apply_remove(view, selection=[0])

    assert view.whole.visible is False
    ops = [msg.get("op") for msg in view._test_message_log]
    assert ops[:2] == ["clear_all", "load_molsys_payload"]
    assert "set_whole_representation" in ops
    assert ops.index("hide_whole") > ops.index("set_whole_representation")


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
    assert ("shape", "orphan-site") not in view._scene_objects  # noqa: SLF001
