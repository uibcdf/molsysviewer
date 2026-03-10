from __future__ import annotations

import pytest

pytest.importorskip("molsysmt")

from molsysviewer.demo import demo


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

    view.append_structures(demo["dialanine"]._molsys, skip_digestion=True)  # noqa: SLF001

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

    view.remove(selection=[0], skip_digestion=True)

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
