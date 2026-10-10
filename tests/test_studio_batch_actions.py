"""Marked scene batches preserve identity, scientific analyses and atomic undo."""

import pytest
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv


@pytest.fixture
def view():
    result = msv.demo["pentalanine"]
    try:
        yield result
    finally:
        result.close()


def scene(view):
    return {
        k: v
        for k, v in view.export_state().items()
        if k not in {"order_high_water_mark", "uid_high_water_mark", "tag_high_water_marks"}
    }


def batch(view, domain, operation, tags):
    dispatch_panel_action(
        view,
        {
            "action": "batch_scene_objects",
            "domain": domain,
            "operation": operation,
            "tags": tags,
            "request_id": "batch",
        },
    )


@pytest.mark.parametrize(
    "domain", ["regions", "selections", "annotations", "measurements", "shapes", "layers", "interactions"]
)
def test_batch_delete_or_ungroup_is_one_undo_and_preserves_unmarked(view, domain):
    if domain == "interactions":
        view.interactions.hbonds.get_buch_hbonds(name="science", structure_indices=[0, 3])
    manager = getattr(view, domain)
    for i, tag in enumerate(["first", "second", "untouched"]):
        if domain == "regions":
            manager.add(atom_indices=[i], tag=tag)
        elif domain == "selections":
            manager.add(atom_indices=[i], tag=tag)
        elif domain == "annotations":
            manager.add(text=tag, atom_indices=[i], tag=tag)
        elif domain == "measurements":
            manager.add_distance([i], [i + 5], tag=tag)
        elif domain == "shapes":
            manager.add_sphere(atom_indices=[i], tag=tag)
        elif domain == "layers":
            manager.add(tag)
        else:
            manager.add("science", tag=tag)
    view.active_selection.set([10, 11])
    before = scene(view)
    batch(view, domain, "ungroup" if domain == "layers" else "delete", ["first", "second"])
    assert "untouched" in manager.tags() and "first" not in manager.tags() and "second" not in manager.tags()
    assert view.active_selection.atom_indices == [10, 11]
    if domain == "interactions":
        assert view.interactions.get_analysis("science") is not None
    assert view.history.undo()
    assert scene(view) == before
    assert view.history.redo()
    assert "first" not in getattr(view, domain).tags()


def test_validation_rejects_entire_batch_before_mutation_and_preserves_redo(view):
    view.regions.add(atom_indices=[0], tag="first")
    view.regions.add(atom_indices=[1], tag="other")
    view.history.undo()
    before = scene(view)
    with pytest.raises(ValueError, match="no longer exists"):
        batch(view, "regions", "delete", ["first", "missing"])
    assert scene(view) == before and view.history.can_redo()


def test_atomic_boundary_rolls_back_a_real_operation_failure(view):
    view.regions.add(atom_indices=[0], tag="first")
    before = scene(view)
    with pytest.raises(ValueError):
        with view.history._atomic_operation(("review", "rollback")):
            view.regions["first"].hide()
            batch(view, "regions", "delete", ["missing"])
    assert scene(view) == before


def test_batch_visibility_and_layer_ungroup_keep_members(view):
    for tag in ["first", "second"]:
        view.shapes.add_sphere(atom_indices=[0], tag=tag)
    layer = view.layers.add("presentation")
    layer.attach(view.shapes.get("first"))
    batch(view, "shapes", "hide", ["first", "second"])
    assert not view.shapes.info("first")["visible"] and not view.shapes.info("second")["visible"]
    batch(view, "shapes", "show", ["first", "second"])
    assert view.shapes.info("first")["visible"]
    batch(view, "layers", "ungroup", ["presentation"])
    assert view.shapes.get("first") is not None
