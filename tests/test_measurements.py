import pytest

from molsysviewer import MolSysView
from molsysviewer import pyunitwizard as puw


def test_interactive_measurement_is_registered_automatically():
    view = MolSysView()
    event = {
        "event": "interaction_measurement_created",
        "action": "distance",
        "picked_count": 2,
        "picks_atom_indices": [[0], [1]],
    }
    view._handle_frontend_event(event)  # noqa: SLF001

    assert view._measurement_history == [  # noqa: SLF001
        {
            "op": "add_distance_measurement",
            "tag": "measurement1",
            "options": {
                "tag": "measurement1",
                "layer_tag": "measurement1",
                "picks_atom_indices": [[0], [1]],
                "endpoint_kinds": ["atom", "atom"],
                "endpoint_policy": "centroid",
                "endpoint_labels": ["atom", "atom"],
                "endpoint_atom_indices": [[0], [1]],
            },
        }
    ]
    assert view.get_last_measurement_created_event()["tag"] == "measurement1"

def test_measurements_info_and_records_report_persisted_measurements():
    view = MolSysView()
    event = {
        "event": "interaction_measurement_created",
        "action": "distance",
        "picked_count": 2,
        "picks_atom_indices": [[0], [1]],
    }
    view._handle_frontend_event(event)  # noqa: SLF001

    assert view.measurements.count() == 1
    assert view.measurements.records() == [  # noqa: SLF001
        {
            "op": "add_distance_measurement",
            "tag": "measurement1",
            "options": {
                "tag": "measurement1",
                "layer_tag": "measurement1",
                "picks_atom_indices": [[0], [1]],
                "endpoint_kinds": ["atom", "atom"],
                "endpoint_policy": "centroid",
                "endpoint_labels": ["atom", "atom"],
                "endpoint_atom_indices": [[0], [1]],
            },
        }
    ]
    assert view.measurements.info() == [
        {
            "kind": "distance",
            "tag": "measurement1",
            "layer_tag": "measurement1",
            "n_picks": 2,
            "picks_atom_indices": [[0], [1]],
            "endpoint_kinds": ["atom", "atom"],
            "endpoint_policy": "centroid",
            "endpoint_labels": ["atom", "atom"],
            "endpoint_atom_indices": [[0], [1]],
            "value": None,
            "visible": True,
            "active": True,
        }
    ]


def test_measurements_info_reports_centroid_endpoint_policy_for_multi_atom_picks():
    view = MolSysView()
    event = {
        "event": "interaction_measurement_created",
        "action": "distance",
        "picked_count": 2,
        "picks_atom_indices": [[0], [1, 2, 3]],
    }
    view._handle_frontend_event(event)  # noqa: SLF001

    assert view.measurements.info() == [
        {
            "kind": "distance",
            "tag": "measurement1",
            "layer_tag": "measurement1",
            "n_picks": 2,
            "picks_atom_indices": [[0], [1, 2, 3]],
            "endpoint_kinds": ["atom", "centroid"],
            "endpoint_policy": "centroid",
            "endpoint_labels": ["atom", "centroid"],
            "endpoint_atom_indices": [[0], []],
            "value": None,
            "visible": True,
            "active": True,
        }
    ]



def test_measurement_series_preserves_all_coordinate_frames(monkeypatch):
    view = MolSysView()
    view._molsys = object()  # noqa: SLF001

    coordinates_by_atom = {
        0: [[[0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0]]],
        1: [[[0.1, 0.0, 0.0]], [[0.2, 0.0, 0.0]]],
    }

    def fake_get(_molsys, *, selection, coordinates=False, **_kwargs):
        atoms = [int(item) for item in selection]
        if coordinates:
            frames = []
            for frame_index in range(2):
                frames.append([coordinates_by_atom[atom][frame_index][0] for atom in atoms])
            return {"coordinates": frames}
        return {
            "atom_name": [f"A{atom}" for atom in atoms],
            "group_name": ["RES" for _atom in atoms],
            "group_type": ["other" for _atom in atoms],
        }

    monkeypatch.setattr("molsysviewer.measurements.msm.get", fake_get)

    view.measurements.add_distance([0], [1], tag="d01")

    record = view.measurements.records()[0]
    assert record["options"]["value"] == pytest.approx(1.0)
    assert record["options"]["value_series"] == pytest.approx([1.0, 2.0])
    assert puw.get_value(view.measurements.info("d01")[0]["value"], to_unit="angstrom") == pytest.approx(1.0)

    view.player.go_to_structure(1)

    assert puw.get_value(view.measurements.info("d01")[0]["value"], to_unit="angstrom") == pytest.approx(2.0)
    assert puw.get_value(view.measurements.series("d01"), to_unit="angstrom").tolist() == pytest.approx([1.0, 2.0])

def test_measurements_manager_supports_registry_access_and_duplicate_tag_guard():
    view = MolSysView()
    layer = view.measurements.add_distance([0], [1], tag="dist_1")

    assert view.measurements.contains("dist_1") is True
    assert view.measurements.get("dist_1") is layer
    assert view.measurements["dist_1"] is layer
    assert view.measurements.tags() == ["dist_1"]
    assert view.layers["dist_1"].measurements == {"dist_1": layer}
    assert view.layers["dist_1"].members == {"dist_1": layer}

    with pytest.raises(ValueError, match="already exists"):
        view.measurements.add_distance([2], [3], tag="dist_1")

    with pytest.raises(KeyError):
        _ = view.measurements["missing"]


def test_measurements_manager_supports_explicit_shared_layer_tag():
    view = MolSysView()
    first = view.measurements.add_distance([0], [1], tag="dist_1", layer_tag="geom")
    second = view.measurements.add_angle([0], [1], [2], tag="ang_1", layer_tag="geom")

    assert first.layer_tag == "geom"
    assert second.layer_tag == "geom"
    assert "geom" in view.layers
    assert set(view.layers["geom"].measurements.keys()) == {"dist_1", "ang_1"}
    assert set(view.layers["geom"].members.keys()) == {"dist_1", "ang_1"}


def test_measurements_manager_can_move_measurement_between_layers():
    view = MolSysView()
    layer = view.measurements.add_distance([0], [1], tag="dist_1")

    moved = view.measurements.set_layer_tag("dist_1", "geom")

    assert moved is layer
    assert view.measurements["dist_1"].layer_tag == "geom"
    assert "dist_1" not in view.layers
    assert "geom" in view.layers
    assert view.layers["geom"].measurements == {"dist_1": layer}
    assert view.measurements.info("dist_1")[0]["layer_tag"] == "geom"
    assert view.measurements.records()[0]["options"]["layer_tag"] == "geom"


def test_add_distance_with_measurement_style_includes_style_in_message():
    view = MolSysView()
    view.measurements.add_distance([0], [1], tag="d1", measurement_style={"color": "#FF0000", "size_em": 1.5})
    records = view.measurements.records()
    assert len(records) == 1
    options = records[0]["options"]
    assert options.get("style") == {"color": "#FF0000", "size_em": 1.5}


def test_add_distance_without_measurement_style_omits_style_from_message():
    view = MolSysView()
    view.measurements.add_distance([0], [1], tag="d2")
    records = view.measurements.records()
    assert len(records) == 1
    options = records[0]["options"]
    assert "style" not in options
