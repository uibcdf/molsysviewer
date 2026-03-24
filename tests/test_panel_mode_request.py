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


def test_set_workspace_sends_message():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    view.set_workspace("core")
    view.set_workspace("topomt")

    assert sent == [
        {"op": "set_workspace", "workspace": "core"},
        {"op": "set_workspace", "workspace": "topomt"},
    ]


def test_set_workspace_panel_sends_message():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    view.set_workspace_panel("topo", workspace="topomt")
    view.set_workspace_panel("overview")

    assert sent == [
        {"op": "set_workspace_panel", "panel": "topo", "workspace": "topomt"},
        {"op": "set_workspace_panel", "panel": "overview", "workspace": None},
    ]


def test_set_panel_mode_is_kept_in_message_history():
    view = MolSysView(debug_js=True)

    view.set_panel_mode("navigate")
    view.set_panel_mode("workbench")
    view.set_panel_mode(None, expanded=False)

    assert view._message_history[-3:] == [  # noqa: SLF001
        {"op": "set_panel_mode", "panel": "navigate", "expanded": True},
        {"op": "set_panel_mode", "panel": "workbench", "expanded": True},
        {"op": "set_panel_mode", "panel": None, "expanded": False},
    ]


def test_set_workspace_is_kept_in_message_history():
    view = MolSysView(debug_js=True)

    view.set_workspace("core")
    view.set_workspace("topomt")

    assert view._message_history[-2:] == [  # noqa: SLF001
        {"op": "set_workspace", "workspace": "core"},
        {"op": "set_workspace", "workspace": "topomt"},
    ]


def test_set_workspace_panel_is_kept_in_message_history():
    view = MolSysView(debug_js=True)

    view.set_workspace_panel("topo", workspace="topomt")
    view.set_workspace_panel("overview")

    assert view._message_history[-2:] == [  # noqa: SLF001
        {"op": "set_workspace_panel", "panel": "topo", "workspace": "topomt"},
        {"op": "set_workspace_panel", "panel": "overview", "workspace": None},
    ]


def test_get_panel_mode_state_returns_last_frontend_state():
    view = MolSysView(debug_js=True)

    payload = {
        "event": "panel_mode_state",
        "panel": "workbench",
        "expanded": True,
        "workspace": "topomt",
        "workspace_panel": "topo",
    }
    view._handle_frontend_event(payload)  # noqa: SLF001

    assert view.get_panel_mode_state() == payload


def test_get_panel_mode_state_pretty_returns_json():
    view = MolSysView(debug_js=True)
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "panel_mode_state",
            "panel": "navigate",
            "expanded": True,
            "workspace": "core",
            "workspace_panel": "navigate",
        }
    )

    pretty = view.get_panel_mode_state(pretty=True)

    assert isinstance(pretty, str)
    assert '"workspace": "core"' in pretty
