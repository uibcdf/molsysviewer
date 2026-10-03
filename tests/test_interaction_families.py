"""Qualify explicit family wrappers with real detectors and chemical systems."""

import inspect

import molsysmt as msm
import numpy as np
import pytest
from devtools.interaction_family_fixtures import make_family_view
from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._private.interaction_families import FAMILIES
from molsysviewer.interactions import _analysis_signature
from molsysviewer.viewer.panel_actions.interactions import _create_interaction

import molsysviewer as msv

KINDS = list(FAMILIES) + ["water_bridge_2"]


def assert_projection(view, result, tag, frame):
    """Independent role/centroid/image oracle; do not call the renderer's adapter."""
    data = result.query(structure_indices=[frame]).to_dict()
    xyz = np.asarray(
        msm.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True, structure_indices=[frame]), to_unit="nm")
    )[0]
    box = msm.get(view.molsys, box=True, structure_indices=[frame])
    box = None if box is None else np.asarray(msm.pyunitwizard.get_value(box, to_unit="nm"))[0]
    expected = {}
    for row, occurrence in enumerate(data["occurrence_indices"]):
        parts = result.relation(int(data["relation_indices"][row]))["participants"]
        positions = np.asarray([xyz[p["atom_indices"]].mean(axis=0) for p in parts])
        if data["image_vectors"] is not None:
            lo, hi = data["image_offsets"][row : row + 2]
            images = data["image_vectors"][lo:hi]
            if np.any(images):
                positions += (images - images[0]) @ box
        roles = {p["role"]: i for i, p in enumerate(parts)}
        kind = result.relation(int(data["relation_indices"][row]))["interaction_type"]
        endpoints = {
            "hbond": [("hydrogen", "acceptor")],
            "ionic_contact": [("positive", "negative")],
            "pi_pi": [("ring_a", "ring_b")],
            "cation_pi": [("cation", "ring")],
            "halogen_bond": [("halogen", "acceptor")],
            "hydrophobic_contact": [("hydrophobic_1", "hydrophobic_2")],
            "metal_coordination_candidate": [("metal", "ligand")],
        }
        if kind == "disulfide_candidate":
            pairs = [(0, 1)]
        elif kind == "water_bridge":
            pairs = [
                (roles[f"leg_{leg}_hydrogen"], roles[f"leg_{leg}_acceptor"]) for leg in range(1, len(parts) // 3 + 1)
            ]
        else:
            pairs = [(roles[a], roles[b]) for a, b in endpoints[kind]]
        for segment, (a, b) in enumerate(pairs):
            expected[int(occurrence), segment] = (positions[a], positions[b], parts)
    message = next(item for item in view.interactions._messages(frame) if item["tag"] == tag)
    assert message["status"] == "evaluated"
    assert message["n_supported"] == len(data["occurrence_indices"])
    assert message["n_observations"] == result.query(structure_indices=[frame]).n_interactions
    assert message["n_segments"] == len(expected) == len(message["links"])
    assert message["n_skipped"] == 0
    assert {(link["occurrence_index"], link["segment_index"]) for link in message["links"]} == set(expected)
    for link in message["links"]:
        start, end, parts = expected[link["occurrence_index"], link["segment_index"]]
        np.testing.assert_allclose(link["start"], start, atol=1e-8)
        np.testing.assert_allclose(link["end"], end, atol=1e-8)
        assert link["participants"] == [{"role": p["role"], "atom_indices": p["atom_indices"].tolist()} for p in parts]
    return message


@pytest.mark.parametrize("kind", KINDS)
def test_named_family_calculation_roles_frames_geometry_and_h5msm(kind, tmp_path):
    case = make_family_view(kind)
    view = case.view
    frames = [2, 0, 1] if view.molsys.structures.n_structures == 3 else [0]
    result = case.calculate(structure_indices=frames)
    assert result is view.molsys.interactions["contacts"]
    assert result.n_interactions > 0
    assert set(result.relation_types) == {"water_bridge" if kind == "water_bridge_2" else kind}
    assert set(result.evaluated_structure_indices) == set(frames)
    assert view.interactions.tags() == []  # Calculation stores data; add creates a display.
    view.interactions.add("contacts", tag="links")
    for frame in frames:
        assert_projection(view, result, "links", frame)
    if kind not in {"hbond", "disulfide_candidate"}:
        assert result.query(structure_indices=[1]).n_interactions == 0
        selected = view.interactions.query("contacts", structure_indices=[2, 0])
        assert selected.n_interactions == result.n_interactions
        atoms = np.unique(result.participant_atoms).tolist()
        assert (
            view.interactions.query(
                "contacts", selection=atoms, mode="internal", structure_indices=[2, 0]
            ).n_interactions
            == result.n_interactions
        )
        atom = int(result.participant_atoms[0])
        incident = view.interactions.query("contacts", selection=[atom], mode="incident", structure_indices=[2, 0])
        assert incident.n_interactions > 0
        assert (
            view.interactions.query("contacts", selection=[atom], mode="cross", structure_indices=[2, 0]).n_interactions
            == incident.n_interactions
        )
        assert (
            view.interactions.query(
                "contacts",
                selection=[atom],
                mode="between",
                selection_2=[i for i in atoms if i != atom],
                structure_indices=[2, 0],
            ).n_interactions
            == incident.n_interactions
        )
    path = str(tmp_path / "family.h5msm")
    msm.convert(view.molsys, to_form=path)
    # Read the stored analysis directly: full MolSys conversion can remap axes
    # and canonicalize evaluated-frame order, creating a new analysis identity.
    restored = msm.h5msm.read_layers(path, layers=["interactions"])["interactions"]["contacts"]
    assert _analysis_signature(restored) == _analysis_signature(result)
    before = set(view.molsys.interactions)
    with pytest.raises(ValueError):
        case.calculate(structure_indices=frames)
    assert set(view.molsys.interactions) == before


@pytest.mark.parametrize("kind", [k for k in KINDS if k not in {"hbond", "disulfide_candidate"}])
def test_periodic_family_segments_and_scientific_session_roundtrip(kind, tmp_path):
    case = make_family_view(kind, periodic=True)
    result = case.calculate(pbc=True)
    assert result.n_interactions > 0
    assert np.any(result.image_vectors)
    case.view.interactions.add("contacts", tag="links")
    original = assert_projection(case.view, result, "links", 0)
    path = tmp_path / "periodic.msvz"
    case.view.save_session(path)
    restored = msv.load_session(path)
    assert _analysis_signature(restored.molsys.interactions["contacts"]) == _analysis_signature(result)
    assert_projection(restored, restored.molsys.interactions["contacts"], "links", 0)
    assert restored.interactions._messages(0)[0]["links"] == original["links"]


def test_explicit_namespaces_signatures_and_bypass_are_reachable():
    case = make_family_view("hbond")
    for name in ("compute", "compute_hbonds", "compute_disulfide_candidates"):
        assert not hasattr(case.view.interactions, name)
    for family, function, _, _ in FAMILIES.values():
        getter = getattr(getattr(case.view.interactions, family), function)
        signature = inspect.signature(getter)
        assert signature.parameters["name"].default is inspect.Parameter.empty
        assert signature.parameters["skip_digestion"].default is False
        assert getattr(getter, "digestion_plan", None) is not None
        assert not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in signature.parameters.values())
    # The legacy peptide demo lacks modern chemical-graph columns. The modern
    # detector correctly requires complete chemistry; use real RDKit topology.
    modern = make_family_view("water_bridge")
    result = modern.view.interactions.hbonds.get_hbonds(name="modern", distance_threshold="0.4 nm")
    assert result.n_interactions > 0
    legacy = case.view.interactions.hbonds.get_luzard_chandler_hbonds(name="luzard")
    assert legacy is case.view.molsys.interactions["luzard"]


