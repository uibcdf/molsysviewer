"""Real scene creation failures preserve state and return correlated Studio results."""

import numpy as np
import pytest
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture
def view():
    result = msv.demo["pentalanine"]
    try:
        yield result
    finally:
        result.close()


def observe(view):
    sent = []
    original = view.widget.send

    def send(message, buffers=None):
        sent.append(message)
        return original(message, buffers=buffers)

    view.widget.send = send
    view._ready = True
    return sent


def scene(view):
    return {
        key: value
        for key, value in view.export_state().items()
        if key not in {"order_high_water_mark", "uid_high_water_mark", "tag_high_water_marks"}
    }


@pytest.mark.parametrize(
    "action, domain, details",
    [
        ("create_measurement", "measurements", {"kind": "distance", "picks": [[0], [5]], "tag": "existing"}),
        ("create_layer", "layers", {"tag": "existing-layer", "members": [{"member_kind": "shape", "member_tag": "member"}]}),
        ("create_annotation", "annotations", {"text": "draft", "position": [None, 0, 0]}),
    ],
)
def test_rejected_creation_preserves_scene_and_redo_and_reports_domain(view, action, domain, details):
    view.measurements.add_distance([0], [5], tag="existing")
    view.layers.add("existing-layer")
    view.shapes.add_sphere(atom_indices=[0], tag="member")
    view.shapes.add_sphere(atom_indices=[1], tag="undone")
    view.history.undo()
    before = scene(view)
    sent = observe(view)
    with pytest.raises(ValueError):
        dispatch_panel_action(view, {"action": action, "request_id": "draft", **details})
    assert scene(view) == before and view.history.can_redo()
    result = sent[-1]
    assert result["op"] == "studio_action_result" and result["request_id"] == "draft"
    assert result["action"] == action and result["domain"] == domain
    assert not result["ok"] and result["error_message"]
    assert view.shapes.get("member").layer_tag == "member"


def test_layer_creation_validates_all_members_before_mutation(view):
    view.shapes.add_sphere(atom_indices=[0], tag="member")
    before = scene(view)
    with pytest.raises(ValueError):
        dispatch_panel_action(
            view,
            {
                "action": "create_layer",
                "tag": "new",
                "members": [
                    {"member_kind": "shape", "member_tag": "member"},
                    {"member_kind": "shape", "member_tag": "missing"},
                ],
            },
        )
    assert scene(view) == before


def test_layer_creation_with_members_has_one_undo_and_redo(view):
    view.shapes.add_sphere(atom_indices=[0], tag="member")
    view.regions.add(atom_indices=[1], tag="region")
    before = scene(view)
    sent = observe(view)
    dispatch_panel_action(
        view,
        {
            "action": "create_layer",
            "tag": "new",
            "request_id": "layer",
            "members": [
                {"member_kind": "shape", "member_tag": "member"},
                {"member_kind": "region", "member_tag": "region"},
            ],
        },
    )
    assert sent[-1]["ok"] and sent[-1]["domain"] == "layers"
    assert view.shapes.get("member").layer_tag == "new" and view.regions["region"].layer == "new"
    assert view.history.undo() and scene(view) == before
    assert view.history.redo()
    assert view.shapes.get("member").layer_tag == "new" and view.regions["region"].layer == "new"


@pytest.mark.parametrize(
    "position", [[None, 0, 0], ["", 0, 0], [True, 0, 0], [float("nan"), 0, 0], [0, float("inf"), 0], [0, 0]]
)
def test_annotation_missing_or_nonfinite_coordinates_are_rejected(view, position):
    before = scene(view)
    with pytest.raises(ValueError, match="three finite numbers"):
        dispatch_panel_action(view, {"action": "create_annotation", "text": "draft", "position": position})
    assert scene(view) == before


@pytest.mark.parametrize("unit", ["nm", "angstrom"])
def test_annotation_explicit_zero_and_nm_coordinates_survive_standard_unit_changes(view, unit):
    with puw.context(standard_units=[unit, "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]):
        sent = observe(view)
        dispatch_panel_action(
            view, {"action": "create_annotation", "text": "origin", "position": [0, 1, 2], "request_id": "annotation"}
        )
    label = next(message for message in sent if message["op"] == "add_label")
    np.testing.assert_allclose(label["options"]["position"], [0, 10, 20])
    assert sent[-1]["ok"] and sent[-1]["domain"] == "annotations"


def test_analysis_deletion_reports_success_and_protects_references(view):
    view.interactions.hbonds.get_buch_hbonds(name="science", structure_indices=[0])
    view.interactions.add("science", tag="visual")
    sent = observe(view)
    with pytest.raises(Exception, match="referenc"):
        dispatch_panel_action(
            view, {"action": "delete_interaction_analysis", "analysis_name": "science", "request_id": "blocked"}
        )
    assert not sent[-1]["ok"] and sent[-1]["domain"] == "interactions"
    assert "science" in view.molsys.interactions and view.history.can_undo()
    view.interactions.delete("visual")
    dispatch_panel_action(
        view, {"action": "delete_interaction_analysis", "analysis_name": "science", "request_id": "delete"}
    )
    assert "science" not in view.molsys.interactions
    assert not view.history.can_undo() and not view.history.can_redo()
    assert sent[-1]["ok"] and sent[-1]["request_id"] == "delete"
