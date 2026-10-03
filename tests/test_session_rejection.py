"""Invalid persisted scenes must not replace a user's existing work."""

import json
import zipfile
from copy import deepcopy

import numpy as np
import pytest
from ipywidgets.widgets.widget import _instances
from molsysviewer._pyunitwizard import puw
from molsysviewer.demo import demo

import molsysviewer as msv


def _damage_scene(path, damage):
    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    state = json.loads(members["state.json"])
    if damage == "version":
        state["version"] = 999
    elif damage == "cycle":
        region = state["regions"][0]
        region["provenance"] = {"kind": "duplicate", "of": region["uid"]}
    elif damage == "missing_operand":
        state["regions"][0]["provenance"] = {"kind": "duplicate", "of": "absent"}
    else:
        state["sections"] = [{"tag": "invalid-plane", "point": [0, 0, 0], "normal": [0, 0, 0]}]
    members["state.json"] = json.dumps(state).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


@pytest.mark.parametrize("damage", ["version", "cycle", "missing_operand", "section"])
@pytest.mark.parametrize("reuse", [True, False])
def test_invalid_session_scene_preserves_open_work_and_releases_temporary_widgets(tmp_path, damage, reuse):
    with demo["dialanine"] as source, demo["pentalanine"] as destination:
        source.regions.add(atom_indices=[0, 1], tag="source-region")
        path = tmp_path / "invalid.msv"
        source.save_session(path)
        _damage_scene(path, damage)

        destination.annotations.add("keep", atom_indices=[0], tag="keep")
        destination.annotations.add("undo-me", atom_indices=[1], tag="undo-me")
        destination.history.undo()
        # Undo rebuilds scene handles; retain the current lifetime.
        handle = destination.annotations.get("keep")
        system = destination.molsys
        coordinates = puw.get_value(system.structures.coordinates, to_unit="nm").copy()
        state = deepcopy(destination.export_state())
        undo, redo = list(destination.history._undo), list(destination.history._redo)
        messages = deepcopy(destination._annotation_history)
        projection = destination._current_molecular_projection
        widgets = set(_instances)

        with pytest.raises(ValueError):
            msv.load_session(path, view=destination if reuse else None)

        assert destination.molsys is system
        np.testing.assert_array_equal(puw.get_value(system.structures.coordinates, to_unit="nm"), coordinates)
        assert destination.export_state() == state
        assert destination.annotations.get("keep") is handle
        assert destination.history._undo == undo
        assert destination.history._redo == redo
        assert destination._annotation_history == messages
        assert destination._current_molecular_projection is projection
        assert set(_instances) == widgets


def test_successful_session_replacement_releases_the_validation_widgets(tmp_path):
    with demo["dialanine"] as source, demo["pentalanine"] as destination:
        source.annotations.add("restored", atom_indices=[0], tag="restored")
        path = tmp_path / "valid.msv"
        source.save_session(path)
        widgets = set(_instances)
        restored = msv.load_session(path, view=destination)
        assert restored is destination
        assert restored.molsys.get_n_atoms() == source.molsys.get_n_atoms()
        assert restored.annotations.tags() == ["restored"]
        assert set(_instances) == widgets
