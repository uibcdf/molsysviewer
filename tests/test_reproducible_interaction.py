import pyunitwizard as puw
import molsysmt as msm
import molsysviewer._pyunitwizard  # noqa: F401

from molsysviewer import demo


def _seed_group_selection(view, group_index):
    atom_indices = list(view.select(selection=f"group_index=={group_index}"))
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": atom_indices,
        "group_indices": [group_index],
        "component_indices": [],
        "chain_indices": [0],
        "molecule_indices": [],
        "entity_indices": [0],
        "count_atoms": len(atom_indices),
        "count_groups": 1,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001
    return atom_indices


def test_new_region_from_active_selection_creates_replayable_region():
    view = demo["dialanine"]
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        "group_indices": [0],
        "component_indices": [],
        "chain_indices": [0],
        "molecule_indices": [],
        "entity_indices": [0],
        "count_atoms": 10,
        "count_groups": 1,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001

    region = view.new_region_from_active_selection(tag="picked", representation="ball_and_stick")

    assert region.tag == "picked"
    assert tuple(region.atom_indices) == tuple(event["atom_indices"])
    assert "picked" in view.regions
    ops = [msg["op"] for msg in view._build_export_messages()]  # noqa: SLF001
    assert "create_region" in ops
    assert "set_region_representation" in ops


def test_context_action_create_region_from_selection_executes_python_bridge():
    view = demo["dialanine"]
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        "group_indices": [0],
        "component_indices": [],
        "chain_indices": [0],
        "molecule_indices": [],
        "entity_indices": [0],
        "count_atoms": 10,
        "count_groups": 1,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001
    view._handle_frontend_event(
        {
            "event": "interaction_context_action",
            "action": "create_region_from_selection",
            "context": {"event": "interaction_context_menu", "kind": "structure", "atom_indices": event["atom_indices"]},
        }
    )  # noqa: SLF001

    assert "region1" in view.regions
    created = next(msg for msg in view._message_history if msg.get("op") == "create_region")  # noqa: SLF001
    assert created["tag"] == "region1"
    assert created["atom_indices"] == event["atom_indices"]


def test_context_action_save_selection_executes_python_bridge():
    view = demo["dialanine"]
    atom_indices = list(view.select(selection="group_index==0"))
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_active_selection_changed",
            "source_kind": "element",
            "element_level": "group",
            "target_level": "none",
            "items": [],
            "atom_indices": atom_indices,
            "group_indices": [0],
            "component_indices": [],
            "chain_indices": [0],
            "molecule_indices": [],
            "entity_indices": [0],
            "count_atoms": len(atom_indices),
            "count_groups": 1,
            "count_shapes": 0,
            "count_annotations": 0,
        }
    )
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "save_selection",
            "tag": "picked",
            "context": {"event": "interaction_context_menu", "kind": "structure", "atom_indices": atom_indices},
        }
    )

    assert view.selections.contains("picked") is True
    records = view.selections.records()
    assert len(records) == 1
    assert records[0]["op"] == "save_selection"
    assert records[0]["tag"] == "picked"
    assert records[0]["atom_indices"] == atom_indices


def test_context_action_remove_selection_executes_python_bridge():
    view = demo["dialanine"]
    atom_indices = _seed_group_selection(view, 0)
    n_atoms_before = int(msm.get(view._molsys, element="system", n_atoms=True, skip_digestion=True))  # noqa: SLF001

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "remove_selection",
            "context": {"event": "interaction_context_menu", "kind": "structure", "atom_indices": atom_indices},
        }
    )

    n_atoms_after = int(msm.get(view._molsys, element="system", n_atoms=True, skip_digestion=True))  # noqa: SLF001
    assert n_atoms_after == n_atoms_before - len(atom_indices)
    assert view.active_selection.is_empty(skip_digestion=True) is True
    assert view._message_history[-1]["op"] == "clear_active_selection"  # noqa: SLF001


