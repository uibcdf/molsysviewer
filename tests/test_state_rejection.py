"""Rejected direct/file imports preserve the actual existing scene owners."""

import json
import warnings
from copy import deepcopy

import numpy as np
import pytest
from ipywidgets.widgets.widget import _instances
from molsysviewer._private.smonitor.warnings import RegionOverlapWarning
from molsysviewer._pyunitwizard import puw

import molsysviewer as msv


@pytest.mark.parametrize("via_file", [False, True])
@pytest.mark.parametrize("clear_first", [False, True])
@pytest.mark.parametrize("on_conflict", ["raise", "skip", "rename"])
@pytest.mark.parametrize("damage", ["section", "measurement_settings"])
def test_rejected_state_preserves_live_scene_history_and_resources(
    tmp_path, via_file, clear_first, on_conflict, damage
):
    with msv.demo["dialanine"] as source, msv.demo["dialanine"] as target:
        source.regions.add([2, 3], tag="incoming")
        source.annotations.add("incoming", atom_indices=[2], tag="incoming-note")
        incoming = source.export_state()
        if damage == "section":
            incoming["sections"] = [{"tag": "invalid", "point": [0, 0, 0], "normal": [0, 0, 0]}]
        else:
            incoming["measurement_settings"] = {"representative_atoms": {"unsupported-target": "CA"}}

        target.regions.add([0, 1], tag="keep")
        target.annotations.add("keep", atom_indices=[0], tag="keep-note")
        target.measurements.add("distance", [0], [1], tag="keep-distance")
        target.shapes.add(
            "sphere",
            center=puw.quantity([0, 0, 0], "nm"),
            radius=puw.quantity(0.1, "nm"),
            tag="keep-sphere",
        )
        target.scene.add_section([0, 0, 0], [1, 0, 0], tag="keep-plane")
        target.annotations.add("undo", atom_indices=[1], tag="undo-note")
        target.history.undo()
        handles = (
            target.regions["keep"],
            target.annotations.get("keep-note"),
            target.measurements.get("keep-distance"),
            target.shapes.get("keep-sphere"),
            target.scene.sections()[0],
        )
        state = deepcopy(target.export_state())
        system = target.molsys
        coordinates = puw.get_value(system.structures.coordinates, to_unit="nm").copy()
        history = (list(target.history._undo), list(target.history._redo))
        replay = deepcopy(
            (target._shape_history, target._annotation_history, target._measurement_history, target._selection_history)
        )
        messages = deepcopy(target._test_message_log)
        projection = target._current_molecular_projection
        widgets = set(_instances)

        with pytest.raises(ValueError):
            if via_file:
                path = tmp_path / "invalid.json"
                path.write_text(json.dumps(incoming))
                target.load_state(path, clear_first=clear_first, on_conflict=on_conflict)
            else:
                target.import_state(incoming, clear_first=clear_first, on_conflict=on_conflict)

        assert target.molsys is system
        np.testing.assert_array_equal(puw.get_value(system.structures.coordinates, to_unit="nm"), coordinates)
        assert target.export_state() == state
        assert target.regions["keep"] is handles[0]
        assert target.annotations.get("keep-note") is handles[1]
        assert target.measurements.get("keep-distance") is handles[2]
        assert target.shapes.get("keep-sphere") is handles[3]
        assert target.scene.sections()[0] is handles[4]
        assert (target.history._undo, target.history._redo) == history
        assert (
            target._shape_history,
            target._annotation_history,
            target._measurement_history,
            target._selection_history,
        ) == replay
        assert target._current_molecular_projection is projection
        assert target._test_message_log == messages
        assert set(_instances) == widgets

        # Rejection leaves both the old handle and the previous redo usable.
        assert target.history.redo()
        assert target.annotations.get("undo-note") is not None


@pytest.mark.parametrize("clear_first", [False, True])
def test_validation_does_not_reissue_accepted_destination_overlap_warnings(clear_first):
    with msv.demo["dialanine"] as source, msv.demo["dialanine"] as target:
        source.annotations.add("incoming", atom_indices=[0], tag="incoming")
        target.regions.add([0, 1], tag="existing-a").set_representation("spacefill")
        with pytest.warns(RegionOverlapWarning):
            target.regions.add([0, 1], tag="existing-b").set_representation("spacefill")

        with warnings.catch_warnings():
            warnings.simplefilter("error", RegionOverlapWarning)
            target.import_state(source.export_state(), clear_first=clear_first)

        assert target.annotations.get("incoming") is not None
        assert len(target.regions) == (0 if clear_first else 2)


@pytest.mark.parametrize("fatal", [False, True])
def test_new_import_overlap_diagnostics_are_once_and_fatal_before_publication(fatal):
    with msv.demo["dialanine"] as source, msv.demo["dialanine"] as target:
        source.regions.add([0, 1], tag="incoming-a").set_representation("spacefill")
        with pytest.warns(RegionOverlapWarning):
            source.regions.add([0, 1], tag="incoming-b").set_representation("spacefill")
        handle = target.regions.add([2, 3], tag="keep")
        before = target.export_state()
        widgets = set(_instances)

        if fatal:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RegionOverlapWarning)
                with pytest.raises(RegionOverlapWarning):
                    target.import_state(source.export_state())
            assert target.export_state() == before
            assert target.regions["keep"] is handle
        else:
            with pytest.warns(RegionOverlapWarning) as recorded:
                target.import_state(source.export_state())
            assert len(recorded) == 1
            assert target.regions.tags() == ["incoming-a", "incoming-b"]
        assert set(_instances) == widgets


def test_validation_reuses_current_bindings_and_receives_replacement_invalidation(monkeypatch):
    from molsysviewer.viewer import load as load_module

    with msv.demo["pentalanine"] as target, msv.demo["dialanine"] as replacement:
        document = target.export_state()
        original_binding = document["sources"]["binding"]["fingerprint"]
        calls = []
        native_binding = load_module._source_binding

        def observe_binding(*args):
            calls.append(args[0])
            return native_binding(*args)

        # Observe the real content hasher, retaining its real calculations.
        monkeypatch.setattr(load_module, "_source_binding", observe_binding)
        system = target.molsys
        target.import_state(document)
        assert target.molsys is system
        assert calls == []

        target.load(replacement.molsys, mode="replace")
        changed = target.export_state()
        assert changed["sources"]["binding"]["fingerprint"] != original_binding
        assert calls and calls[-1] is target.molsys
        reads = len(calls)
        target.import_state(changed)
        assert len(calls) == reads


@pytest.mark.parametrize("on_conflict", ["skip", "raise", "rename"])
def test_validation_uses_actual_target_conflicts_before_inspecting_a_skipped_record(on_conflict):
    with msv.demo["dialanine"] as target:
        handle = target.scene.add_section([0, 0, 0], [1, 0, 0], tag="existing")
        before = target.export_state()
        incoming = {"version": 2, "sections": [{"tag": "existing", "point": [0, 0, 0], "normal": [0, 0, 0]}]}
        if on_conflict == "skip":
            target.import_state(incoming, clear_first=False, on_conflict=on_conflict)
        else:
            with pytest.raises(ValueError):
                target.import_state(incoming, clear_first=False, on_conflict=on_conflict)
        assert target.scene.sections()[0] is handle
        assert target.export_state() == before
