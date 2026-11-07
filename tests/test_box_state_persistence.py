"""Retain semantic cell display, not a copied trajectory or frozen edge list."""

import json
import zipfile
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
import pyunitwizard as puw
from molsysviewer._private.exceptions import ArgumentError

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as source:
        with source.extract(structure_indices=[0, 8, 3]) as result:
            cells = np.array([np.diag([length, length + 1, length + 2]) for length in [3.0, 4.0, 5.0]])
            msm.set(result.molsys, box=puw.quantity(cells, "nm"))
            result.apply_system_edit(result.molsys, skip_digestion=True)
            yield result


def box_edges(view):
    records = [m for m in view._shape_history if view._tag_from_message(m) == view._BOX_TAG]
    assert len(records) == 1
    return np.asarray(records[0]["options"]["coordinate_pairs"], dtype=float)


def recipe(frame):
    return {"color": 0xFF0000, "width_angstrom": 0.2, "alpha": 0.7, "structure_index": frame}


def test_duplicate_frame_feedback_preserves_an_explicit_other_cell(view):
    view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=2)
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 0})
    assert view.export_state()["box_display"] == recipe(2)
    view.player.go_to_structure(0)
    assert view.export_state()["box_display"] == recipe(0)


def test_native_resolved_cell_feedback_preserves_its_actual_cell_and_style(view):
    view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=2)
    revision = view._box_definition_revision
    view._handle_frontend_event(
        {
            "event": "trajectory_frame_changed",
            "frame": 1,
            "box_display": {"definition_revision": revision, "structure_index": 2},
        }
    )
    assert view.player.index == 1
    assert view.export_state()["box_display"] == recipe(2)
    np.testing.assert_array_equal(box_edges(view)[0], [[0, 0, 0], [50, 0, 0]])


@pytest.mark.parametrize("change", ["older_revision", "invalid_index", "boolean_index", "boolean_revision"])
def test_late_or_invalid_box_feedback_does_not_undo_a_newer_definition(view, change):
    view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=2)
    projection = {"definition_revision": view._box_definition_revision, "structure_index": 0}
    if change == "older_revision":
        projection["definition_revision"] -= 1
    elif change == "invalid_index":
        projection["structure_index"] = 3
    elif change == "boolean_index":
        projection["structure_index"] = True
    else:
        projection["definition_revision"] = True
    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 1, "box_display": projection})
    assert view.player.index == 1
    assert view.export_state()["box_display"] == recipe(2)


def test_repeated_box_frame_projection_keeps_one_recipe_and_a_single_definition(view):
    view.show_box(color="red", width=0.2, alpha=0.7)
    revision = view._box_definition_revision
    for index in range(30):
        view._handle_frontend_event(
            {
                "event": "trajectory_frame_changed",
                "frame": index % 3,
                "is_playing": True,
                "box_display": {"definition_revision": revision, "structure_index": index % 3},
            }
        )
    assert view._box_definition_revision == revision
    assert view.export_state()["box_display"] == recipe(2)
    assert len([m for m in view._shape_history if view._tag_from_message(m) == view._BOX_TAG]) == 1


@pytest.mark.parametrize("ready", [False, True])
@pytest.mark.parametrize("kind", ["state", "session"])
def test_saved_box_keeps_style_cell_and_frame_following(view, tmp_path, ready, kind):
    view._ready = ready
    view.player.go_to_structure(1)
    view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=1)
    original_cells = puw.get_value(view.molsys.structures.box, to_unit="angstrom").copy()
    path = tmp_path / ("box.json" if kind == "state" else "box.msv")
    if kind == "state":
        view.save_state(path)
        saved = json.loads(path.read_text())
        restored = msv.new_view(view.molsys)
        restored.load_state(path)
    else:
        view.save_session(path)
        with zipfile.ZipFile(path) as archive:
            saved = json.loads(archive.read("state.json"))
        restored = msv.load_session(path)
    with restored:
        assert saved["box_display"] == recipe(1)
        assert restored.export_state()["box_display"] == recipe(1)
        assert restored._box_visible and restored.player.index == 1
        np.testing.assert_array_equal(box_edges(restored)[0], [[0, 0, 0], [40, 0, 0]])
        restored.player.go_to_structure(2)
        assert restored.export_state()["box_display"] == recipe(2)
        np.testing.assert_array_equal(box_edges(restored)[0], [[0, 0, 0], [50, 0, 0]])
        np.testing.assert_array_equal(puw.get_value(restored.molsys.structures.box, to_unit="angstrom"), original_cells)
    assert view.export_state()["box_display"] == recipe(1)
    np.testing.assert_array_equal(puw.get_value(view.molsys.structures.box, to_unit="angstrom"), original_cells)