def test_context_action_activate_selection_executes_python_bridge():
    view = demo["dialanine"]
    atom_indices = list(view.select(selection="group_index==1"))
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_active_selection_changed",
            "source_kind": "element",
            "element_level": "group",
            "target_level": "none",
            "items": [],
            "atom_indices": atom_indices,
            "group_indices": [1],
            "component_indices": [],
            "chain_indices": [0],
            "molecule_indices": [],
            "entity_indices": [0],
            "count_atoms": len(atom_indices),
            "count_groups": 1,
            "count_shapes": 0,
            "count_annotations": 0,
        }
    )
    view.active_selection.save("picked")
    view.active_selection.clear()

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "activate_selection",
            "tag": "picked",
            "context": {"event": "interaction_context_menu", "kind": "empty"},
        }
    )

    assert view.active_selection.group_indices == [1]
    assert view._message_history[-1]["op"] == "set_active_selection"  # noqa: SLF001


def test_add_label_from_active_selection_creates_replayable_annotation():
    view = demo["dialanine"]
    atom_indices = list(view.select(selection="group_index==0"))
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": atom_indices,
        "group_indices": [0],
        "component_indices": [],
        "chain_indices": [0],
        "molecule_indices": [],
        "entity_indices": [0],
        "count_atoms": len(atom_indices),
        "count_groups": 1,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001

    layer = view.annotations.add_label_from_active_selection(text="Selected group", tag="picked-label")

    assert layer.tag == "picked-label"
    assert view._annotation_history == [  # noqa: SLF001
        {
            "op": "add_label",
            "tag": "picked-label",
            "options": {
                "text": "Selected group",
                "tag": "picked-label",
                "layer_tag": "picked-label",
                "atom_indices": atom_indices,
            },
        }
    ]


def test_context_action_add_label_from_selection_executes_python_bridge():
    view = demo["dialanine"]
    atom_indices = list(view.select(selection="group_index==0"))
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_active_selection_changed",
            "source_kind": "element",
            "element_level": "group",
            "target_level": "none",
            "items": [],
            "atom_indices": atom_indices,
            "group_indices": [0],
            "component_indices": [],
            "chain_indices": [0],
            "molecule_indices": [],
            "entity_indices": [0],
            "count_atoms": len(atom_indices),
            "count_groups": 1,
            "count_shapes": 0,
            "count_annotations": 0,
        }
    )
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "add_label_from_selection",
            "text": "Picked group",
            "context": {"event": "interaction_context_menu", "kind": "structure", "atom_indices": atom_indices},
        }
    )

    assert len(view._annotation_history) == 1  # noqa: SLF001
    msg = view._annotation_history[0]  # noqa: SLF001
    assert msg["op"] == "add_label"
    assert msg["options"]["text"] == "Picked group"


def test_context_action_delete_annotation_executes_python_bridge():
    view = demo["dialanine"]
    atom_indices = list(view.select(selection="group_index==0"))
    view.annotations.add_label(text="Picked group", group_index=0, tag="picked-label")

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "delete_annotation",
            "tag": "picked-label",
            "context": {
                "event": "interaction_context_menu",
                "kind": "annotation",
                "atom_indices": atom_indices,
                "tag": "picked-label",
                "text": "Picked group",
            },
        }
    )

    assert view.annotations.contains("picked-label") is False
    assert view.annotations.count() == 0
    assert [msg for msg in view._build_export_messages() if msg.get("tag") == "picked-label"] == []  # noqa: SLF001


