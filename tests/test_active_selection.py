from molsysviewer import demo


def _seed_group_selection(view, group_index=1):
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


def test_active_selection_exposes_current_payload_and_helpers():
    view = demo["dialanine"]
    atom_indices = _seed_group_selection(view, 1)

    assert view.active_selection.source_kind == "element"
    assert view.active_selection.element_level == "group"
    assert view.active_selection.target_level == "none"
    assert view.active_selection.atom_indices == atom_indices
    assert view.active_selection.group_indices == [1]
    assert view.active_selection.chain_indices == [0]
    assert view.active_selection.entity_indices == [0]
    assert view.active_selection.is_empty() is False
    assert view.active_selection.info()["atom_indices"] == atom_indices


def test_active_selection_clear_resets_python_state_and_emits_frontend_message():
    view = demo["dialanine"]
    _seed_group_selection(view, 1)

    view.active_selection.clear()

    assert view.active_selection.is_empty() is True
    assert view.get_last_active_selection_event()["source_kind"] == "empty"
    assert view._message_history[-1]["op"] == "clear_active_selection"  # noqa: SLF001


def test_active_selection_focus_new_region_and_add_label_delegate_to_reproducible_apis():
    view = demo["dialanine"]
    atom_indices = _seed_group_selection(view, 1)

    view.active_selection.focus(duration_ms=50)
    assert view._message_history[-1]["op"] == "zoom"  # noqa: SLF001
    assert view._message_history[-1]["atom_indices"] == atom_indices  # noqa: SLF001

    region = view.active_selection.new_region(tag="picked", representation="ball_and_stick")
    assert region.tag == "picked"
    assert "picked" in view.regions

    layer = view.active_selection.add_label("Selected", tag="picked-label")
    assert layer.tag == "picked-label"
    assert view.annotations.contains("picked-label") is True