def test_explicit_other_cell_and_independent_copy_are_preserved(view):
    view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=2)
    assert view.player.index == 0
    with msv.tools.basic.copy(view) as copied:
        assert copied.player.index == 0
        assert copied.export_state()["box_display"] == recipe(2)
        np.testing.assert_array_equal(box_edges(copied)[0], [[0, 0, 0], [50, 0, 0]])
        copied.hide_box()
        assert "box_display" not in copied.export_state()
    assert view._box_visible


@pytest.mark.parametrize("frames,expected", [([2, 0, 2], 0), ([0, 2], 1), ([1, 0], 0)])
def test_extraction_remaps_box_to_retained_structure_positions(view, frames, expected):
    view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=2)
    with view.extract(structure_indices=frames) as extracted:
        assert extracted.export_state()["box_display"] == recipe(expected)
        np.testing.assert_array_equal(box_edges(extracted)[0], [[0, 0, 0], [10 * (3 + frames[expected]), 0, 0]])
        assert extracted._box_record["structure_indices"] == expected
    assert view.export_state()["box_display"] == recipe(2)


@pytest.mark.parametrize("clear", ["hide", "all-shapes", "tagged-shapes", "decorations"])
def test_clearing_the_rendered_box_cannot_resurrect_its_recipe(view, clear):
    view.show_box(color="red", width=0.2, alpha=0.7)
    if clear == "hide":
        view.hide_box()
    elif clear == "all-shapes":
        view.shapes.clear()
    elif clear == "tagged-shapes":
        view.shapes.clear(view._BOX_TAG)
    else:
        view.clear_decorations()
    assert not view._box_visible and view._box_record is None
    assert "box_display" not in view.export_state()
    assert not any(view._tag_from_message(m) == view._BOX_TAG for m in view._shape_history)


@pytest.mark.parametrize("clear_first", [False, True])
def test_legacy_state_uses_existing_merge_or_replace_semantics(view, clear_first):
    legacy = view.export_state()
    assert "box_display" not in legacy and legacy["version"] == 2
    view.show_box(color="red", width=0.2, alpha=0.7)
    view.import_state(legacy, clear_first=clear_first)
    assert view._box_visible is not clear_first
    assert ("box_display" in view.export_state()) is not clear_first


def test_clearing_another_owner_keeps_the_box_and_shape_history_roundtrips_it(view):
    view.show_box(color="red", width=0.2, alpha=0.7)
    view.annotations.add("discard", atom_indices=[0], tag="note")
    view.annotations.clear()
    assert view.export_state()["box_display"] == recipe(0)
    view.shapes.add_sphere(center="[1, 1, 1] nm", radius="0.1 nm", tag="marker")
    view.shapes.clear("marker")
    assert view.export_state()["box_display"] == recipe(0)
    view.history.undo()
    assert "marker" in view.shapes.tags()
    assert view.export_state()["box_display"] == recipe(0)
    view.history.redo()
    assert "marker" not in view.shapes.tags()
    assert view.export_state()["box_display"] == recipe(0)
    np.testing.assert_array_equal(box_edges(view)[0], [[0, 0, 0], [30, 0, 0]])