def test_context_action_delete_shape_executes_python_bridge():
    view = demo["dialanine"]
    view.shapes.add_sphere(center=puw.quantity([0.0, 0.0, 0.0], "nm"), radius=puw.quantity(1.0, "nm"), tag="shape-1")

    assert "shape-1" in view.layers
    assert len(view._shape_history) == 1  # noqa: SLF001

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "delete_shape",
            "tag": "shape-1",
            "context": {
                "event": "interaction_context_menu",
                "kind": "shape",
                "atom_indices": [],
                "tag": "shape-1",
                "shape_name": "Sphere",
            },
        }
    )

    assert "shape-1" not in view.layers
    assert view._shape_history == []  # noqa: SLF001
    assert [msg for msg in view._build_export_messages() if msg.get("tag") == "shape-1"] == []  # noqa: SLF001


def test_context_action_delete_measurement_executes_python_bridge():
    view = demo["dialanine"]
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_measurement_created",
            "action": "distance",
            "picked_count": 2,
            "picks_atom_indices": [[0], [1]],
        }
    )
    view.layers["measurement1"].set_tag("dist-1", skip_digestion=True)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "delete_measurement",
            "tag": "dist-1",
            "context": {
                "event": "interaction_context_menu",
                "kind": "measurement",
                "atom_indices": [0, 1],
                "tag": "dist-1",
            },
        }
    )

    assert "dist-1" not in view.layers
    assert view.measurements.info("dist-1") == []
    assert [msg for msg in view._build_export_messages() if msg.get("tag") == "dist-1"] == []  # noqa: SLF001


def test_context_action_hide_measurement_executes_python_bridge():
    view = demo["dialanine"]
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_measurement_created",
            "action": "distance",
            "picked_count": 2,
            "picks_atom_indices": [[0], [1]],
        }
    )
    view.layers["measurement1"].set_tag("dist-1", skip_digestion=True)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "hide_measurement",
            "tag": "dist-1",
            "context": {
                "event": "interaction_context_menu",
                "kind": "measurement",
                "atom_indices": [0, 1],
                "tag": "dist-1",
            },
        }
    )

    endpoint_labels = list(
        msm.get(view._molsys, element="atom", selection=[0, 1], atom_name=True, skip_digestion=True)  # noqa: SLF001
    )

    assert "dist-1" in view.layers
    assert view.layers["dist-1"]._hidden is True  # noqa: SLF001
    assert view.measurements.info("dist-1") == [
        {
            "kind": "distance",
            "tag": "dist-1",
            "layer_tag": "dist-1",
            "n_picks": 2,
            "picks_atom_indices": [[0], [1]],
            "endpoint_kinds": ["atom", "atom"],
            "endpoint_policy": "centroid",
            "endpoint_labels": endpoint_labels,
            "endpoint_atom_indices": [[0], [1]],
            "value": None,
            "visible": False,
            "active": True,
        }
    ]


def test_add_label_from_active_selection_supports_multi_group():
    view = demo["dialanine"]
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": [0, 1, 2, 3],
        "group_indices": [0, 1],
        "component_indices": [],
        "chain_indices": [0],
        "molecule_indices": [],
        "entity_indices": [0],
        "count_atoms": 4,
        "count_groups": 2,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001
    layer = view.annotations.add_label_from_active_selection(text="Multi-group label")
    assert layer is not None
    records = view.annotations.records()
    assert any(r.get("options", {}).get("text") == "Multi-group label" for r in records)


