from __future__ import annotations

import pytest

from molsysviewer import MolSysView
from _edit_helpers import apply_remove


# ---------------------------------------------------------------------------
# reset_viewer / clear_all
# ---------------------------------------------------------------------------

def test_reset_viewer_sends_clear_all_op():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.reset_viewer(skip_digestion=True)

    ops = [m.get("op") for m in view._message_history]  # noqa: SLF001
    assert "clear_all" in ops


def test_reset_viewer_clears_internal_histories():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    # Inject fake history entries directly to simulate a loaded state
    view._shape_history.append({"op": "add_sphere", "tag": "s1", "options": {}})  # noqa: SLF001
    view._annotation_history.append({"op": "add_label", "tag": "a1", "options": {}})  # noqa: SLF001
    view._measurement_history.append({"op": "add_distance_measurement", "tag": "d1", "options": {}})  # noqa: SLF001
    assert len(view._shape_history) == 1  # noqa: SLF001

    view.reset_viewer(skip_digestion=True)

    assert len(view._shape_history) == 0  # noqa: SLF001
    assert len(view._annotation_history) == 0  # noqa: SLF001
    assert len(view._measurement_history) == 0  # noqa: SLF001
    assert len(view._regions) == 0  # noqa: SLF001
    assert len(view._layers) == 0  # noqa: SLF001


def test_reset_viewer_last_message_is_clear_all():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.reset_viewer(skip_digestion=True)

    # _message_history is an append-only log; reset appends clear_all last
    assert view._message_history[-1]["op"] == "clear_all"  # noqa: SLF001


# ---------------------------------------------------------------------------
# clear_decorations → clear_scene op
# ---------------------------------------------------------------------------

def test_clear_decorations_sends_clear_scene_op_with_correct_flags():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.clear_decorations(shapes=True, styles=False, labels=False, skip_digestion=True)

    last = view._message_history[-1]  # noqa: SLF001
    assert last["op"] == "clear_scene"
    assert last["options"]["shapes"] is True
    assert last["options"]["styles"] is False
    assert last["options"]["labels"] is False


def test_clear_decorations_all_flags_true():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.clear_decorations(shapes=True, styles=True, labels=True, skip_digestion=True)

    last = view._message_history[-1]  # noqa: SLF001
    assert last["op"] == "clear_scene"
    assert last["options"] == {"shapes": True, "styles": True, "labels": True}


def test_clear_decorations_clears_shape_history_when_shapes_true():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view._shape_history.append({"op": "add_sphere", "tag": "s1", "options": {}})  # noqa: SLF001
    assert len(view._shape_history) == 1  # noqa: SLF001

    view.clear_decorations(shapes=True, styles=False, labels=False, skip_digestion=True)

    assert len(view._shape_history) == 0  # noqa: SLF001


def test_clear_decorations_preserves_shape_history_when_shapes_false():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view._shape_history.append({"op": "add_sphere", "tag": "s1", "options": {}})  # noqa: SLF001

    view.clear_decorations(shapes=False, styles=True, labels=False, skip_digestion=True)

    assert len(view._shape_history) == 1  # noqa: SLF001


# ---------------------------------------------------------------------------
# Layer retag — requires molsysmt for annotation/measurement creation
# ---------------------------------------------------------------------------

pytest.importorskip("molsysmt")
from molsysviewer.demo import demo  # noqa: E402


def test_annotation_set_layer_tag_rewrites_annotation_history():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.annotations.add_annotation(
        text="Site A",
        selection="group_index==0",
        tag="siteA",
        layer_tag="old_group",
        skip_digestion=True,
    )

    orig = next(m for m in view._annotation_history if m.get("tag") == "siteA")  # noqa: SLF001
    assert orig["options"]["layer_tag"] == "old_group"

    view.annotations.set_layer_tag("siteA", "new_group", skip_digestion=True)

    # Python object updated
    assert view.annotations["siteA"].layer_tag == "new_group"

    # Annotation history rewritten
    updated = next(m for m in view._annotation_history if m.get("tag") == "siteA")  # noqa: SLF001
    assert updated["options"]["layer_tag"] == "new_group"

    # No `retag_layer` op emitted — layer_tag is a pure history rewrite
    ops = [m.get("op") for m in view._message_history]  # noqa: SLF001
    assert "retag_layer" not in ops


def test_measurement_set_layer_tag_rewrites_measurement_history():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.measurements.add_distance(
        selection_a="atom_index==0",
        selection_b="atom_index==1",
        tag="d01",
        layer_tag="layer_old",
        skip_digestion=True,
    )

    view.measurements.set_layer_tag("d01", "layer_new", skip_digestion=True)

    assert view.measurements["d01"].layer_tag == "layer_new"

    updated = next(m for m in view._measurement_history if m.get("tag") == "d01")  # noqa: SLF001
    assert updated["options"]["layer_tag"] == "layer_new"


# ---------------------------------------------------------------------------
# set_global_representation replay after rebuild
# ---------------------------------------------------------------------------

def test_set_global_representation_survives_rebuild():
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.styles.apply(representation="cartoon", skip_digestion=True)
    before_ops = [m.get("op") for m in view._message_history]  # noqa: SLF001
    assert "set_global_representation" in before_ops

    apply_remove(view, selection="atom_index < 3")

    repr_msgs = [m for m in view._message_history if m.get("op") == "set_global_representation"]  # noqa: SLF001
    assert len(repr_msgs) >= 1, "set_global_representation must appear in replayed history"
    assert repr_msgs[0]["representation"] == "cartoon"


def test_global_hidden_state_replayed_after_rebuild():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.hide(skip_digestion=True)
    assert view._global_hidden is True  # noqa: SLF001

    apply_remove(view, selection="atom_index < 2")

    assert view._global_hidden is True  # noqa: SLF001
    hide_ops = [m for m in view._message_history if m.get("op") == "hide_global"]  # noqa: SLF001
    assert len(hide_ops) >= 1, "hide_global must be re-emitted after rebuild"


def test_hidden_region_state_replayed_after_rebuild():
    view = demo["pentalanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(atom_indices=[5, 6, 7], tag="pocket", representation="line", skip_digestion=True)
    region.hide(skip_digestion=True)
    assert region._hidden is True  # noqa: SLF001

    apply_remove(view, selection="atom_index < 3")

    rebuilt_region = view.regions.get("pocket")
    assert rebuilt_region is not None
    assert rebuilt_region._hidden is True  # noqa: SLF001
