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
