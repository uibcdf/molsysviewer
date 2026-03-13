from molsysviewer import MolSysView


def test_persist_last_measurement_builds_replayable_distance_message():
    view = MolSysView()
    event = {
        "event": "interaction_measurement_created",
        "action": "distance",
        "picked_count": 2,
        "picks_atom_indices": [[0], [1]],
    }
    view._handle_frontend_event(event)  # noqa: SLF001

    layer = view.measurements.persist_last_measurement(tag="m1")

    assert layer.tag == "m1"
    assert layer.kind == "measurement"
    assert view._measurement_history == [  # noqa: SLF001
        {
            "op": "add_distance_measurement",
            "tag": "m1",
            "options": {
                "tag": "m1",
                "picks_atom_indices": [[0], [1]],
            },
        }
    ]


def test_context_action_persist_last_measurement_executes_python_bridge():
    view = MolSysView()
    measurement = {
        "event": "interaction_measurement_created",
        "action": "distance",
        "picked_count": 2,
        "picks_atom_indices": [[0], [1]],
    }
    view._handle_frontend_event(measurement)  # noqa: SLF001
    view._handle_frontend_event(
        {
            "event": "interaction_context_action",
            "action": "persist_last_measurement",
            "context": {"event": "interaction_context_menu", "kind": "empty"},
        }
    )  # noqa: SLF001

    assert len(view._measurement_history) == 1  # noqa: SLF001
    msg = view._measurement_history[0]  # noqa: SLF001
    assert msg["op"] == "add_distance_measurement"
    assert msg["options"]["picks_atom_indices"] == [[0], [1]]


def test_measurements_info_and_records_report_persisted_measurements():
    view = MolSysView()
    event = {
        "event": "interaction_measurement_created",
        "action": "distance",
        "picked_count": 2,
        "picks_atom_indices": [[0], [1]],
    }
    view._handle_frontend_event(event)  # noqa: SLF001
    view.measurements.persist_last_measurement(tag="m1")

    assert view.measurements.count() == 1
    assert view.measurements.records() == [  # noqa: SLF001
        {
            "op": "add_distance_measurement",
            "tag": "m1",
            "options": {
                "tag": "m1",
                "picks_atom_indices": [[0], [1]],
            },
        }
    ]
    assert view.measurements.info() == [
        {
            "kind": "distance",
            "tag": "m1",
            "n_picks": 2,
            "picks_atom_indices": [[0], [1]],
            "visible": True,
            "active": True,
        }
    ]
