from molsysviewer import demo


def test_build_export_messages_captures_reproducible_workbench_state_end_to_end():
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

    region = view.new_region_from_active_selection(tag="picked", representation="ball_and_stick")
    assert region.tag == "picked"

    label_layer = view.annotations.add_label_from_active_selection(text="Seed", tag="notes")
    assert label_layer.tag == "notes"
    view.annotations.set_text("notes", "Edited")

    dist = view.measurements.add_distance([0], [1], tag="dist")
    ang = view.measurements.add_angle([0], [1], [2], tag="ang")
    dih = view.measurements.add_dihedral([0], [1], [2], [3], tag="dih")
    assert dist.tag == "dist"
    assert ang.tag == "ang"
    assert dih.tag == "dih"

    view.set_camera_snapshot(
        {
            "target": [1.0, 2.0, 3.0],
            "position": [4.0, 5.0, 6.0],
            "up": [0.0, 1.0, 0.0],
        },
        duration_ms=125,
    )

    messages = view._build_export_messages()  # noqa: SLF001
    ops = [msg["op"] for msg in messages]

    assert ops[0] == "load_molsys_payload"
    assert "create_region" in ops
    assert "set_region_representation" in ops
    assert "add_label" in ops
    assert "update_label" in ops
    assert "add_distance_measurement" in ops
    assert "add_angle_measurement" in ops
    assert "add_dihedral_measurement" in ops
    assert ops[-1] == "set_camera_snapshot"

    region_msg = next(msg for msg in messages if msg.get("op") == "create_region" and msg.get("tag") == "picked")
    assert region_msg["atom_indices"] == atom_indices

    region_repr_msg = next(
        msg for msg in messages if msg.get("op") == "set_region_representation" and msg.get("tag") == "picked"
    )
    assert region_repr_msg["representation"] == "ball-and-stick"

    label_msgs = [msg for msg in messages if msg.get("tag") == "notes"]
    assert [msg["op"] for msg in label_msgs] == ["add_label", "update_label"]
    assert label_msgs[0]["options"]["text"] == "Seed"
    assert label_msgs[1]["options"]["text"] == "Edited"
    assert label_msgs[0]["options"]["atom_indices"] == atom_indices
    assert label_msgs[1]["options"]["atom_indices"] == atom_indices

    distance_msg = next(msg for msg in messages if msg.get("tag") == "dist")
    angle_msg = next(msg for msg in messages if msg.get("tag") == "ang")
    dihedral_msg = next(msg for msg in messages if msg.get("tag") == "dih")
    assert distance_msg["op"] == "add_distance_measurement"
    assert distance_msg["options"]["picks_atom_indices"] == [[0], [1]]
    assert angle_msg["op"] == "add_angle_measurement"
    assert angle_msg["options"]["picks_atom_indices"] == [[0], [1], [2]]
    assert dihedral_msg["op"] == "add_dihedral_measurement"
    assert dihedral_msg["options"]["picks_atom_indices"] == [[0], [1], [2], [3]]

    camera_msg = messages[-1]
    assert camera_msg == {
        "op": "set_camera_snapshot",
        "snapshot": {
            "target": [1.0, 2.0, 3.0],
            "position": [4.0, 5.0, 6.0],
            "up": [0.0, 1.0, 0.0],
        },
        "duration_ms": 125,
    }
