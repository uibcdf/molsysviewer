from __future__ import annotations

import pytest

from molsysviewer.demo import demo
from molsysviewer import pyunitwizard as puw


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def _scene(state):
    """The reproducible scene content, minus the monotonic high-water marks.
    Undo restores the scene but never rolls the uid/order counters back (that
    would let a later create collide with a redo-able snapshot)."""
    return {k: v for k, v in state.items()
            if k not in ("order_high_water_mark", "uid_high_water_mark", "tag_high_water_marks")}


def test_undo_restores_prior_scene_compared_via_export_state():
    view = _mute(demo["dialanine"])
    before = view.export_state()
    a = view.regions.add(atom_indices=[0, 1, 2], tag="A", skip_digestion=True)
    a.set_representation("spacefill", skip_digestion=True)
    assert _scene(view.export_state()) != _scene(before)

    view.history.undo()  # undo set_representation
    view.history.undo()  # undo the add
    # The acceptance criterion: the scene matches the prior export_state exactly.
    assert _scene(view.export_state()) == _scene(before)


def test_undo_redo_walks_each_mutating_operation():
    view = _mute(demo["dialanine"])
    view.regions.add(atom_indices=[0, 1, 2], tag="A", skip_digestion=True)
    view.regions.add(atom_indices=[3, 4], tag="B", skip_digestion=True)
    assert sorted(view.regions.tags()) == ["A", "B"]

    assert view.history.undo() and sorted(view.regions.tags()) == ["A"]
    assert view.history.undo() and view.regions.tags() == []
    assert view.history.redo() and sorted(view.regions.tags()) == ["A"]
    assert view.history.redo() and sorted(view.regions.tags()) == ["A", "B"]


def test_a_new_operation_clears_the_redo_stack():
    view = _mute(demo["dialanine"])
    view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    view.regions.add(atom_indices=[2, 3], tag="B", skip_digestion=True)
    view.history.undo()  # B gone, redo has B
    assert view.history.can_redo()
    view.regions.add(atom_indices=[4, 5], tag="C", skip_digestion=True)  # new branch
    assert not view.history.can_redo()


def test_composite_operation_is_a_single_undo_step():
    view = _mute(demo["dialanine"])
    a = view.regions.add(atom_indices=[0, 1, 2, 3], tag="A", skip_digestion=True)
    b = view.regions.add(atom_indices=[2, 3, 4], tag="B", skip_digestion=True)
    baseline = view.export_state()
    # union with a representation internally creates a region AND sets its
    # representation (a nested decorated call); it must be one undo step.
    a.union(b, tag="U", representation="cartoon", skip_digestion=True)
    assert "U" in view.regions and view.regions["U"].representation == "cartoon"
    view.history.undo()
    assert "U" not in view.regions
    assert _scene(view.export_state()) == _scene(baseline)


def test_undo_restores_the_active_selection():
    view = _mute(demo["dialanine"])
    view.active_selection.set([0, 1, 2], syntax="Indices", skip_digestion=True)
    assert sorted(view.active_selection.atom_indices) == [0, 1, 2]
    view.active_selection.set([5, 6], syntax="Indices", skip_digestion=True)

    state = view.export_state()
    assert state["active_selection"]["atom_indices"] == [5, 6]

    fresh = _mute(demo["dialanine"])
    fresh.import_state(state)
    assert sorted(fresh.active_selection.atom_indices) == [5, 6]


def test_apply_system_edit_invalidates_history():
    view = _mute(demo["dialanine"])
    view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    assert view.history.can_undo()
    n = int(view.molsys.get_n_atoms())
    view.apply_system_edit(view.molsys, atom_index_map={i: i for i in range(n)}, skip_digestion=True)
    assert not view.history.can_undo()


def test_history_is_not_serialised_into_state():
    view = _mute(demo["dialanine"])
    view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    state = view.export_state()
    assert "history" not in state


def test_history_stores_compact_json_checkpoints_without_changing_undo_semantics():
    view = _mute(demo["dialanine"])
    view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)

    assert isinstance(view.history._undo[-1], bytes)  # noqa: SLF001
    assert view.history.undo()
    assert view.regions.tags() == []


