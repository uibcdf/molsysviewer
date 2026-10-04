"""Real-system guards for the final pre-1.0 design review (#146--#150)."""

import json
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._private.smonitor.warnings import StateStructureDiffersWarning
from molsysviewer._pyunitwizard import puw
from molsysviewer.styles import Style

import molsysviewer as msv


def test_coordinate_annotation_lifecycle(tmp_path):
    view = msv.demo["dialanine"]
    note = view.annotations.add(
        "site",
        position=puw.quantity([1, 2, 3], "nm"),
        tag="point",
        offset_mode="world",
        offset=puw.quantity([2, 0, 0], "angstrom"),
        leader_line=True,
    )
    assert view.annotations.info("point")["position"] == pytest.approx([1, 2, 3])
    assert view.annotations.info("point")["offset"] == pytest.approx([0.2, 0, 0])
    state = view.export_state()
    assert state["annotations"][0]["anchor"] == {
        "type": "position",
        "coordinates": [10.0, 20.0, 30.0],
        "unit": "angstrom",
    }
    assert state["annotations"][0]["options"]["offset_unit"] == "angstrom"
    view.annotations.set_text("point", "updated")
    view.annotations.set_style("point", {"color": "#ff0000"})
    note.set_coordinates(puw.quantity([4, 5, 6], "angstrom"))
    assert puw.get_value(note.get_coordinates(), to_unit="angstrom") == pytest.approx([4, 5, 6])
    assert view.history.undo()
    assert view.annotations.info("point")["position"] == pytest.approx([1, 2, 3])
    assert view.history.redo()
    assert view.annotations.info("point")["position"] == pytest.approx([0.4, 0.5, 0.6])
    for other in (msv.tools.copy(view), view.extract(selection=[0, 1])):
        assert other.annotations.info("point")["position"] == pytest.approx([0.4, 0.5, 0.6])
        assert not other.annotations.info("point")["broken"]
    view.save_session(tmp_path / "coordinate.msv")
    restored = msv.load_session(tmp_path / "coordinate.msv")
    assert restored.annotations.info("point")["position"] == pytest.approx([0.4, 0.5, 0.6])
    assert restored.annotations.info("point")["text"] == "updated"
    view.annotations.set_anchor("point", atom_indices=[0, 1])
    assert view.export_state()["annotations"][0]["anchor"]["type"] == "atoms"
    assert "position" not in view.annotations.records()[0]["options"]
    view.annotations.set_anchor("point", position=[1, 0, 0])
    assert view.annotations.info("point")["atom_indices"] == []
    assert view.annotations.info("point")["position"] == pytest.approx([1, 0, 0])