@pytest.mark.parametrize("recorded", [[], False, "box", {}, {"color": 0xFF0000}])
def test_malformed_box_display_cannot_replace_an_existing_recipe(view, recorded):
    view.show_box(color="red", width=0.2, alpha=0.7)
    original = view.export_state()
    incoming = {**original, "box_display": recorded}
    with pytest.raises(ValueError):
        view.import_state(incoming)
    assert view.export_state() == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("color", True),
        ("color", -1),
        ("color", 0x1000000),
        ("width_angstrom", False),
        ("width_angstrom", 0),
        ("width_angstrom", float("inf")),
        pytest.param("width_angstrom", 10**500, id="overflowing-width"),
        ("alpha", True),
        ("alpha", float("nan")),
        ("alpha", 1.1),
        ("structure_index", True),
        ("structure_index", -1),
        ("structure_index", 3),
    ],
)
def test_invalid_box_display_preserves_the_existing_scene(view, field, value):
    annotation = view.annotations.add("keep", atom_indices=[0], tag="keep")
    view.show_box(color="red", width=0.2, alpha=0.7)
    original = view.export_state()
    history = deepcopy(view._shape_history)
    incoming = deepcopy(original)
    incoming["annotations"] = []
    incoming["box_display"] = {**recipe(0), field: value}
    with pytest.raises(ValueError):
        view.import_state(incoming)
    assert view.export_state() == original
    assert view.annotations["keep"] is annotation and annotation._active
    assert view._shape_history == history


def test_a_box_recipe_requires_a_cell_in_the_destination_system(view):
    annotation = view.annotations.add("keep", atom_indices=[0], tag="keep")
    incoming = view.export_state()
    msm.set(view.molsys, box=None)
    view.apply_system_edit(view.molsys, skip_digestion=True)
    original = view.export_state()
    incoming["box_display"] = recipe(0)
    with pytest.raises(ValueError):
        view.import_state(incoming)
    assert view.export_state() == original
    assert view.annotations["keep"] is annotation
    assert view.molsys.structures.box is None


def test_box_display_geometry_has_explicit_units_under_a_user_policy(view):
    view.show_box(color="red", width=0.2, alpha=0.7, structure_indices=1)
    document = view.export_state()
    policy = ["angstrom", "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]
    with puw.context(standard_units=policy):
        with msv.new_view(view.molsys) as restored:
            restored.import_state(document)
            assert restored.export_state()["box_display"] == recipe(1)
            np.testing.assert_array_equal(box_edges(restored)[0], [[0, 0, 0], [40, 0, 0]])


@pytest.mark.parametrize("skip", [False, True])
@pytest.mark.parametrize("width", [0, -1, float("nan"), float("inf"), True, np.bool_(True), [0.1, 0.2]])
def test_invalid_public_box_width_preserves_previous_display(view, width, skip):
    view.show_box(color="red", width=0.2, alpha=0.7)
    original = view.export_state()
    history = deepcopy(view._shape_history)
    with pytest.raises(ArgumentError):
        view.show_box(width=width, skip_digestion=skip)
    assert view.export_state() == original
    assert view._shape_history == history


@pytest.mark.parametrize("skip", [False, True])
@pytest.mark.parametrize("unit,value", [(None, 1.5), ("nm", 0.15), ("angstrom", 1.5)])
@pytest.mark.parametrize("policy_length", ["nm", "angstrom"])
def test_box_width_converts_explicit_lengths_without_changing_bare_values(view, skip, unit, value, policy_length):
    policy = [policy_length, "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]
    cells = puw.get_value(view.molsys.structures.box, to_unit="angstrom").copy()
    with puw.context(standard_units=policy):
        width = value if unit is None else puw.quantity(value, unit)
        view.show_box(width=width, skip_digestion=skip)
        assert view._shape_history[-1]["options"]["radii"] == pytest.approx(1.5)
        assert view.export_state()["box_display"]["width_angstrom"] == pytest.approx(1.5)
        np.testing.assert_array_equal(puw.get_value(view.molsys.structures.box, to_unit="angstrom"), cells)
