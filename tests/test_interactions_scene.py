"""Native interaction objects on real molecular systems and provider results."""

import json
import sys
import zipfile
from copy import deepcopy

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer._pyunitwizard import puw
from molsysviewer.demo import demo
from molsysviewer.interactions import _to_plain
from molsysviewer.viewer.panel_actions import dispatch_panel_action

import molsysviewer as msv


@pytest.fixture
def view():
    view = msv.new_view(demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
    participants = [
        {"role": role, "atom_indices": [index]} for index, role in enumerate(("donor", "hydrogen", "acceptor"))
    ]
    records = [
        {
            "structure_index": 0,
            "interaction_type": "hbond",
            "participants": participants,
            "measurements": {"distance": value},
        }
        for value in (0.2, 0.21)
    ]
    records.append(
        {
            "structure_index": 0,
            "interaction_type": "pi_stacking",
            "participants": [{"role": "ring", "atom_indices": [3, 4]}, {"role": "ring", "atom_indices": [5, 6]}],
            "measurements": {"distance": 0.4},
        }
    )
    result = msm.Interactions.from_records(
        records,
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=3,
        evaluated_structure_indices=[0, 1],
        method="synthetic_scene_fixture",
        measure_units={"distance": "nm"},
    )
    view.interactions.attach(result, name="contacts", assume_aligned=True)
    return view


def test_sparse_visual_projection_and_inspection_keep_parallel_identity(view):
    obj = view.interactions.add("contacts", tag="hb")
    payload = view.interactions._messages()[0]
    assert payload["coordinate_unit"] == "nm"
    assert payload["n_observations"] == 3 and payload["n_supported"] == 2 and payload["n_skipped"] == 1
    assert payload["status"] == "partial"
    assert [link["occurrence_index"] for link in payload["links"]] == [0, 1]
    xyz = puw.get_value(msm.get(view.molsys, coordinates=True, structure_indices=[0]), to_unit="nm")[0]
    assert payload["links"][0]["start"] == pytest.approx(xyz[1])
    assert payload["links"][0]["end"] == pytest.approx(xyz[2])
    inspection = view.interactions.inspect("hb", offset=2, limit=1)
    assert inspection["total"] == 3
    assert inspection["observations"][0]["participants"][0]["atom_indices"] == [3, 4]
    assert inspection["observations"][0]["occurrence_index"] == 2
    json.dumps(_to_plain(inspection), allow_nan=False)
    assert "occurrence_indices" not in view.interactions.records()[0]
    assert view.layers[obj.layer_tag].members[("interaction", "hb")] is obj


def test_frame_coverage_is_distinct_from_visual_filter(view):
    obj = view.interactions.add("contacts")
    assert view.interactions._frame(obj, 1)["status"] == "evaluated"
    assert view.interactions._frame(obj, 1)["n_observations"] == 0
    assert view.interactions._frame(obj, 2)["status"] == "unevaluated"
    obj.set_filter(structure_indices=[0, 2])
    assert view.interactions._frame(obj, 1)["status"] == "excluded"
    obj.set_filter(selection=[0], mode="internal")
    assert view.interactions._frame(obj, 0)["n_observations"] == 0
    obj.set_filter(selection=[0], selection_2=[2], mode="between")
    assert view.interactions._frame(obj, 0)["n_supported"] == 2


def test_inspector_tracks_query_revision_and_respects_excluded_frames(view):
    obj = view.interactions.add("contacts", tag="hb")
    original = view.interactions.inspect("hb")
    obj.set_filter(selection=[0, 1, 2], mode="internal", structure_indices=[1])
    excluded = view.interactions.inspect("hb", structure_index=0)
    assert excluded["status"] == "excluded" and excluded["total"] == 0
    assert excluded["observations"] == []
    assert excluded["query_revision"] != original["query_revision"]
    assert excluded["analysis_revision"] == original["analysis_revision"]
    assert "atom_indices" not in excluded["evaluation_scope"]
    obj.set_filter(selection=[0], mode="incident")
    assert view.interactions.inspect("hb")["total"] == 2


def test_inspector_metadata_budget_preserves_complete_scientific_data(view):
    parameters = {"note": "x" * (512 * 1024)}
    result = msm.Interactions.from_records(
        [],
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=3,
        evaluated_structure_indices=[0],
        method="synthetic_metadata_budget",
        parameters=parameters,
    )
    view.interactions.attach(result, name="large-metadata", assume_aligned=True)
    view.interactions.add("large-metadata", tag="metadata")
    reply = view.interactions.inspect("metadata")
    assert reply["status"] == "inspection-limit" and reply["total"] == 0
    assert reply["observations"] == [] and "metadata" in reply["limit_reason"]
    assert len(json.dumps(_to_plain(reply)).encode()) < 512 * 1024
    assert view.interactions.get_analysis("large-metadata").parameters == parameters


def test_oversized_frame_is_refused_before_occurrence_materialization(view):
    source = view.interactions.get_analysis("contacts")
    count = 50001
    result = msm.Interactions(
        n_atoms=source.n_atoms,
        n_structures=source.n_structures,
        evaluated_structure_indices=[0],
        relation_types=["hbond"],
        relation_participant_offsets=[0, 3],
        participant_roles=["donor", "hydrogen", "acceptor"],
        participant_atom_offsets=[0, 1, 2, 3],
        participant_atoms=[0, 1, 2],
        occurrence_structures=np.zeros(count, dtype=np.int64),
        occurrence_relations=np.zeros(count, dtype=np.int64),
        occurrence_evidence=np.zeros(count, dtype=np.int32),
        evidence_labels=["synthetic"],
        measurements={"distance": np.full(count, 0.2)},
        measure_units={"distance": "nm"},
        method="dense_frame_fixture",
    )
    view.interactions.attach(result, name="large", assume_aligned=True)
    materialized = []
    previous = sys.getprofile()

    def record_call(frame, event, arg):
        if event == "call" and frame.f_code is msm.Interactions.to_dict.__code__:
            materialized.append(frame.f_code.co_name)

    sys.setprofile(record_call)
    try:
        obj = view.interactions.add("large", tag="large")
        payload = view.interactions._frame(obj, 0)
        inspection = view.interactions.inspect("large")
    finally:
        sys.setprofile(previous)
    assert materialized == [], "Rejected frames must not copy occurrence columns first."
    assert payload["status"] == "render-limit" and payload["n_observations"] == count
    assert inspection["status"] == "evaluated" and inspection["total"] == count
    assert len(inspection["observations"]) == 50 and inspection["next_offset"] == 50
    assert inspection["limit_reason"] is None


def test_context_deletion_keeps_same_tag_shapes_and_measurements(view):
    view.interactions.add("contacts", tag="same")
    view.shapes.add_sphere(center="[0, 0, 0] nm", radius="0.1 nm", tag="same")
    view.measurements.add_distance(selection_a=[0], selection_b=[1], tag="same")
    view._handle_frontend_event({"event": "interaction_context_action", "action": "delete_interaction", "tag": "same"})
    assert not view.interactions.contains("same")
    assert view.shapes.contains("same") and view.measurements.contains("same")


def test_scene_lifecycle_history_layers_and_scientific_delete_guard(view):
    result = view.interactions.get_analysis("contacts")
    obj = view.interactions.add("contacts", tag="same")
    view.annotations.add(text="label", atom_indices=[0], tag="same")
    obj.set_tag("renamed")
    obj.set_color("#336699")
    obj.set_radius("0.3 angstroms")
    obj.set_alpha(0.5)
    view.layers.add("shared")
    obj.set_layer_tag("shared")
    assert view.layers["shared"].members[("interaction", "renamed")] is obj
    obj.hide()
    view.history.undo()
    assert not view.interactions["renamed"]._hidden
    state = view.export_state()
    view.interactions.delete("renamed")
    assert view.interactions.get_analysis("contacts") is result
    view.history.undo()
    obj = view.interactions["renamed"]
    assert obj.style == {"color": 0x336699, "alpha": 0.5, "radius_nm": pytest.approx(0.03), "radius_unit": "nm"}
    with pytest.raises(ValueError, match="referenc"):
        view.interactions.delete_analysis("contacts")
    view.import_state(state)
    assert view.interactions["renamed"].layer_tag == "shared"
    view.interactions.clear()
    view.interactions.delete_analysis("contacts")
    assert view.interactions.analyses() == [] and not view.history.can_undo()


def test_state_reference_mismatch_is_rejected_before_scene_mutation(view):
    obj = view.interactions.add("contacts")
    state = view.export_state()
    invalid = deepcopy(state)
    invalid["interactions"][0]["analysis_revision"] = "sha256:wrong"
    with pytest.raises(ValueError, match="different scientific analysis"):
        view.import_state(invalid)
    assert view.interactions[obj.tag] is obj
    invalid = deepcopy(state)
    invalid["interaction_state_version"] = 900
    with pytest.raises(ValueError, match="Unsupported interaction state"):
        view.import_state(invalid)
    assert view.interactions[obj.tag] is obj


def test_periodic_participants_are_shifted_relative_to_donor(view):
    box = np.array([[2.0, 0.0, 0.0], [0.5, 2.0, 0.0], [0.0, 0.0, 2.0]])
    msm.set(view.molsys, box=puw.quantity(np.repeat(box[None], 3, axis=0), "nm"))
    participants = [
        {"role": role, "atom_indices": [index]} for index, role in enumerate(("donor", "hydrogen", "acceptor"))
    ]
    result = msm.Interactions.from_records(
        [
            {
                "structure_index": 0,
                "interaction_type": "hbond",
                "participants": participants,
                "images": [[1, 0, 0], [1, 1, 0], [2, 1, 0]],
            }
        ],
        n_atoms=view.molsys.get_n_atoms(),
        n_structures=3,
        evaluated_structure_indices=[0],
        method="periodic_fixture",
    )
    view.interactions.attach(result, name="periodic", assume_aligned=True)
    obj = view.interactions.add("periodic")
    link = view.interactions._frame(obj, 0)["links"][0]
    xyz = puw.get_value(msm.get(view.molsys, coordinates=True, structure_indices=[0]), to_unit="nm")[0]
    assert link["start"] == pytest.approx(xyz[1] + box[1])
    assert link["end"] == pytest.approx(xyz[2] + box[0] + box[1])


def test_static_export_and_live_snapshots_have_different_frame_contracts(view):
    view.interactions.add("contacts", tag="hb")
    live = view._build_embedded_runtime_snapshot()
    assert any(msg["op"] == "set_interaction_frame" for msg in live)
    assert any(msg["op"] == "set_interaction_summaries" for msg in live)
    static = view._build_static_export_snapshot()
    assert not any(msg["op"] == "set_interaction_frame" for msg in static)
    frames = next(msg["frames"] for msg in static if msg["op"] == "set_interaction_series")
    assert [item["status"] for item in frames] == ["partial", "evaluated", "unevaluated"]
    assert view.interactions._frame(view.interactions["hb"], 0)["frame"] == 0


def test_native_panel_actions_and_frame_request_are_json_safe(view):
    dispatch_panel_action(
        view, {"action": "create_interaction", "source": "stored", "analysis_name": "contacts", "tag": "hb"}
    )
    dispatch_panel_action(
        view,
        {
            "action": "edit_interaction",
            "tag": "hb",
            "color": "#336699",
            "radius_nm": 0.03,
            "radius_unit": "nm",
            "alpha": 0.5,
        },
    )
    view.history.undo()
    assert view.interactions["hb"].style["color"] == 0x34D399
    view._ready = True
    view._handle_frontend_event({"event": "request_interaction_frame", "frame": 1, "request_id": 9})
    assert view.player.index == 0
    dispatch_panel_action(view, {"action": "inspect_interaction", "tag": "hb", "frame": 0, "request_id": 10})
    dispatch_panel_action(view, {"action": "toggle_interaction_visibility", "tag": "hb"})
    assert view.interactions["hb"]._hidden


def test_session_roundtrip_keeps_visual_references_and_occurrences(view, tmp_path):
    view.interactions.add("contacts", tag="hb").hide()
    path = tmp_path / "interactions.msvz"
    view.save_session(path)
    restored = msv.load_session(path)
    assert restored.interactions.tags() == ["hb"]
    assert restored.interactions["hb"]._hidden
    assert [link["occurrence_index"] for link in restored.interactions._messages()[0]["links"]] == [0, 1]


@pytest.mark.parametrize("damage", ["signature", "style", "filter", "version"])
def test_session_rejects_invalid_scientific_scene_before_replacing_destination(view, tmp_path, damage):
    from ipywidgets.widgets.widget import _instances

    view.interactions.add("contacts", tag="hb")
    path = tmp_path / "invalid-scientific-scene.msv"
    view.save_session(path)
    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    state = json.loads(members["state.json"])
    record = state["interactions"][0]
    if damage == "signature":
        record["analysis_revision"] = "sha256:wrong"
    elif damage == "style":
        record["style"]["radius_unit"] = "angstrom"
    elif damage == "filter":
        record["filter"]["structure_indices"] = [999]
    else:
        state["interaction_state_version"] = 999
    members["state.json"] = json.dumps(state).encode()
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    with demo["dialanine"] as destination:
        destination.annotations.add("keep", atom_indices=[0], tag="keep")
        handle = destination.annotations.get("keep")
        system = destination.molsys
        original = deepcopy(destination.export_state())
        widgets = set(_instances)
        with pytest.raises(ValueError):
            msv.load_session(path, view=destination)
        assert destination.molsys is system
        assert destination.export_state() == original
        assert destination.annotations.get("keep") is handle
        assert set(_instances) == widgets


def test_invalid_visual_edits_leave_valid_configuration(view):
    obj = view.interactions.add("contacts")
    before = deepcopy(obj.filter)
    with pytest.raises(ValueError):
        obj.set_filter(selection=[0], selection_2=[0], mode="between")
    assert obj.filter == before
    with pytest.raises(ValueError):
        obj.set_radius("0 nm")
    with pytest.raises(ValueError):
        obj.set_alpha(float("nan"))
    with pytest.raises(KeyError):
        view.interactions.info("missing")


def test_damaged_filter_survives_state_roundtrip_and_can_be_repaired(view):
    obj = view.interactions.add("contacts", selection=[0], tag="hb")
    obj.broken = True
    obj.filter["selection"] = [view.molsys.get_n_atoms() + 10]
    obj._payload_key = None
    state = view.export_state()
    view.import_state(state)
    restored = view.interactions["hb"]
    assert restored.broken and view.interactions.info("hb")["status"] == "broken"
    restored.set_filter(selection=[0])
    assert not restored.broken and view.interactions.info("hb")["n_supported"] == 2


def test_structural_removal_preserves_a_broken_set_and_invalidates_coverage(view):
    size = view.molsys.get_n_atoms()
    obj = view.interactions.add("contacts", tag="hb", selection=[size - 1])
    extracted = msm.extract(view.molsys, selection=list(range(size - 1)))
    view.apply_system_edit(extracted, atom_index_map={i: i for i in range(size - 1)})
    assert view.interactions["hb"] is obj and obj.broken
    assert view.interactions.info("hb")["status"] == "broken"
    assert view.interactions.get_analysis("contacts").evaluated_structure_indices.size == 0
    view.import_state(view.export_state())
    assert view.interactions["hb"].broken
    view.interactions["hb"].set_filter(selection=[0])
    assert view.interactions.info("hb")["status"] == "unevaluated"


def test_panel_form_validation_precedes_all_visual_mutations(view):
    obj = view.interactions.add("contacts", tag="hb")
    with pytest.raises(ValueError, match="Invalid interaction radius_nm"):
        dispatch_panel_action(
            view, {"action": "edit_interaction", "tag": "hb", "new_tag": "changed", "color": "#336699", "radius_nm": -1}
        )
    assert view.interactions["hb"] is obj and obj.style["color"] == 0x34D399
    with pytest.raises(ValueError):
        view.interactions.inspect("hb", limit=201, skip_digestion=True)


def test_panel_calculation_and_file_routes_publish_then_create_sets(view, tmp_path):
    dispatch_panel_action(
        view,
        {
            "action": "create_interaction",
            "source": "calculate",
            "analysis_name": "buch",
            "tag": "calculated",
            "calculation": {"kind": "hbond", "structure_indices": [0], "distance_threshold": "0.23 nm"},
        },
    )
    assert view.interactions["calculated"].analysis_name == "buch"
    assert view.interactions.get_analysis("buch").evaluated_structure_indices.tolist() == [0]
    path = tmp_path / "analysis.h5msm"
    msm.h5msm.write_layers(str(path), interactions={"stored": view.interactions.get_analysis("contacts")})
    content = {
        "action": "create_interaction",
        "source": "file",
        "analysis_name": "loaded",
        "tag": "loaded-set",
        "filename": str(path),
        "file_analysis_name": "stored",
    }
    with pytest.raises(ValueError, match="assume_aligned=True"):
        dispatch_panel_action(view, content)
    assert view.interactions.get("loaded-set") is None
    content["assume_aligned"] = True
    dispatch_panel_action(view, content)
    assert view.interactions.info("loaded-set")["n_observations"] == 3
    content = {
        "action": "create_interaction",
        "source": "calculate",
        "analysis_name": "retained",
        "tag": "calculated",
        "calculation": {"kind": "disulfide_candidate", "structure_indices": [0]},
    }
    with pytest.raises(ValueError, match="was stored"):
        dispatch_panel_action(view, content)
    assert view.interactions.get_analysis("retained").evaluated_structure_indices.tolist() == [0]


def test_radius_unit_is_declared_and_checked_before_restore(view):
    obj = view.interactions.add("contacts", tag="hb")
    obj.set_radius("0.3 angstroms")
    assert obj.style["radius_unit"] == "nm"
    assert obj.style["radius_nm"] == pytest.approx(0.03)
    state = view.export_state()
    state["interactions"][0]["style"]["radius_unit"] = "angstrom"
    with pytest.raises(ValueError, match="Invalid interaction display style"):
        view.import_state(state)
    assert view.interactions["hb"] is obj
