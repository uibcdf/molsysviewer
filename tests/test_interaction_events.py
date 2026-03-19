from molsysviewer import MolSysView


def test_frontend_interaction_events_are_stored_on_view():
    view = MolSysView()

    hover = {"event": "interaction_hover", "kind": "structure", "atom_indices": [1, 2, 3]}
    click = {"event": "interaction_click", "kind": "empty"}
    context = {"event": "interaction_context_menu", "kind": "structure", "atom_indices": [4], "page_x": 10, "page_y": 20}
    action = {"event": "interaction_context_action", "action": "distance", "context": context}
    active_selection = {"event": "interaction_active_selection_changed", "source_kind": "element", "atom_indices": [4]}
    tool_state = {"event": "interaction_tool_state", "action": "distance", "status": "started", "picked_count": 1}
    measurement = {"event": "interaction_measurement_created", "action": "distance", "picked_count": 2}

    view._handle_frontend_event(hover)  # noqa: SLF001
    view._handle_frontend_event(click)  # noqa: SLF001
    view._handle_frontend_event(context)  # noqa: SLF001
    view._handle_frontend_event(action)  # noqa: SLF001
    view._handle_frontend_event(active_selection)  # noqa: SLF001
    view._handle_frontend_event(tool_state)  # noqa: SLF001
    view._handle_frontend_event(measurement)  # noqa: SLF001

    assert view.get_last_hover_event() == hover
    assert view.get_last_click_event() == click
    assert view.get_last_context_event() == context
    assert view.get_last_context_action_event() == action
    assert view.get_last_active_selection_event() == active_selection
    assert view.get_last_tool_state_event() == tool_state
    assert view.get_last_measurement_created_event() == measurement


def test_hover_and_context_targets_expose_lightweight_public_wrappers():
    view = MolSysView()

    assert view.hover_target.is_empty() is True
    assert view.context_target.is_empty() is True

    hover = {"event": "interaction_hover", "kind": "structure", "atom_indices": [1, 2, 3]}
    context = {
        "event": "interaction_context_menu",
        "kind": "annotation",
        "atom_indices": [4],
        "tag": "note-1",
        "text": "Catalytic",
        "page_x": 10,
        "page_y": 20,
    }

    view._handle_frontend_event(hover)  # noqa: SLF001
    view._handle_frontend_event(context)  # noqa: SLF001

    assert view.hover_target.kind == "structure"
    assert view.hover_target.atom_indices == [1, 2, 3]
    assert view.hover_target.info() == hover

    assert view.context_target.kind == "annotation"
    assert view.context_target.atom_indices == [4]
    assert view.context_target.tag == "note-1"
    assert view.context_target.text == "Catalytic"
    assert view.context_target.page_x == 10
    assert view.context_target.page_y == 20
    assert view.context_target.info() == context
