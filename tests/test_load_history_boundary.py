"""Scene-only Undo/Redo must not cross a molecular load/reset boundary."""

import molsysmt as msm
import pytest

import molsysviewer as msv


@pytest.fixture
def source():
    with msv.demo["dialanine"] as view:
        yield msm.extract(view.molsys, structure_indices=[0])


def _populate_both_stacks(view):
    view.annotations.add("before", atom_indices=[0], tag="old-note")
    view.annotations.set_text("old-note", "edited")
    view.annotations.set_text("old-note", "future")
    assert view.history.undo()
    assert view.annotations.info("old-note")["text"] == "edited"
    assert view.history.can_undo() and view.history.can_redo()


def _assert_history_empty(view):
    assert not view.history.can_undo()
    assert not view.history.can_redo()
    assert not view.history.undo()
    assert not view.history.redo()


@pytest.mark.parametrize("multiple", [False, True])
@pytest.mark.parametrize("skip_digestion", [False, True])
def test_replacement_discards_previous_system_history(source, multiple, skip_digestion):
    with msv.new_view(source) as view:
        _populate_both_stacks(view)
        incoming = [source, source] if multiple else source
        view.load(incoming, multiple=multiple, mode="replace", skip_digestion=skip_digestion)

        assert view.molsys.get_n_atoms() == source.get_n_atoms() * (2 if multiple else 1)
        assert view.annotations.count() == 0
        _assert_history_empty(view)
        assert view.annotations.count() == 0
        assert len(view.regions) == (2 if multiple else 0)

        # The new system still gets its own ordinary scene history.
        view.annotations.add("new", atom_indices=[0], tag="new-note")
        assert view.history.undo()
        assert view.annotations.count() == 0
        assert view.history.redo()
        assert view.annotations.info("new-note")["text"] == "new"
        assert "old-note" not in view.annotations.tags()


@pytest.mark.parametrize("multiple", [False, True])
@pytest.mark.parametrize("skip_digestion", [False, True])
def test_rejected_replacement_preserves_undo_and_redo(source, tmp_path, multiple, skip_digestion):
    invalid = tmp_path / "invalid.h5msm"
    invalid.write_bytes(b"not an H5MSM file")
    with msv.new_view(source) as view:
        _populate_both_stacks(view)
        previous_system = view.molsys
        previous_scene = view.export_state()
        previous_sources = view.load_blocks
        undo, redo = list(view.history._undo), list(view.history._redo)
        incoming = [source, str(invalid)] if multiple else str(invalid)
        with pytest.raises(OSError):
            view.load(incoming, multiple=multiple, mode="replace", skip_digestion=skip_digestion)

        assert view.molsys is previous_system
        assert view.export_state() == previous_scene
        assert view.load_blocks == previous_sources
        assert view.history._undo == undo
        assert view.history._redo == redo
        assert view.history.redo()
        assert view.annotations.info("old-note")["text"] == "future"
        assert view.history.undo()
        assert view.history.undo()
        assert view.annotations.info("old-note")["text"] == "before"


def test_reset_discards_history_before_a_later_load(source):
    with msv.new_view(source) as view:
        _populate_both_stacks(view)
        view.reset_viewer()

        assert view.molsys is None
        assert view.annotations.count() == 0
        _assert_history_empty(view)
        view.load(source)
        _assert_history_empty(view)
        assert view.annotations.count() == 0


def test_initial_molecular_load_preserves_shapes_but_starts_new_history(source):
    with msv.new_view() as view:
        shape = view.shapes.add_sphere(center="[0, 0, 0] nm", radius="1 nm", tag="caller-shape")
        shape.set_alpha(0.4)
        shape.set_alpha(0.6)
        assert view.history.undo()
        assert view.history.can_undo() and view.history.can_redo()
        records = view.shapes.records()
        # Undo restores scene objects with fresh handles, before loading.
        shape = view.shapes["caller-shape"]

        view.load(source)

        assert view.shapes.records() == records
        _assert_history_empty(view)
        # The retained handle remains usable in the new history domain.
        shape.set_alpha(0.8)
        assert view.history.undo()
        assert view.shapes.records() == records