@pytest.mark.parametrize(
    "parameters",
    [
        {"distance_threshold": 0.4},
        {"max_matches": True},
        {"structure_indices": [True]},
        {"assume_complete_connectivity": "yes"},
        {"angle_threshold": "1 nm"},
    ],
)
def test_invalid_arguments_are_digested_before_calculation(parameters):
    case = make_family_view("hbond")
    with pytest.raises(ArgumentError):
        case.view.interactions.hbonds.get_hbonds(name="invalid", **parameters)
    assert not case.view.molsys.interactions


def test_studio_uses_the_family_wrapper_with_explicit_two_set_scope():
    case = make_family_view("halogen_bond")
    _create_interaction(
        case.view,
        {
            "source": "calculate",
            "analysis_name": "studio",
            "tag": "links",
            "calculation": {
                "kind": "halogen_bond",
                "selection": [0, 1],
                "selection_2": [2, 3],
                "structure_indices": [2, 0],
                "parameters": {},
            },
        },
    )
    result = case.view.molsys.interactions["studio"]
    assert result.n_interactions == 2
    assert result.evaluation_mode == "between"
    assert_projection(case.view, result, "links", 0)
    with pytest.raises(ValueError, match="override"):
        _create_interaction(
            case.view,
            {
                "source": "calculate",
                "analysis_name": "bad",
                "calculation": {"kind": "halogen_bond", "parameters": {"skip_digestion": True}},
            },
        )
    assert "bad" not in case.view.molsys.interactions


@pytest.mark.parametrize("standard_angle", ["radians", "degrees"])
def test_studio_angular_endpoints_become_a_provider_vector_quantity(standard_angle):
    case = make_family_view("halogen_bond")
    with msm.pyunitwizard.context(
        standard_units=["angstrom", "ps", "K", "mole", "dalton", "e", "kJ/mol", standard_angle]
    ):
        _create_interaction(
            case.view,
            {
                "source": "calculate",
                "analysis_name": "intervals",
                "tag": "links",
                "calculation": {
                    "kind": "halogen_bond",
                    "parameters": {
                        "donor_angle_range": ["130 degrees", f"{np.pi} radians"],
                        "acceptor_angle_range": [f"{np.deg2rad(80)} radians", "140 degrees"],
                    },
                },
            },
        )
        result = case.view.interactions.get_analysis("intervals")
        expected = msm.interactions.halogen_bonds.get_halogen_bonds(
            case.view.molsys,
            structure_indices=[0],
            pbc=False,
            donor_angle_range=msm.pyunitwizard.quantity([130, 180], "degrees"),
            acceptor_angle_range=msm.pyunitwizard.quantity([80, 140], "degrees"),
            output_type="molsysmt.Interactions",
        )
        assert result.n_interactions == expected.n_interactions > 0
        np.testing.assert_array_equal(result.participant_atoms, expected.participant_atoms)
        np.testing.assert_allclose(result.measurements["donor_angle"], expected.measurements["donor_angle"])
        np.testing.assert_allclose(result.parameters["donor_angle_range"]["value"], np.deg2rad([130, 180]))
        assert result.parameters["donor_angle_range"]["unit"] == "radians"
        assert_projection(case.view, result, "links", 0)


@pytest.mark.parametrize("endpoints", [[None, "180 degrees"], ["130 degrees", "1 nm"], [True, "180 degrees"]])
def test_invalid_angular_endpoints_do_not_attach_an_analysis(endpoints):
    case = make_family_view("halogen_bond")
    with pytest.raises(ArgumentError):
        case.view.interactions.halogen_bonds.get_halogen_bonds(name="invalid", donor_angle_range=endpoints)
    assert not case.view.molsys.interactions
