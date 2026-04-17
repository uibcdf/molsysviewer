import pytest

from molsysviewer import MolSysView


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
            "tag": "layer1",
            "options": {
                "tag": "layer1",
                "layer_tag": "layer1",
                "picks_atom_indices": [[0], [1]],
                "endpoint_kinds": ["atom", "atom"],
                "endpoint_policy": "centroid",
                "endpoint_labels": ["atom", "atom"],
                "endpoint_atom_indices": [[0], [1]],
            },
        }
    ]
    assert view.get_last_measurement_created_event()["tag"] == "layer1"

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
            "tag": "layer1",
            "options": {
                "tag": "layer1",
                "layer_tag": "layer1",
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
            "tag": "layer1",
            "layer_tag": "layer1",
            "n_picks": 2,
            "picks_atom_indices": [[0], [1]],
            "endpoint_kinds": ["atom", "atom"],
            "endpoint_policy": "centroid",
            "endpoint_labels": ["atom", "atom"],
            "endpoint_atom_indices": [[0], [1]],
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
            "tag": "layer1",
            "layer_tag": "layer1",
            "n_picks": 2,
            "picks_atom_indices": [[0], [1, 2, 3]],
            "endpoint_kinds": ["atom", "centroid"],
            "endpoint_policy": "centroid",
            "endpoint_labels": ["atom", "centroid"],
            "endpoint_atom_indices": [[0], []],
            "visible": True,
            "active": True,
        }
    ]


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