def test_coordinate_annotation_units_and_nonfinite_refusal():
    view = msv.demo["dialanine"]
    with puw.context(standard_units=["angstrom", "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]):
        note = view.annotations.add("point", position=[1, 0, 0], offset_mode="world", offset=[0.2, 0, 0])
        assert puw.get_value(note.get_coordinates(), to_unit="nm") == pytest.approx([1, 0, 0])
        assert view.annotations.info(note.tag)["offset"] == pytest.approx([0.2, 0, 0])
    before = view.export_state()
    for kwargs in (
        {"position": [float("nan"), 0, 0]},
        {"position": [1, 2]},
        {"position": puw.quantity([1, 2, 3], "ps")},
        {"atom_indices": [0], "offset": [float("inf"), 0, 0]},
    ):
        with pytest.raises(ArgumentError):
            view.annotations.add("invalid", **kwargs)
        assert view.export_state() == before


def test_state_identity_distinguishes_same_names_with_different_groups():
    source = msv.demo["dialanine"]
    source.annotations.add("site", atom_indices=[0], tag="note")
    state = source.export_state()
    target = msv.tools.copy(source)
    names_before = msm.get(target.molsys, element="atom", atom_name=True)
    msm.set(target.molsys, element="group", selection=[0], group_id=["100"])
    target.apply_system_edit(target.molsys)
    assert np.array_equal(msm.get(target.molsys, element="atom", atom_name=True), names_before)
    assert target.export_state()["structure"]["fingerprint"] != state["structure"]["fingerprint"]
    with pytest.warns(StateStructureDiffersWarning):
        target.import_state(state)
    assert target.annotations.info("note")["broken"]


def test_announced_same_size_edit_invalidates_atom_identity_cache():
    view = msv.demo["dialanine"]
    view.annotations.add("site", atom_indices=[0], tag="note")
    before = view.export_state()
    msm.set(view.molsys, element="group", selection=[0], group_id=["100"])
    same_object = view.molsys
    view.apply_system_edit(same_object)
    after = view.export_state()
    assert view.molsys is same_object
    assert after["structure"]["n_atoms"] == before["structure"]["n_atoms"]
    assert after["structure"]["fingerprint"] != before["structure"]["fingerprint"]
    assert after["annotations"][0]["anchor"]["identity"] != before["annotations"][0]["anchor"]["identity"]
    after["structure"]["fingerprint"] = "caller mutation"
    assert view.export_state()["structure"]["fingerprint"] != "caller mutation"


def test_invalid_system_edit_append_accounting_preserves_scene():
    view = msv.demo["dialanine"]
    view.annotations.add("site", atom_indices=[0], tag="note")
    before = view.export_state()
    original = view.molsys
    messages_before = deepcopy(view._test_message_log)
    with pytest.raises(ValueError, match="requires appended_n_atoms"):
        view.apply_system_edit(msv.demo["dialanine"].molsys, load_blocks="append")
    assert view.molsys is original
    assert view.export_state() == before
    assert view._test_message_log == messages_before


def test_invalid_replacement_conversion_preserves_scene(tmp_path):
    view = msv.demo["dialanine"]
    view.annotations.add("site", atom_indices=[0], tag="note")
    before = view.export_state()
    original = view.molsys
    invalid = tmp_path / "invalid.h5msm"
    invalid.write_bytes(b"This is not an HDF5 file.")
    messages_before = deepcopy(view._test_message_log)
    with pytest.raises(OSError):
        view.load(str(invalid), mode="replace", skip_digestion=True)
    assert view.molsys is original
    assert view.export_state() == before
    assert view._test_message_log == messages_before


def test_styles_are_detached_at_input_registry_and_builtin_boundaries():
    left, right = msv.demo["dialanine"], msv.demo["dialanine"]
    params = {"molstar_color_theme": {"name": "element-symbol", "params": {"carbonColor": "element-symbol"}}}
    style = Style(representation="ball-and-stick", params=params)
    params["molstar_color_theme"]["name"] = "bad-input"
    assert style.params["molstar_color_theme"]["name"] == "element-symbol"
    added = left.styles.add("custom", style)
    style.params["molstar_color_theme"]["name"] = "bad-source"
    added.params["molstar_color_theme"]["name"] = "bad-return"
    queried = left.styles.get("custom")
    queried.params["molstar_color_theme"]["name"] = "bad-query"
    assert left.styles.get("custom").params["molstar_color_theme"]["name"] == "element-symbol"
    builtin = left.styles.get_builtin("cartoon-chain")
    builtin.params["color_scheme"] = "bad-builtin"
    assert right.styles.get_builtin("cartoon-chain").params["color_scheme"] == "chain_default"
    focus = left.styles.get_builtin_focus("hydrophobicity")
    focus.params["molstar_color_theme"]["name"] = "bad-focus"
    assert right.styles.get_builtin_focus("hydrophobicity").params["molstar_color_theme"]["name"] == "hydrophobicity"
    result = left.styles.apply(tag="cartoon-chain")
    result.params["color_scheme"] = "bad-applied"
    assert right.styles.get_builtin("cartoon-chain").params["color_scheme"] == "chain_default"
    assert left.whole.params["color_scheme"] == "chain_default"
    left.styles.focus("hydrophobicity", atom_indices=[0], tag="focus")
    exported = left.export_state()
    exported["focus"]["focus"]["style"]["params"]["molstar_color_theme"]["name"] = "bad-state-query"
    assert left.export_state()["focus"]["focus"]["style"]["params"]["molstar_color_theme"]["name"] == "hydrophobicity"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("field", ["series", "x"])
def test_nonfinite_plot_values_are_refused_before_mutation(value, field):
    view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 2, 8])
    view.trajectory_plot.show([1, 2, 3], x=[8, 2, 0], tag="valid")
    before = view.export_state()
    kwargs = {"series": [1, 2, 3], "x": [0, 2, 8]}
    kwargs[field][1] = value
    with pytest.raises(ArgumentError):
        view.trajectory_plot.show(**kwargs)
    assert view.export_state() == before
    invalid = deepcopy(before)
    card = invalid["trajectory_plots"][0]
    if field == "series":
        card["series"][0]["values"][1] = value
    else:
        card["x"][1] = value
    with pytest.raises(ArgumentError):
        view.import_state(invalid)
    assert view.export_state() == before
    json.dumps(before, allow_nan=False)
