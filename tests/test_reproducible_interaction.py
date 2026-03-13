from molsysviewer import demo


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


def test_add_label_from_active_selection_requires_exactly_one_group():
    view = demo["dialanine"]
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": [0, 1],
        "group_indices": [0, 1],
        "component_indices": [],
        "chain_indices": [0],
        "molecule_indices": [],
        "entity_indices": [0],
        "count_atoms": 2,
        "count_groups": 2,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001

    try:
        view.annotations.add_label_from_active_selection(text="bad")
    except ValueError as exc:
        assert "exactly one group" in str(exc)
    else:
        raise AssertionError("Expected ValueError for multi-group active selection")