def test_full_reproducible_workflow_exports_region_selection_label_and_measurement():
    view = demo["dialanine"]
    group_1_atoms = _seed_group_selection(view, 1)
    group_2_atoms = list(view.select(selection="group_index==2"))

    region = view.active_selection.new_region(tag="picked-region", representation="ball_and_stick")
    selection = view.active_selection.save("picked")
    label = view.active_selection.add_label("Picked group", tag="picked-label")
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_measurement_created",
            "action": "distance",
            "picked_count": 2,
            "picks_atom_indices": [[group_1_atoms[0]], [group_2_atoms[0]]],
        }
    )
    measurement = view.layers["measurement1"]
    measurement.set_tag("picked-distance", skip_digestion=True)

    assert region.tag == "picked-region"
    assert selection.tag == "picked"
    assert label.tag == "picked-label"
    assert measurement.tag == "picked-distance"

    messages = view._build_export_messages()  # noqa: SLF001
    ops = [msg["op"] for msg in messages]
    assert "create_region" in ops
    assert "set_region_representation" in ops
    assert "save_selection" in ops
    assert "add_label" in ops
    assert "add_distance_measurement" in ops

    selection_msg = next(msg for msg in messages if msg.get("op") == "save_selection")
    assert selection_msg["tag"] == "picked"
    assert selection_msg["atom_indices"] == group_1_atoms

    label_msg = next(msg for msg in messages if msg.get("op") == "add_label")
    assert label_msg["tag"] == "picked-label"
    assert label_msg["options"]["atom_indices"] == group_1_atoms

    measurement_msg = next(msg for msg in messages if msg.get("op") == "add_distance_measurement")
    assert measurement_msg["tag"] == "picked-distance"
    assert measurement_msg["options"]["picks_atom_indices"] == [[group_1_atoms[0]], [group_2_atoms[0]]]


def test_full_reproducible_workflow_remaps_region_selection_label_and_measurement_on_remove():
    view = demo["dialanine"]
    group_1_atoms = _seed_group_selection(view, 1)
    group_2_atoms = list(view.select(selection="group_index==2"))

    view.active_selection.new_region(tag="picked-region", representation="ball_and_stick")
    view.active_selection.save("picked")
    view.active_selection.add_label("Picked group", tag="picked-label")
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_measurement_created",
            "action": "distance",
            "picked_count": 2,
            "picks_atom_indices": [[group_1_atoms[0]], [group_2_atoms[0]]],
        }
    )
    view.layers["measurement1"].set_tag("picked-distance", skip_digestion=True)

    view.remove(selection="group_index==0")

    remapped_group_0_atoms = list(view.select(selection="group_index==0"))
    remapped_group_1_atoms = list(view.select(selection="group_index==1"))
    endpoint_labels = list(
        msm.get(
            view._molsys,  # noqa: SLF001
            element="atom",
            selection=[remapped_group_0_atoms[0], remapped_group_1_atoms[0]],
            atom_name=True,
            skip_digestion=True,
        )
    )

    assert view.regions["picked-region"].atom_indices == tuple(remapped_group_0_atoms)
    assert view.selections.info("picked")["atom_indices"] == remapped_group_0_atoms
    assert view.selections.info("picked")["group_indices"] == [0]
    assert view.annotations.info("picked-label")["atom_indices"] == remapped_group_0_atoms
    assert view.measurements.info("picked-distance") == [
        {
            "kind": "distance",
            "tag": "picked-distance",
            "layer_tag": "picked-distance",
            "n_picks": 2,
            "picks_atom_indices": [[remapped_group_0_atoms[0]], [remapped_group_1_atoms[0]]],
            "endpoint_kinds": ["atom", "atom"],
            "endpoint_policy": "centroid",
            "endpoint_labels": endpoint_labels,
            "endpoint_atom_indices": [[remapped_group_0_atoms[0]], [remapped_group_1_atoms[0]]],
            "value": None,
            "visible": True,
            "active": True,
        }
    ]

    messages = view._build_export_messages()  # noqa: SLF001
    selection_msg = next(msg for msg in messages if msg.get("op") == "save_selection" and msg.get("tag") == "picked")
    assert selection_msg["atom_indices"] == remapped_group_0_atoms

    label_msg = next(msg for msg in messages if msg.get("op") == "add_label" and msg.get("tag") == "picked-label")
    assert label_msg["options"]["atom_indices"] == remapped_group_0_atoms

    measurement_msg = next(
        msg for msg in messages if msg.get("op") == "add_distance_measurement" and msg.get("tag") == "picked-distance"
    )
    assert measurement_msg["options"]["picks_atom_indices"] == [[remapped_group_0_atoms[0]], [remapped_group_1_atoms[0]]]
