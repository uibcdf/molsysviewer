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
