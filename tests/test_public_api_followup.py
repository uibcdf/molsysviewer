"""Final API boundary regressions on real demo systems (#218–#222)."""

from copy import deepcopy
from typing import get_args, get_type_hints

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.layers import Annotation, Layer, Measurement, Region, SceneObject

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["dialanine"] as scene:
        yield scene


@pytest.mark.parametrize("skip", [False, True])
def test_region_system_queries_never_expand_atom_scope(view, skip):
    region = view.regions.add(atom_indices=[0, 1], tag="subset")
    assert region.get(n_atoms=True, skip_digestion=skip) == 2
    assert view.whole.get(n_atoms=True, skip_digestion=skip) == 22
    for selection, mask, expected in [("all", None, 2), ([1, 10], None, 1), ([10], None, 0), ("all", [1, 10], 1)]:
        assert region.get(selection=selection, mask=mask, n_atoms=True, skip_digestion=skip) == expected
    actual = region.get(coordinates=True, structure_indices=[0], skip_digestion=skip)
    expected = msm.get(view.molsys, selection=[0, 1], coordinates=True, structure_indices=[0])
    np.testing.assert_allclose(msv.pyunitwizard.get_value(actual), msv.pyunitwizard.get_value(expected))
    # Global structural quantities retain the provider's meaning under atom scoping.
    for attribute in ("time", "box"):
        actual = region.get(**{attribute: True}, skip_digestion=skip)
        expected = msm.get(view.molsys, selection=[0, 1], **{attribute: True})
        if expected is None:
            assert actual is None
        else:
            np.testing.assert_equal(msv.pyunitwizard.get_value(actual), msv.pyunitwizard.get_value(expected))
    assert region.get(element="atom", selection=[1, 10], atom_index=True, skip_digestion=skip) == [1]


@pytest.mark.parametrize("retirement", ["delete", "undo", "import"])
@pytest.mark.parametrize("skip", [False, True])
def test_retired_queries_reject_tag_reuse_without_changing_state(view, retirement, skip):
    region = view.regions.add(atom_indices=[0, 1], tag="old")
    layer = view.layers.add("old-layer")
    view.history.clear()
    if retirement == "delete":
        region.delete()
        layer.delete()
        view.regions.add(atom_indices=[10, 11], tag="old")
        view.layers.add("old-layer")
    elif retirement == "undo":
        region.hide()
        assert view.history.undo()
    else:
        view.import_state(view.export_state())
    before = deepcopy(view.export_state())
    redo = view.history.can_redo()
    operations = [
        lambda: region.select(skip_digestion=skip),
        lambda: region.get(n_atoms=True, skip_digestion=skip),
        lambda: region.info(output_type="dictionary", skip_digestion=skip),
        lambda: region.convert(skip_digestion=skip),
        lambda: region.get_center(skip_digestion=skip),
        lambda: region.overlaps(skip_digestion=skip),
        lambda: layer.info(skip_digestion=skip),
    ]
    operations += [
        lambda field=field: getattr(layer, field)
        for field in ("members", "shapes", "annotations", "measurements", "interactions", "regions")
    ]
    for operation in operations:
        with pytest.raises(ValueError, match="retired"):
            operation()
        assert view.export_state() == before
        assert view.history.can_redo() == redo


@pytest.mark.parametrize("assignment", [False, True])
def test_region_mode_is_undoable_and_invalid_changes_preserve_redo(view, assignment):
    region = view.regions.add(selection="atom_index < 2", tag="query")
    view.history.clear()
    if assignment:
        region.mode = "dynamic"
    else:
        region.set_mode("dynamic")
    assert region.mode == "dynamic" and view.history.can_undo()
    assert view.history.undo()
    restored = view.regions["query"]
    assert restored.mode == "static"
    restored.set_mode("static")
    assert view.history.can_redo()
    for skip in (False, True):
        with pytest.raises(ValueError):
            restored.set_mode("unknown", skip_digestion=skip)
        assert restored.mode == "static" and view.history.can_redo()
    with pytest.raises(ValueError, match="retired"):
        region.set_mode("static")
    assert view.history.redo()
    assert view.regions["query"].mode == "dynamic"
    assert view.history.undo()
    assert not view.history.can_undo()  # exactly one checkpoint


def test_index_only_regions_reject_dynamic_mode_without_history(view):
    region = view.regions.add(atom_indices=[0, 1], tag="indices")
    view.history.clear()
    for skip in (False, True):
        with pytest.raises(ValueError, match="re-evaluable"):
            region.set_mode("dynamic", skip_digestion=skip)
    assert region.mode == "static" and not view.history.can_undo()


def test_public_handle_annotations_match_runtime_objects(view):
    note = view.annotations.add("note", atom_indices=[0])
    distance = view.measurements.add("distance", [0], [1])
    for manager, obj, expected in ((view.annotations, note, Annotation), (view.measurements, distance, Measurement)):
        assert type(obj) is expected
        for name in ("__getitem__", "add", "get", "show", "hide", "set_tag", "set_layer_tag"):
            declared = get_type_hints(getattr(manager, name))["return"]
            assert declared is expected or set(get_args(declared)) == {expected, type(None)}
        assert manager[obj.tag] is obj and manager.get(obj.tag) is obj
    for method in (Layer.attach, Layer.detach):
        assert set(get_args(get_type_hints(method)["obj"])) == {SceneObject, Region}
    group = view.layers.add("group")
    assert type(group) is Layer and not isinstance(note, Layer) and not isinstance(distance, Layer)


def test_interaction_state_reads_are_detached_and_setters_own_history(view):
    view.interactions.hbonds.get_buch_hbonds(name="analysis")
    obj = view.interactions.add("analysis", selection=[0, 1], structure_indices=[0], tag="contacts")
    before = deepcopy(view.export_state())
    view.history.clear()
    config = obj.filter
    config["selection"].append(10)
    config["structure_indices"].append(2)
    obj.style["alpha"] = -1
    for field in ("filter", "style"):
        with pytest.raises(AttributeError):
            setattr(obj, field, {})
    assert view.export_state() == before and not view.history.can_undo()
    obj.set_alpha(0.3)
    assert obj.style["alpha"] == 0.3 and view.history.can_undo()
    assert view.history.undo()
    restored = view.interactions["contacts"]
    assert restored.style["alpha"] == 0.85
    with pytest.raises(ValueError, match="retired"):
        _ = obj.filter
    assert view.history.redo()
    restored = view.interactions["contacts"]
    assert restored.style["alpha"] == 0.3
    restored.set_filter(selection=[1], structure_indices=[0])
    state = view.export_state()
    view.import_state(state)
    assert view.interactions["contacts"].filter["selection"] == [1]
    assert view.interactions["contacts"].style["alpha"] == 0.3
