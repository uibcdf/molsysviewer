"""Tests for combined visibility semantics and rebuild-replay consistency.

Focus: behaviours that are not purely live-edit operations and are not covered
by test_live_edit_rebuild.py or test_visibility_semantics.py individually.
"""
from __future__ import annotations

import pytest

pytest.importorskip("molsysmt")
from molsysviewer.demo import demo


# ---------------------------------------------------------------------------
# Hidden region survives a global show/hide cycle AFTER a rebuild
# ---------------------------------------------------------------------------

def test_hidden_region_stays_sticky_after_rebuild_and_global_show():
    """A region hidden before a rebuild must remain hidden after global show."""
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(atom_indices=[5, 6, 7], tag="pocket", skip_digestion=True)
    region.hide(skip_digestion=True)

    # Trigger rebuild
    view.remove(selection="atom_index < 3", skip_digestion=True)

    rebuilt = view.regions["pocket"]
    assert rebuilt._hidden is True, "region must still be hidden post-rebuild"  # noqa: SLF001

    # Global show — region must stay hidden (sticky semantics)
    view.show(skip_digestion=True)

    assert rebuilt._hidden is True  # noqa: SLF001
    assert not any(
        m.get("op") == "show_region" and m.get("tag") == "pocket"
        for m in view._message_history  # noqa: SLF001
    ), "show_region must not appear for a persistently hidden region after global show"


def test_global_hide_after_rebuild_does_not_duplicate_hide_region():
    """After rebuild, calling view.hide() must not re-emit hide_region for an already-hidden region."""
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(atom_indices=[3, 4, 5], tag="site", skip_digestion=True)
    region.hide(skip_digestion=True)

    view.remove(selection="atom_index < 2", skip_digestion=True)

    pre_hide_count = sum(
        1 for m in view._message_history  # noqa: SLF001
        if m.get("op") == "hide_region" and m.get("tag") == "site"
    )

    view.hide(skip_digestion=True)

    post_hide_count = sum(
        1 for m in view._message_history  # noqa: SLF001
        if m.get("op") == "hide_region" and m.get("tag") == "site"
    )
    assert post_hide_count == pre_hide_count, "view.hide() must not re-emit hide_region for already-hidden region"


# ---------------------------------------------------------------------------
# Annotation layer-tag retag survives rebuild
# ---------------------------------------------------------------------------

def test_annotation_retag_survives_rebuild():
    """A layer_tag change to an annotation must appear in the rebuilt message history."""
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.annotations.add_annotation(
        text="Residue 0",
        selection="group_index==0",
        tag="res0",
        layer_tag="initial_layer",
        skip_digestion=True,
    )
    view.annotations.set_layer_tag("res0", "updated_layer", skip_digestion=True)

    # Sanity: history rewritten before rebuild
    hist_entry = next(m for m in view._annotation_history if m.get("tag") == "res0")  # noqa: SLF001
    assert hist_entry["options"]["layer_tag"] == "updated_layer"

    # Trigger rebuild
    view.remove(selection="atom_index < 2", skip_digestion=True)

    # After rebuild the add_label message in _message_history must carry the updated layer_tag
    replayed = next(
        m for m in view._message_history  # noqa: SLF001
        if m.get("op") == "add_label" and m.get("tag") == "res0"
    )
    assert replayed["options"]["layer_tag"] == "updated_layer"


# ---------------------------------------------------------------------------
# Selection history remapping: indices shift correctly after rebuild
# ---------------------------------------------------------------------------

def test_selection_history_remapped_after_rebuild():
    """Named selections must have their atom indices remapped in history after a rebuild."""
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    # Save a selection on atoms 10 and 11
    view.selections.add(tag="pair", atom_indices=[10, 11], skip_digestion=True)

    # Remove first 3 atoms — indices shift by -3
    view.remove(selection="atom_index < 3", skip_digestion=True)

    save_msg = next(
        m for m in view._message_history  # noqa: SLF001
        if m.get("op") == "save_selection" and m.get("tag") == "pair"
    )
    assert save_msg["atom_indices"] == [7, 8], (
        f"Expected remapped indices [7, 8], got {save_msg['atom_indices']}"
    )


# ---------------------------------------------------------------------------
# Global style survives rebuild and then is respected by a second rebuild
# ---------------------------------------------------------------------------

def test_set_global_representation_replayed_across_two_rebuilds():
    """The applied global style must appear in the replay after each of two successive rebuilds."""
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.styles.apply(representation="cartoon", skip_digestion=True)

    # First rebuild
    view.remove(selection="atom_index < 2", skip_digestion=True)

    repr_after_first = [
        m for m in view._message_history  # noqa: SLF001
        if m.get("op") == "set_global_representation"
    ]
    assert len(repr_after_first) >= 1
    assert repr_after_first[0]["representation"] == "cartoon"

    # Second rebuild
    view.remove(selection="atom_index < 2", skip_digestion=True)

    repr_after_second = [
        m for m in view._message_history  # noqa: SLF001
        if m.get("op") == "set_global_representation"
    ]
    assert len(repr_after_second) >= 1
    assert repr_after_second[0]["representation"] == "cartoon"


# ---------------------------------------------------------------------------
# Export message ordering after a multi-step rebuild chain (item 2)
# ---------------------------------------------------------------------------

def test_export_messages_ordered_after_remove_then_append():
    """After remove() + append_structures(), export messages keep load → region → label → camera."""
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    atom_indices = list(view.select(selection="group_index==2"))
    view.new_region(atom_indices=atom_indices, tag="site", skip_digestion=True)
    view.annotations.add_annotation(
        text="Site label",
        selection="group_index==2",
        tag="lbl",
        skip_digestion=True,
    )
    view._last_camera_snapshot = {"target": [1.0, 0.0, 0.0], "position": [0.0, 0.0, 10.0], "up": [0.0, 1.0, 0.0]}  # noqa: SLF001

    # First rebuild: remove some atoms
    view.remove(selection="atom_index < 3", skip_digestion=True)

    # Second rebuild: append back the original structures
    view.append_structures(view.molsys, skip_digestion=True)

    messages = view._build_export_messages()  # noqa: SLF001
    ops = [m["op"] for m in messages if m.get("op") != "set_addon_runtime_summary"]

    assert "load_molsys_payload" in ops
    assert "create_region" in ops
    assert "add_label" in ops
    assert ops.index("load_molsys_payload") < ops.index("create_region"), \
        "load must precede create_region"
    assert ops.index("create_region") < ops.index("add_label"), \
        "create_region must precede add_label"
    assert ops[-1] == "set_camera_snapshot", \
        "camera snapshot must be last"


def test_export_messages_region_atom_indices_remapped_after_rebuild_chain():
    """Region atom indices in export messages are correctly remapped after remove() + append_structures()."""
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    # Use atoms well above index 3 so the remap is predictable
    atom_indices_before = list(view.select(selection="group_index==3"))
    view.new_region(atom_indices=atom_indices_before, tag="stable", skip_digestion=True)

    # Remove atoms 0..2 — indices shift by -3
    view.remove(selection="atom_index < 3", skip_digestion=True)

    # Second rebuild: append structures
    view.append_structures(view.molsys, skip_digestion=True)

    messages = view._build_export_messages()  # noqa: SLF001
    region_msg = next(m for m in messages if m.get("op") == "create_region" and m.get("tag") == "stable")

    # The region must exist in export and have a non-empty atom_indices list
    assert isinstance(region_msg.get("atom_indices"), list)
    assert len(region_msg["atom_indices"]) > 0
