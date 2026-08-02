from molsysviewer import AddonPanelSpec, AddonSpec, AddonSectionSpec, AddonWorkspaceSpec, MolSysView, addons


def test_set_panel_mode_sends_message():
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    sent = []

    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    view.set_panel_mode("navigate")
    view.set_panel_mode("addons")
    view.set_panel_mode(None, expanded=False)

    assert sent == [
        {"op": "set_panel_mode", "panel": "navigate", "expanded": True},
        {"op": "set_panel_mode", "panel": "addons", "expanded": True},
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


def test_set_panel_mode_is_kept_in_test_message_log():
    view = MolSysView(debug_js=True)

    view.set_panel_mode("navigate")
    view.set_panel_mode("addons")
    view.set_panel_mode(None, expanded=False)

    assert view._test_message_log[-3:] == [  # noqa: SLF001
        {"op": "set_panel_mode", "panel": "navigate", "expanded": True},
        {"op": "set_panel_mode", "panel": "addons", "expanded": True},
        {"op": "set_panel_mode", "panel": None, "expanded": False},
    ]


def test_set_workspace_is_kept_in_test_message_log():
    view = MolSysView(debug_js=True)

    view.set_workspace("core")
    view.set_workspace("topomt")

    assert view._test_message_log[-2:] == [  # noqa: SLF001
        {"op": "set_workspace", "workspace": "core"},
        {"op": "set_workspace", "workspace": "topomt"},
    ]


def test_set_workspace_panel_is_kept_in_test_message_log():
    view = MolSysView(debug_js=True)

    view.set_workspace_panel("topo", workspace="topomt")
    view.set_workspace_panel("overview")

    assert view._test_message_log[-2:] == [  # noqa: SLF001
        {"op": "set_workspace_panel", "panel": "topo", "workspace": "topomt"},
        {"op": "set_workspace_panel", "panel": "overview", "workspace": None},
    ]


def test_get_panel_mode_state_returns_last_frontend_state():
    view = MolSysView(debug_js=True)

    payload = {
        "event": "panel_mode_state",
        "panel": "addons",
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


def test_workspace_catalog_and_panels_follow_effective_runtime():
    addons.clear()
    try:
        addons.register(
            AddonSpec(
                name="topomt",
                workspaces=(AddonWorkspaceSpec(id="topomt", title="TopoMT", entry_panel="topo"),),
                panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel.topo"),),
                addon_sections=(
                    AddonSectionSpec(id="summary", title="Summary", entry="topomt.section.summary"),
                ),
            )
        )
        view = MolSysView(debug_js=True)

        assert view.workspace_catalog() == [
            {"id": "core", "title": "Core", "subtitle": "Navigate + Workbench", "active": False},
            {
                "id": "topomt",
                "title": "TopoMT",
                "entry_panel": "topo",
                "description": None,
                "order": 0,
                "meta": {},
                "addon": "topomt",
                "subtitle": "1 panel · 1 section",
                "active": False,
            },
        ]
        assert view.workspace_panels() == [
            {"id": "navigate", "title": "Navigate", "active": False},
            {"id": "addons", "title": "Add-ons", "active": False},
        ]
        assert view.workspace_panels("topomt") == [
            {
                "id": "topo",
                "title": "Topo",
                "description": None,
                "entry": "topomt.panel.topo",
                "addon": "topomt",
                "workspace": "topomt",
                "active": False,
            }
        ]
        assert view.workspace_sections("topomt") == [
            {
                "id": "summary",
                "title": "Summary",
                "entry": "topomt.section.summary",
                "target_panel": "addons",
                "order": 0,
                "meta": {},
                "addon": "topomt",
                "workspace": "topomt",
            }
        ]
        assert view.workspace_sections("core") == []
        assert view.workspace_panels("missing") == []
    finally:
        addons.clear()


def test_workspace_catalog_and_panels_reflect_active_runtime_state():
    addons.clear()
    try:
        addons.register(
            AddonSpec(
                name="topomt",
                workspaces=(AddonWorkspaceSpec(id="topomt", title="TopoMT", entry_panel="topo"),),
                panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel.topo"),),
            )
        )
        view = MolSysView(debug_js=True)
        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "panel_mode_state",
                "panel": "addons",
                "expanded": True,
                "workspace": "topomt",
                "workspace_panel": "topo",
            }
        )

        assert view.workspace_catalog() == [
            {"id": "core", "title": "Core", "subtitle": "Navigate + Workbench", "active": False},
            {
                "id": "topomt",
                "title": "TopoMT",
                "entry_panel": "topo",
                "description": None,
                "order": 0,
                "meta": {},
                "addon": "topomt",
                "subtitle": "1 panel",
                "active": True,
            },
        ]
        assert view.workspace_panels("topomt") == [
            {
                "id": "topo",
                "title": "Topo",
                "description": None,
                "entry": "topomt.panel.topo",
                "addon": "topomt",
                "workspace": "topomt",
                "active": True,
            }
        ]
    finally:
        addons.clear()


