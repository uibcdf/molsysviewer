from __future__ import annotations

from molsysviewer.demo import demo


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def _scene(state):
    """The reproducible scene content, minus the monotonic high-water marks.
    Undo restores the scene but never rolls the uid/order counters back (that
    would let a later create collide with a redo-able snapshot)."""
    return {k: v for k, v in state.items()
            if k not in ("order_high_water_mark", "uid_high_water_mark")}


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


def test_undo_absorbs_active_selection_changes():
    view = _mute(demo["dialanine"])
    view.active_selection.set([0, 1, 2], syntax="Indices", skip_digestion=True)
    view.active_selection.set([5, 6], syntax="Indices", skip_digestion=True)
    assert sorted(view.active_selection.atom_indices) == [5, 6]
    view.history.undo()
    assert sorted(view.active_selection.atom_indices) == [0, 1, 2]
