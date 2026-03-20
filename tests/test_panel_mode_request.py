from molsysviewer import MolSysView


def test_set_panel_mode_sends_message():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    view.set_panel_mode("navigate")
    view.set_panel_mode("workbench")
    view.set_panel_mode(None, expanded=False)

    assert sent == [
        {"op": "set_panel_mode", "panel": "navigate", "expanded": True},
        {"op": "set_panel_mode", "panel": "workbench", "expanded": True},
        {"op": "set_panel_mode", "panel": None, "expanded": False},
    ]