def test_workspace_runtime_aggregates_state_catalog_and_current_panels():
    addons.clear()
    try:
        addons.register(
            AddonSpec(
                name="topomt",
                workspaces=(AddonWorkspaceSpec(id="topomt", title="TopoMT", entry_panel="topo"),),
                panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel.topo"),),
            )
        )
        view = MolSysView(debug_js=True)
        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "panel_mode_state",
                "panel": "addons",
                "expanded": True,
                "workspace": "topomt",
                "workspace_panel": "topo",
            }
        )

        assert view.workspace_runtime() == {
            "state": {
                "event": "panel_mode_state",
                "panel": "addons",
                "expanded": True,
                "workspace": "topomt",
                "workspace_panel": "topo",
            },
            "current_workspace": "topomt",
            "current_workspace_record": {
                "id": "topomt",
                "title": "TopoMT",
                "entry_panel": "topo",
                "description": None,
                "order": 0,
                "meta": {},
                "addon": "topomt",
                "subtitle": "1 panel",
                "active": True,
            },
            "workspaces": [
                {"id": "core", "title": "Core", "subtitle": "Navigate + Workbench", "active": False},
                {
                    "id": "topomt",
                    "title": "TopoMT",
                    "entry_panel": "topo",
                    "description": None,
                    "order": 0,
                    "meta": {},
                    "addon": "topomt",
                    "subtitle": "1 panel",
                    "active": True,
                },
            ],
            "current_panels": [
                {
                    "id": "topo",
                    "title": "Topo",
                    "description": None,
                    "entry": "topomt.panel.topo",
                    "addon": "topomt",
                    "workspace": "topomt",
                    "active": True,
                }
            ],
            "current_panel": {
                "id": "topo",
                "title": "Topo",
                "description": None,
                "entry": "topomt.panel.topo",
                "addon": "topomt",
                "workspace": "topomt",
                "active": True,
            },
            "current_sections": [],
        }
    finally:
        addons.clear()


def test_workspace_runtime_includes_current_sections():
    addons.clear()
    try:
        addons.register(
            AddonSpec(
                name="topomt",
                workspaces=(AddonWorkspaceSpec(id="topomt", title="TopoMT", entry_panel="topo"),),
                panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel.topo"),),
                addon_sections=(
                    AddonSectionSpec(id="summary", title="Summary", entry="topomt.section.summary"),
                ),
            )
        )
        view = MolSysView(debug_js=True)
        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "panel_mode_state",
                "panel": "addons",
                "expanded": True,
                "workspace": "topomt",
                "workspace_panel": "topo",
            }
        )

        runtime = view.workspace_runtime()

        assert runtime["current_workspace_record"] == {
            "id": "topomt",
            "title": "TopoMT",
            "entry_panel": "topo",
            "description": None,
            "order": 0,
            "meta": {},
            "addon": "topomt",
            "subtitle": "1 panel · 1 section",
            "active": True,
        }
        assert runtime["current_panel"] == {
            "id": "topo",
            "title": "Topo",
            "description": None,
            "entry": "topomt.panel.topo",
            "addon": "topomt",
            "workspace": "topomt",
            "active": True,
        }
        assert runtime["current_sections"] == [
            {
                "id": "summary",
                "title": "Summary",
                "entry": "topomt.section.summary",
                "target_panel": "addons",
                "order": 0,
                "meta": {},
                "addon": "topomt",
                "workspace": "topomt",
            }
        ]
    finally:
        addons.clear()


def test_workspace_runtime_pretty_returns_json():
    addons.clear()
    try:
        addons.register(
            AddonSpec(
                name="topomt",
                workspaces=(AddonWorkspaceSpec(id="topomt", title="TopoMT", entry_panel="topo"),),
                panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel.topo"),),
                addon_sections=(
                    AddonSectionSpec(id="summary", title="Summary", entry="topomt.section.summary"),
                ),
            )
        )
        view = MolSysView(debug_js=True)
        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "panel_mode_state",
                "panel": "addons",
                "expanded": True,
                "workspace": "topomt",
                "workspace_panel": "topo",
            }
        )

        runtime = view.workspace_runtime(pretty=True)

        assert isinstance(runtime, str)
        assert '"current_workspace": "topomt"' in runtime
        assert '"workspace_panel": "topo"' in runtime
        assert '"current_sections"' in runtime
    finally:
        addons.clear()
