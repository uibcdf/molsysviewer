"""Public boundary regressions on real scene and scientific owners (#211–#216)."""

import inspect
import warnings
from copy import deepcopy
from types import MappingProxyType

import numpy as np
import pytest

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["dialanine"] as scene:
        yield scene


def test_annotation_arguments_are_honored_before_mutation(view):
    expected = view.whole.select("resid 0", syntax="MDTraj")
    note = view.annotations.add("group", selection="resid 0", syntax="MDTraj", tag="note")
    assert view.annotations.info("note")["atom_indices"] == list(expected)
    view.annotations.set_anchor("note", "resid 1", syntax="MDTraj")
    assert view.annotations.info("note")["atom_indices"] == list(view.whole.select("resid 1", syntax="MDTraj"))
    state = deepcopy(view.export_state())
    with pytest.raises(ValueError, match="Unsupported annotation kind"):
        view.annotations.add("unknown", atom_indices=[0], kind="unknown")
    assert view.export_state() == state
    assert note is view.annotations["note"]


@pytest.mark.parametrize("skip", [False, True])
def test_foreign_handles_cannot_change_either_scene(view, skip):
    with msv.demo["pentalanine"] as other:
        local = view.regions.add(atom_indices=[0, 1, 2], tag="local")
        foreign = other.regions.add(atom_indices=[1, 2, 3], tag="foreign")
        group = view.layers.add("group")
        foreign_group = other.layers.add("foreign-group")
        shape = other.shapes.add_sphere(tag="sphere")
        states = (deepcopy(view.export_state()), deepcopy(other.export_state()))
        operations = [
            lambda: group.attach(shape, skip_digestion=skip),
            lambda: group.attach(foreign, skip_digestion=skip),
            lambda: local.set_layer(foreign_group, skip_digestion=skip),
            lambda: view.camera.focus_region(foreign, skip_digestion=skip),
        ]
        operations += [lambda method=method: method(foreign, tag="result", skip_digestion=skip)
                       for method in (local.union, local.intersection, local.difference)]
        for operation in operations:
            with pytest.raises(ValueError, match="same view"):
                operation()
            assert (view.export_state(), other.export_state()) == states


def test_layer_attach_and_detach_region_use_canonical_lifecycle(view):
    region = view.regions.add(atom_indices=[0, 1], tag="region")
    group = view.layers.add("group")
    group.attach(region)
    assert region.layer == "group"
    assert group.members[("region", "region")] is region
    assert view.history.undo()
    assert view.regions["region"].layer is None
    assert view.history.redo()
    group = view.layers["group"]
    group.detach(view.regions["region"])
    assert view.regions["region"].layer is None
    assert not group.members


@pytest.mark.parametrize("kind", ["annotation", "interaction"])
def test_camera_dispatch_agrees_with_live_object_focus(view, kind, length_standard):
    if kind == "annotation":
        obj = view.annotations.add("point", position="[1, 2, 3] nm", tag="target")
    else:
        view.interactions.hbonds.get_buch_hbonds(name="analysis")
        obj = view.interactions.add("analysis", tag="target")
    obj.focus(duration="80 ms", extra_radius="0.7 nm")
    direct = deepcopy(view._test_message_log[-1])
    view.camera.focus_on_object("target", kind=kind, duration="80 ms", extra_radius="0.7 nm")
    assert view._test_message_log[-1] == direct
    assert direct["duration_ms"] == 80
    assert direct["radius"] >= 7
    if kind == "annotation":
        assert direct["center"] == pytest.approx([10, 20, 30])
        # A point keeps the existing 0.1 nm minimum bounding radius plus padding.
        assert direct["radius"] == pytest.approx(8)
    else:
        metadata = obj.info()
        metadata["tag"] = "detached"
        assert obj.info()["tag"] == "target"
    obj.delete()
    start = len(view._test_message_log)
    with pytest.raises(ValueError, match="retired"):
        obj.focus()
    with pytest.raises(ValueError, match="retired"):
        obj.info()
    assert not any(msg["op"] in {"zoom", "zoom_to_position"} for msg in view._test_message_log[start:])


@pytest.fixture(params=["nm", "angstrom"])
def length_standard(request):
    puw = msv.pyunitwizard
    original = list(puw.configure.get_standard_units())
    standards = ["nm", "ps", "K", "mole", "amu", "e", "kJ/mol",
                 "kJ/(mol*nm)", "kJ/(mol*nm**2)", "radians"]
    standards[0] = request.param
    puw.configure.set_standard_units(standards)
    try:
        yield request.param
    finally:
        puw.configure.set_standard_units(original)


