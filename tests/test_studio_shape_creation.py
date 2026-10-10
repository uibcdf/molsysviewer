"""Studio creation uses real systems, explicit units and correlated replies."""

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


@pytest.fixture
def view():
    source = msv.demo["pentalanine"]
    try:
        result = msv.new_view(source.molsys, structure_indices=[0, 8, 3])
    finally:
        source.close()
    try:
        yield result
    finally:
        result.close()


@pytest.fixture(params=["nm", "angstrom"])
def length_policy(request):
    with puw.context(standard_units=[request.param, "ps", "K", "mole", "dalton", "e", "kJ/mol", "radians"]):
        yield request.param


@pytest.mark.parametrize("kind", ["add_network_links", "add_displacement_vectors"])
def test_shape_centers_use_all_unique_atoms_and_visible_structure(view, kind, length_policy):
    view.player.go_to_structure(2)
    xyz = puw.get_value(msm.get(view.molsys, coordinates=True, structure_indices=2), to_unit="angstroms")[0]
    first, second = xyz[[0, 1]].mean(axis=0), xyz[[7, 8]].mean(axis=0)
    dispatch_panel_action(
        view,
        {
            "action": "create_shape",
            "shape_type": kind,
            "tag": "centered",
            "atom_indices": [0, 1, 1],
            "atom_indices_2": [7, 8],
        },
    )
    options = next(
        message["options"] for message in view.export_state()["shapes"] if message["options"]["tag"] == "centered"
    )
    if kind == "add_network_links":
        np.testing.assert_allclose(options["coordinate_pairs"], [[first, second]])
    else:
        np.testing.assert_allclose(options["origins"], [first])
        np.testing.assert_allclose(options["vectors"], [second - first])
    view.player.go_to_structure(0)
    assert (
        next(message["options"] for message in view.export_state()["shapes"] if message["options"]["tag"] == "centered")
        == options
    ), "Studio explicitly creates fixed geometry"


@pytest.mark.parametrize(
    "payload",
    [
        {"shape_type": "add_network_links", "atom_indices": [0]},
        {"shape_type": "add_displacement_vectors", "atom_indices": [0], "atom_indices_2": [0]},
        {"shape_type": "add_sphere", "atom_indices": []},
        {"shape_type": "add_sphere", "atom_indices": [999999]},
        {"shape_type": "add_sphere", "coordinates": [float("nan"), 0, 0]},
        {"shape_type": "add_pocket_surface"},
        {"shape_type": "add_rings", "atom_indices": [0]},
    ],
)
def test_invalid_creation_is_reported_without_a_scene_mutation(view, payload):
    before = view.export_state()
    sent = []
    original = view.widget.send

    def observe(message, buffers=None):
        sent.append(message)
        return original(message, buffers=buffers)

    view.widget.send = observe
    view._ready = True
    with pytest.raises(ValueError):
        dispatch_panel_action(view, {"action": "create_shape", "request_id": "draft", **payload})
    assert view.export_state() == before
    reply = sent[-1]
    assert reply["op"] == "studio_action_result" and reply["request_id"] == "draft"
    assert not reply["ok"] and reply["error_message"]


def test_valid_sphere_and_pocket_creation_reports_completion(view):
    for kind in ["add_sphere", "add_pocket_surface"]:
        dispatch_panel_action(
            view,
            {"action": "create_shape", "shape_type": kind, "tag": kind, "atom_indices": [0, 1, 2], "request_id": kind},
        )
        assert view.shapes.get(kind) is not None