def test_history_byte_budget_discards_oldest_checkpoints_observably():
    view = _mute(demo["dialanine"])
    view.history._byte_limit = 2048  # noqa: SLF001

    with pytest.warns(RuntimeWarning, match="storage budget"):
        for index in range(10):
            view.active_selection.set(
                [index], syntax="Indices", skip_digestion=True
            )

    retained = view.history._undo_bytes + view.history._redo_bytes  # noqa: SLF001
    assert retained <= view.history._byte_limit  # noqa: SLF001
    assert 0 < len(view.history._undo) < 10  # noqa: SLF001
    assert view.active_selection.atom_indices == [9]
    assert view.history.undo()
    assert view.active_selection.atom_indices != [9]


def test_history_byte_budget_counts_undo_and_redo_together():
    view = _mute(demo["dialanine"])
    for index in range(6):
        view.active_selection.set(
            [index], syntax="Indices", skip_digestion=True
        )

    checkpoint_size = max(len(snapshot) for snapshot in view.history._undo)  # noqa: SLF001
    view.history._byte_limit = checkpoint_size * 3  # noqa: SLF001
    with pytest.warns(RuntimeWarning, match="storage budget"):
        assert view.history.undo()

    retained = view.history._undo_bytes + view.history._redo_bytes  # noqa: SLF001
    assert retained <= view.history._byte_limit  # noqa: SLF001
    assert view.history.can_redo()


def test_undo_absorbs_active_selection_changes():
    view = _mute(demo["dialanine"])
    view.active_selection.set([0, 1, 2], syntax="Indices", skip_digestion=True)
    view.active_selection.set([5, 6], syntax="Indices", skip_digestion=True)
    assert sorted(view.active_selection.atom_indices) == [5, 6]
    view.history.undo()
    assert sorted(view.active_selection.atom_indices) == [0, 1, 2]


def _pick(view, indices):
    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_active_selection_changed",
        "atom_indices": list(indices),
    })


def test_frontend_pick_is_checkpointed_and_undoable():
    view = _mute(demo["dialanine"])
    _pick(view, [0, 1, 2])
    assert sorted(view.active_selection.atom_indices) == [0, 1, 2]
    assert view.history.can_undo()
    _pick(view, [5, 6])
    assert sorted(view.active_selection.atom_indices) == [5, 6]

    # Undo, driven through the single scene history via the frontend event.
    view._handle_frontend_event({"event": "scene_history_undo"})  # noqa: SLF001
    assert sorted(view.active_selection.atom_indices) == [0, 1, 2]


def test_unchanged_pick_echo_does_not_add_a_history_entry():
    view = _mute(demo["dialanine"])
    _pick(view, [0, 1, 2])
    depth = len(view.history._undo)  # noqa: SLF001
    # An echo of the same selection (what a Python-driven set produces) must not
    # add a spurious checkpoint.
    _pick(view, [0, 1, 2])
    assert len(view.history._undo) == depth  # noqa: SLF001


def test_history_state_is_pushed_to_the_frontend():
    view = _mute(demo["dialanine"])
    pushed = []
    view._send_runtime_only = lambda m: pushed.append(m)  # noqa: SLF001
    view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    states = [m for m in pushed if m.get("op") == "set_history_state"]
    assert states and states[-1]["can_undo"] is True


def test_a_slider_drag_does_not_wipe_the_undo_history():
    view = _mute(demo["dialanine"])
    view.regions.add(atom_indices=[0, 1], tag="r1", skip_digestion=True)
    view.regions.add(atom_indices=[2, 3], tag="r2", skip_digestion=True)
    shape = view.shapes.add_sphere(tag="sphere1", alpha=0.2, skip_digestion=True)
    assert len(view.history._undo) == 3  # noqa: SLF001

    with view.history.coalescing():
        for step in range(40):
            shape.set_alpha(step / 40, skip_digestion=True)

    assert len(view.history._undo) == 4  # noqa: SLF001
    assert view.history.undo()
    assert view.shapes.records()[0]["options"]["alpha"] == 0.2
    assert view.history.undo()
    assert view.shapes.tags() == []
    assert view.history.undo()
    assert view.regions.tags() == ["r1"]
    assert view.history.undo()
    assert view.regions.tags() == []