def test_retired_region_focus_preserves_redo_and_camera(view):
    region = view.regions.add(atom_indices=[0, 1], tag="region")
    region.delete()
    assert view.history.undo()
    redo = list(view.history._redo)
    start = len(view._test_message_log)
    with pytest.raises(ValueError, match="retired"):
        view.camera.focus_region(region)
    assert view.history._redo == redo
    assert not any(msg["op"] == "zoom" for msg in view._test_message_log[start:])


@pytest.mark.parametrize("indices", [[0, 1], [0, 1, 20, 21]])
def test_saved_selection_label_retains_exact_atoms_without_deprecated_routes(view, indices):
    selection = view.selections.add("saved", atom_indices=indices)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        selection.add_label("saved label", tag="label")
    assert view.annotations.info("label")["atom_indices"] == indices
    assert not any(issubclass(item.category, DeprecationWarning) for item in caught)


def test_general_measurement_constructor_preserves_explicit_bypass(view):
    style = MappingProxyType({"color": 0xFF0000})
    named = view.measurements.add_distance([0], [1], measurement_style=style, tag="named", skip_digestion=True)
    general = view.measurements.add("distance", [0], [1], measurement_style=style, tag="general", skip_digestion=True)
    assert np.allclose(msv.pyunitwizard.get_value(named.get_coordinates()),
                       msv.pyunitwizard.get_value(general.get_coordinates()))
    records = view.measurements.records()
    assert records[0]["options"]["style"] == records[1]["options"]["style"]


def test_scene_identity_is_read_only_and_supported_renames_still_restore(view):
    shape = view.shapes.add_sphere(tag="shape")
    note = view.annotations.add("note", atom_indices=[0], tag="note")
    measure = view.measurements.add_distance([0], [1], tag="measure")
    group = view.layers.add("group")
    selection = view.selections.add("selection", atom_indices=[0])
    region = view.regions.add(atom_indices=[0], tag="region")
    state = deepcopy(view.export_state())
    for obj in (shape, note, measure, group, selection, region):
        with pytest.raises(AttributeError):
            obj.tag = "raw-write"
    for obj in (shape, note, measure):
        with pytest.raises(AttributeError):
            obj.layer_tag = "raw-write"
        with pytest.raises(AttributeError):
            obj.kind = "raw-write"
    with pytest.raises(AttributeError):
        region.uid = "raw-write"
    assert view.export_state() == state
    shape.set_tag("renamed")
    shape.set_layer_tag("group")
    assert view.history.undo()
    assert view.shapes["renamed"].layer_tag == "renamed"
    assert view.history.redo()
    assert view.shapes["renamed"].layer_tag == "group"
    view.import_state(view.export_state())
    assert view.shapes["renamed"].tag == "renamed"
    assert view.shapes["renamed"].layer_tag == "group"


def test_scene_handle_queries_and_annotation_edits_delegate_to_owners(view):
    note = view.annotations.add("original", atom_indices=[0], tag="note")
    note.set_text("edited")
    note.set_style({"color": "#ff0000", "size_em": 1.5})
    note.set_anchor(position="[1, 2, 3] nm")
    assert note.info()["text"] == "edited"
    assert note.info()["style"]["size_em"] == 1.5
    assert np.allclose(msv.pyunitwizard.get_value(note.get_coordinates(), to_unit="nm"), [1, 2, 3])
    note.info()["style"]["size_em"] = 99
    assert note.info()["style"]["size_em"] == 1.5
    assert view.history.undo()
    note = view.annotations["note"]
    assert note.info()["atom_indices"] == [0]
    assert view.history.redo()
    shape = view.shapes.add_sphere(tag="shape")
    measure = view.measurements.add_distance([0], [1], tag="measure")
    assert shape.info()["tag"] == "shape"
    assert measure.info()["tag"] == "measure"
    note = view.annotations["note"]
    note.delete()
    for operation in (note.info, lambda: note.set_text("retired"),
                      lambda: note.set_style({}), lambda: note.set_anchor(atom_indices=[1])):
        with pytest.raises(ValueError, match="retired"):
            operation()


def test_region_rename_vocabulary_and_sphere_signature_are_discoverable(view):
    region = view.regions.add(atom_indices=[0, 1], tag="region")
    region.set_tag("renamed")
    assert view.regions["renamed"] is region
    assert "region" not in view.regions
    view.regions.add(atom_indices=[2], tag="occupied")
    state = deepcopy(view.export_state())
    with pytest.raises(ValueError, match="already exists"):
        region.set_tag("occupied")
    assert view.export_state() == state
    params = inspect.signature(view.shapes.add_sphere).parameters
    assert {"structure_centers", "selection", "atom_indices", "structures_atom_indices"} <= params.keys()
    shape = view.shapes.add_sphere(atom_indices=[0], tag="anchored")
    assert shape.info()["tag"] == "anchored"
