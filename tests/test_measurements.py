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
