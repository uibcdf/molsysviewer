from molsysviewer import MolSysView


def test_frontend_interaction_events_are_stored_on_view():
    view = MolSysView()

    hover = {"event": "interaction_hover", "kind": "structure", "atom_indices": [1, 2, 3]}
    click = {"event": "interaction_click", "kind": "empty"}

    view._handle_frontend_event(hover)  # noqa: SLF001
    view._handle_frontend_event(click)  # noqa: SLF001

    assert view.get_last_hover_event() == hover
    assert view.get_last_click_event() == click
