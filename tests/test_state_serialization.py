import json
import pytest
from molsysviewer import MolSysView


def test_export_state_returns_json_serializable_dict():
    view = MolSysView()
    view.measurements.add_distance([0], [1], tag="d1", measurement_style={"color": "#FF0000"})
    view.measurements.add_angle([0], [1], [2], tag="ang1")

    state = view.export_state()

    assert isinstance(state, dict)
    assert state["version"] == 1

    # Must be fully JSON-serializable (no numpy types, no non-serializable objects)
    serialized = json.dumps(state)
    restored = json.loads(serialized)
    assert restored["version"] == 1


def test_export_state_captures_annotations():
    view = MolSysView()
    # Simulate annotation history directly (no structure needed)
    view._annotation_history.append({  # noqa: SLF001
        "op": "add_label",
        "tag": "ann1",
        "options": {"text": "Hello", "atom_indices": [3, 4], "tag": "ann1"},
    })

    state = view.export_state()

    assert len(state["annotations"]) == 1
    assert state["annotations"][0]["tag"] == "ann1"
    assert state["annotations"][0]["options"]["text"] == "Hello"


def test_export_state_captures_measurements():
    view = MolSysView()
    view.measurements.add_distance([0], [1], tag="d1")
    view.measurements.add_angle([0], [1], [2], tag="a1")

    state = view.export_state()

    tags = [m["tag"] for m in state["measurements"]]
    assert "d1" in tags
    assert "a1" in tags


def test_export_state_captures_selections():
    view = MolSysView()
    # Inject a selection record directly (no structure needed)
    view._selection_history.append({  # noqa: SLF001
        "op": "save_selection",
        "tag": "sel1",
        "atom_indices": [0, 1, 2],
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "group_indices": [],
        "component_indices": [],
        "chain_indices": [],
        "molecule_indices": [],
        "entity_indices": [],
    })

    state = view.export_state()

    assert len(state["selections"]) == 1
    assert state["selections"][0]["tag"] == "sel1"


def test_import_state_replays_measurements():
    source = MolSysView()
    source.measurements.add_distance([0], [1], tag="d1", measurement_style={"color": "#00FF00"})
    source.measurements.add_dihedral([0], [1], [2], [3], tag="dih1")

    state = source.export_state()

    target = MolSysView()
    target.import_state(state)

    assert target.measurements.count() == 2
    tags = {r["tag"] for r in target.measurements.records()}
    assert tags == {"d1", "dih1"}
    d1_record = next(r for r in target.measurements.records() if r["tag"] == "d1")
    assert d1_record["options"].get("style") == {"color": "#00FF00"}


def test_import_state_replays_annotations():
    source = MolSysView()
    source._annotation_history.append({  # noqa: SLF001
        "op": "add_label",
        "tag": "ann1",
        "options": {"text": "Active site", "atom_indices": [10, 11], "tag": "ann1"},
    })

    state = source.export_state()

    target = MolSysView()
    target.import_state(state)

    assert target.annotations.count() == 1
    assert target.annotations.records()[0]["tag"] == "ann1"


def test_import_state_replays_selections():
    selection_msg = {
        "op": "save_selection",
        "tag": "sel1",
        "atom_indices": [5, 6, 7],
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "group_indices": [],
        "component_indices": [],
        "chain_indices": [],
        "molecule_indices": [],
        "entity_indices": [],
    }
    source = MolSysView()
    source._selection_history.append(selection_msg)  # noqa: SLF001

    state = source.export_state()

    target = MolSysView()
    target.import_state(state)

    assert target.selections.contains("sel1", skip_digestion=True)


def test_import_state_clear_first_removes_existing_state():
    view = MolSysView()
    view.measurements.add_distance([0], [1], tag="old")

    new_state = {"version": 1, "annotations": [], "measurements": [], "selections": [], "regions": []}
    view.import_state(new_state, clear_first=True)

    assert view.measurements.count() == 0


def test_import_state_merge_keeps_existing_measurements():
    view = MolSysView()
    view.measurements.add_distance([0], [1], tag="existing")

    extra_state = {
        "version": 1,
        "annotations": [],
        "measurements": [{
            "op": "add_distance_measurement",
            "tag": "new",
            "options": {"tag": "new", "picks_atom_indices": [[2], [3]], "endpoint_atom_indices": [[2], [3]],
                        "endpoint_kinds": ["atom", "atom"], "endpoint_policy": "centroid",
                        "endpoint_labels": ["atom", "atom"], "layer_tag": "new"},
        }],
        "selections": [],
        "regions": [],
    }
    view.import_state(extra_state, clear_first=False)

    assert view.measurements.count() == 2


def test_import_state_skips_duplicate_selection_tags():
    view = MolSysView()
    msg = {
        "op": "save_selection", "tag": "sel1", "atom_indices": [1, 2],
        "source_kind": "element", "element_level": "group", "target_level": "none",
        "items": [], "group_indices": [], "component_indices": [],
        "chain_indices": [], "molecule_indices": [], "entity_indices": [],
    }
    view._selection_history.append(msg)  # noqa: SLF001

    state = view.export_state()
    view.import_state(state, clear_first=False)

    assert sum(1 for r in view.selections.records() if r["tag"] == "sel1") == 1


def test_export_state_numpy_int_serializable():
    """Atom indices from real MolSysMT operations are numpy.int64 — must be converted."""
    import numpy as np
    view = MolSysView()
    view._annotation_history.append({  # noqa: SLF001
        "op": "add_label",
        "tag": "np-ann",
        "options": {"text": "test", "atom_indices": [np.int64(0), np.int64(1)], "tag": "np-ann"},
    })
    state = view.export_state()
    # Should not raise
    serialized = json.dumps(state)
    assert '"atom_indices": [0, 1]' in serialized or json.loads(serialized)["annotations"][0]["options"]["atom_indices"] == [0, 1]