def test_typing_a_label_does_not_wipe_the_undo_history():
    view = _mute(demo["dialanine"])
    view.regions.add(atom_indices=[0, 1], tag="r1", skip_digestion=True)
    view.regions.add(atom_indices=[2, 3], tag="r2", skip_digestion=True)
    view.annotations.add("x", atom_indices=[0], tag="a1", skip_digestion=True)
    assert len(view.history._undo) == 3  # noqa: SLF001

    text = "catalytic triad"
    with view.history.coalescing():
        for index in range(1, len(text) + 1):
            view.annotations.set_text("a1", text[:index], skip_digestion=True)

    assert len(view.history._undo) == 4  # noqa: SLF001
    assert view.annotations.info("a1")["text"] == text
    assert view.history.undo()
    assert view.annotations.info("a1")["text"] == "x"


def test_coalescing_keeps_distinct_operations_as_distinct_undo_steps():
    view = _mute(demo["dialanine"])
    shape = view.shapes.add_sphere(tag="sphere1", radius="1.0 nm", alpha=0.2, skip_digestion=True)
    view.history.clear()

    with view.history.coalescing():
        shape.set_alpha(0.4, skip_digestion=True)
        shape.set_alpha(0.8, skip_digestion=True)
        shape.set_radius("1.5 nm", skip_digestion=True)
        shape.set_radius("2.0 nm", skip_digestion=True)

    assert len(view.history._undo) == 2  # noqa: SLF001
    assert view.history.undo()
    expected_radius = puw.get_value(puw.quantity(1.0, "nm"), to_unit="angstroms")
    assert view.shapes.records()[0]["options"]["radius"] == expected_radius
    assert view.history.undo()
    assert view.shapes.records()[0]["options"]["alpha"] == 0.2


def test_coalescing_keeps_same_tag_shape_and_layer_in_distinct_domains():
    view = _mute(demo["dialanine"])
    shape = view.shapes.add_sphere(tag="shared", skip_digestion=True)
    layer = view.layers["shared"]
    view.history.clear()

    with view.history.coalescing():
        shape.hide(skip_digestion=True)
        layer.hide(skip_digestion=True)

    assert len(view.history._undo) == 2  # noqa: SLF001


def test_scene_object_domains_are_restored_by_undo():
    view = _mute(demo["dialanine"])
    view.annotations.add_annotation(text="site", atom_indices=[0], tag="note", skip_digestion=True)
    view.measurements.add_distance([0], [1], tag="distance", skip_digestion=True)
    view.shapes.add_sphere(tag="sphere", skip_digestion=True)
    view.layers.add("analysis", skip_digestion=True)
    view.history.clear()

    view.annotations.delete("note", skip_digestion=True)
    assert not view.annotations.contains("note", skip_digestion=True)
    assert view.history.undo()
    assert view.annotations.contains("note", skip_digestion=True)

    view.measurements.delete("distance", skip_digestion=True)
    assert not view.measurements.contains("distance", skip_digestion=True)
    assert view.history.undo()
    assert view.measurements.contains("distance", skip_digestion=True)

    view.shapes.delete("sphere", skip_digestion=True)
    assert not view.shapes.contains("sphere", skip_digestion=True)
    assert view.history.undo()
    assert view.shapes.contains("sphere", skip_digestion=True)

    view.layers.delete("analysis", skip_digestion=True)
    assert not view.layers.contains("analysis", skip_digestion=True)
    assert view.history.undo()
    assert view.layers.contains("analysis", skip_digestion=True)


def test_specialized_shape_and_interactive_measurement_paths_enter_history():
    view = _mute(demo["dialanine"])
    view.shapes.spheres.add_sphere(tag="specialized", skip_digestion=True)
    assert view.history.undo()
    assert not view.shapes.contains("specialized", skip_digestion=True)

    view.history.clear()
    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_measurement_created",
        "action": "distance",
        "picked_count": 2,
        "picks_atom_indices": [[0], [1]],
    })
    assert view.measurements.contains("measurement1", skip_digestion=True)
    assert view.history.undo()
    assert not view.measurements.contains("measurement1", skip_digestion=True)
