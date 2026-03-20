from types import ModuleType
import sys
import importlib

addons_module = importlib.import_module("molsysviewer.addons")
from molsysviewer import (
    AddonContextActionSpec,
    AddonExportHelperSpec,
    AddonPanelSpec,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonStyleHelperSpec,
    AddonToolModeSpec,
    AddonWorkbenchSectionSpec,
    AddonWorkspaceSpec,
    MolSysView,
    addons,
)


def test_global_addons_registry_supports_complete_fake_addon():
    addons.clear()

    addon = AddonSpec(
        name="topomt",
        package="TopoMT",
        version="0.1.0",
        description="Fake topography add-on used to validate the extension platform.",
        workspaces=(
            AddonWorkspaceSpec(
                id="topomt",
                title="TopoMT",
                entry_panel="topo",
                description="Topography workspace",
                order=10,
            ),
        ),
        panels=(
            AddonPanelSpec(
                id="topo",
                title="Topo",
                entry="topomt.panel.topo",
                description="Main cavity/topography panel",
                order=20,
            ),
        ),
        context_actions=(
            AddonContextActionSpec(
                id="focus-pocket",
                title="Focus Pocket",
                entry="topomt.context.focus_pocket",
                target_kinds=("structure", "shape"),
                group="topography",
                order=10,
            ),
        ),
        workbench_sections=(
            AddonWorkbenchSectionSpec(
                id="pockets",
                title="Pockets",
                entry="topomt.workbench.pockets",
                target_panel="workbench",
                order=30,
            ),
        ),
        shape_providers=(
            AddonShapeProviderSpec(
                id="pocket-surface",
                title="Pocket Surface",
                entry="topomt.shapes.pocket_surface",
                kinds=("surface", "cavity"),
                order=40,
            ),
        ),
        style_helpers=(
            AddonStyleHelperSpec(
                id="topography-publication",
                title="Topography Publication",
                entry="topomt.styles.publication",
                tags=("topography-publication",),
                order=50,
            ),
        ),
        export_helpers=(
            AddonExportHelperSpec(
                id="topography-figure",
                title="Topography Figure Export",
                entry="topomt.export.figure",
                formats=("png", "html"),
                order=60,
            ),
        ),
        tool_modes=(
            AddonToolModeSpec(
                id="pocket-pick",
                title="Pocket Pick",
                entry="topomt.tools.pick",
                order=70,
            ),
        ),
        meta={"domain": "topography"},
    )

    addons.register(addon)

    assert addons.contains("topomt") is True
    assert addons.count() == 1
    assert addons.names() == ["topomt"]
    assert addons.available() == ["topomt"]
    assert addons.enabled() == ["topomt"]
    assert addons.get("topomt") == addon

    records = addons.records()
    assert records[0]["name"] == "topomt"
    assert records[0]["enabled"] is True
    assert records[0]["module"] is None
    assert records[0]["meta"] == {"domain": "topography"}
    assert records[0]["workspaces"][0]["id"] == "topomt"
    assert records[0]["panels"][0]["id"] == "topo"
    assert records[0]["context_actions"][0]["id"] == "focus-pocket"
    assert records[0]["workbench_sections"][0]["id"] == "pockets"
    assert records[0]["shape_providers"][0]["id"] == "pocket-surface"
    assert records[0]["style_helpers"][0]["id"] == "topography-publication"
    assert records[0]["export_helpers"][0]["id"] == "topography-figure"
    assert records[0]["tool_modes"][0]["id"] == "pocket-pick"

    assert addons.workspace_specs() == [
        {
            "addon": "topomt",
            "id": "topomt",
            "title": "TopoMT",
            "entry_panel": "topo",
            "description": "Topography workspace",
            "order": 10,
            "meta": {},
        }
    ]
    assert addons.panel_specs() == [
        {
            "addon": "topomt",
            "id": "topo",
            "title": "Topo",
            "entry": "topomt.panel.topo",
            "description": "Main cavity/topography panel",
            "order": 20,
            "target": "panel_mode",
            "meta": {},
        }
    ]
    assert addons.context_action_specs()[0]["addon"] == "topomt"
    assert addons.workbench_section_specs()[0]["target_panel"] == "workbench"
    assert addons.shape_provider_specs()[0]["kinds"] == ["surface", "cavity"]
    assert addons.style_helper_specs()[0]["tags"] == ["topography-publication"]
    assert addons.export_helper_specs()[0]["formats"] == ["png", "html"]
    assert addons.tool_mode_specs()[0]["id"] == "pocket-pick"


def test_view_addons_inherit_global_registry_and_support_local_overrides():
    addons.clear()
    addons.register(
        AddonSpec(
            name="topomt",
            workspaces=(AddonWorkspaceSpec(id="topomt", title="TopoMT", entry_panel="topo"),),
            panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel.topo"),),
        )
    )
    addons.register(
        AddonSpec(
            name="pharmacophoremt",
            panels=(AddonPanelSpec(id="pharma", title="Pharmacophore", entry="pharma.panel"),),
        )
    )
    addons.disable("pharmacophoremt")

    view = MolSysView()

    assert view.addons.available() == ["pharmacophoremt", "topomt"]
    assert view.addons.enabled() == ["topomt"]
    assert view.addons.disabled() == ["pharmacophoremt"]
    assert [record["id"] for record in view.addons.workspace_specs()] == ["topomt"]
    assert [record["id"] for record in view.addons.panel_specs()] == ["topo"]

    view.addons.enable("pharmacophoremt")
    assert view.addons.enabled() == ["pharmacophoremt", "topomt"]
    assert [record["id"] for record in view.addons.panel_specs()] == ["pharma", "topo"]

    view.addons.disable("topomt")
    assert view.addons.enabled() == ["pharmacophoremt"]
    assert view.addons.disabled() == ["topomt"]

    view.addons.reset()
    assert view.addons.enabled() == ["topomt"]
    assert view.addons.disabled() == ["pharmacophoremt"]


def test_addons_can_load_project_config_defaults_and_new_views_inherit_them(tmp_path):
    addons.clear()
    config_path = tmp_path / "_molsysviewer.py"
    config_path.write_text(
        "\n".join(
            [
                "from molsysviewer import Style",
                "",
                'DEFAULT_SCENE_STYLE = Style(preset=\"polymer-cartoon\", name=\"Default Polymer\")',
                "STYLES = {}",
                "ADDONS_ENABLED = ['topomt']",
                "ADDONS_DISABLED = ['pharmacophoremt']",
                "",
            ]
        ),
        encoding="utf-8",
    )

    addons.register(AddonSpec(name="topomt", panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel"),)))
    addons.register(
        AddonSpec(
            name="pharmacophoremt",
            panels=(AddonPanelSpec(id="pharma", title="Pharmacophore", entry="pharma.panel"),),
        )
    )

    result = addons.load_project_config(str(config_path))

    assert result["addons_enabled"] == ["topomt"]
    assert result["addons_disabled"] == ["pharmacophoremt"]
    assert addons.project_enabled_defaults() == ["topomt"]
    assert addons.project_disabled_defaults() == ["pharmacophoremt"]
    assert addons.enabled() == ["topomt"]
    assert addons.disabled() == ["pharmacophoremt"]

    view = MolSysView()
    assert view.addons.enabled() == ["topomt"]
    assert view.addons.disabled() == ["pharmacophoremt"]


def test_addons_project_disabled_defaults_apply_to_later_registrations(tmp_path):
    addons.clear()
    config_path = tmp_path / "_molsysviewer.py"
    config_path.write_text(
        "\n".join(
            [
                "from molsysviewer import Style",
                "",
                'DEFAULT_SCENE_STYLE = Style(preset=\"polymer-cartoon\", name=\"Default Polymer\")',
                "STYLES = {}",
                "ADDONS_DISABLED = ['topomt']",
                "",
            ]
        ),
        encoding="utf-8",
    )

    addons.load_project_config(str(config_path))
    addons.register(AddonSpec(name="topomt", panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel"),)))

    assert addons.enabled() == []
    assert addons.disabled() == ["topomt"]
    assert addons.records()[0]["project_default_disabled"] is True


def test_addons_registry_rejects_duplicate_contribution_ids_within_one_addon():
    try:
        AddonSpec(
            name="broken",
            panels=(
                AddonPanelSpec(id="topo", title="Topo", entry="broken.panel.topo"),
                AddonPanelSpec(id="topo", title="Topo Duplicate", entry="broken.panel.topo_2"),
            ),
        )
    except ValueError as exc:
        assert "duplicate contribution ids" in str(exc)
    else:
        raise AssertionError("Expected duplicate add-on contribution ids to raise ValueError.")


def test_addons_registry_supports_manual_module_registration():
    addons.clear()
    module = ModuleType("molsysviewer_topomt_dev")
    module.addon = AddonSpec(
        name="topomt-dev",
        package="molsysviewer-topomt-dev",
        panels=(AddonPanelSpec(id="topo-dev", title="Topo Dev", entry="topomt.dev.panel"),),
    )
    module.on_enable = lambda view: setattr(view, "_topomt_dev_enabled", True)
    module.on_disable = lambda view: setattr(view, "_topomt_dev_disabled", True)
    module.on_context_action = lambda view, action_id, payload: setattr(view, "_topomt_dev_action", (action_id, payload["addon"]))
    sys.modules[module.__name__] = module
    try:
        addon = addons.register_module(module)
        assert addon.name == "topomt-dev"
        assert addons.available() == ["topomt-dev"]
        assert addons.records()[0]["module"] == "molsysviewer_topomt_dev"
        assert addons.records()[0]["lifecycle"] == {
            "has_on_enable": True,
            "has_on_disable": True,
            "has_on_context_action": True,
        }
    finally:
        sys.modules.pop(module.__name__, None)
        addons.clear()


def test_addons_registry_can_discover_known_modules(monkeypatch):
    addons.clear()
    module = ModuleType("molsysviewer_topomt")

    def _get_addon():
        return AddonSpec(
            name="topomt",
            package="molsysviewer-topomt",
            panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel"),),
        )

    module.get_addon = _get_addon
    sys.modules[module.__name__] = module
    monkeypatch.setattr(addons_module, "KNOWN_ADDON_MODULES", ("molsysviewer_topomt", "molsysviewer_missing"))
    try:
        discovered = addons.discover()
        assert [item.name for item in discovered] == ["topomt"]
        assert addons.known_modules() == ["molsysviewer_topomt", "molsysviewer_missing"]
        assert addons.records()[0]["module"] == "molsysviewer_topomt"
    finally:
        sys.modules.pop(module.__name__, None)
        addons.clear()


def test_addon_template_module_is_importable_and_registerable():
    addons.clear()
    try:
        addon = addons.register_module("molsysviewer.addon_templates.minimal_topomt")
        assert addon.name == "topomt-template"
        assert addons.available() == ["topomt-template"]
        assert addons.workspace_specs()[0]["id"] == "topomt"
        assert addons.panel_specs()[0]["id"] == "topo"
        assert addons.context_action_specs()[0]["id"] == "focus-pocket"
        assert addons.workbench_section_specs()[0]["id"] == "pockets"
        assert addons.shape_provider_specs()[0]["id"] == "pocket-surface"
        assert addons.lifecycle_for("topomt-template") is not None
        assert addons.lifecycle_for("topomt-template").info() == {
            "has_on_enable": True,
            "has_on_disable": True,
            "has_on_context_action": True,
        }
    finally:
        addons.clear()


def test_addon_template_module_has_visible_runtime_lifecycle_flow():
    addons.clear()
    try:
        addons.register_module("molsysviewer.addon_templates.minimal_topomt")
        view = MolSysView(debug_js=True)

        assert view._topomt_template_enabled is True
        assert ("enable", "topomt-template") in view._topomt_template_events

        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "interaction_context_action",
                "action": "addon_context_action",
                "addon": "topomt-template",
                "addon_action_id": "focus-pocket",
                "addon_action_title": "Focus Pocket",
                "context": {"kind": "structure", "atom_indices": [1, 2, 3]},
            }
        )

        assert view._topomt_template_last_context_action["action_id"] == "focus-pocket"
        assert view._topomt_template_last_context_action["payload"]["addon"] == "topomt-template"
        assert ("context", "focus-pocket") in view._topomt_template_events

        view.addons.disable("topomt-template")
        assert view._topomt_template_enabled is False
        assert ("disable", "topomt-template") in view._topomt_template_events
    finally:
        addons.clear()


def test_view_addons_run_lifecycle_hooks_on_init_toggle_and_reset():
    addons.clear()
    events: list[str] = []

    def _on_enable(view):
        events.append("enable")
        view._addon_marker = "enabled"

    def _on_disable(view):
        events.append("disable")
        view._addon_marker = "disabled"

    addons.register(
        AddonSpec(
            name="lifecycle-addon",
            panels=(AddonPanelSpec(id="life", title="Life", entry="life.panel"),),
        ),
        lifecycle=addons_module.AddonLifecycleSpec(on_enable=_on_enable, on_disable=_on_disable),
    )

    view = MolSysView()
    assert events == ["enable"]
    assert view._addon_marker == "enabled"

    view.addons.disable("lifecycle-addon")
    assert events == ["enable", "disable"]
    assert view._addon_marker == "disabled"

    view.addons.enable("lifecycle-addon")
    assert events == ["enable", "disable", "enable"]
    assert view._addon_marker == "enabled"

    view.addons.reset()
    assert events == ["enable", "disable", "enable"]

    addons.disable("lifecycle-addon")
    another_view = MolSysView()
    assert events == ["enable", "disable", "enable"]
    assert another_view.addons.enabled() == []
    addons.clear()


def test_view_addons_handle_context_action_through_lifecycle():
    addons.clear()
    events: list[tuple[str, str, str]] = []

    def _on_context_action(view, action_id, payload):
        events.append((view.__class__.__name__, action_id, payload["addon"]))
        view._addon_context_action = payload

    addons.register(
        AddonSpec(
            name="topomt",
            context_actions=(
                AddonContextActionSpec(
                    id="focus-pocket",
                    title="Focus Pocket",
                    entry="topomt.context.focus_pocket",
                    target_kinds=("structure",),
                ),
            ),
        ),
        lifecycle=addons_module.AddonLifecycleSpec(on_context_action=_on_context_action),
    )

    view = MolSysView()
    handled = view.addons.handle_context_action(
        "topomt",
        "focus-pocket",
        {
            "event": "interaction_context_action",
            "action": "addon_context_action",
            "addon": "topomt",
            "addon_action_id": "focus-pocket",
            "context": {"kind": "structure", "atom_indices": [0, 1, 2]},
        },
    )

    assert handled is True
    assert events == [("MolSysView", "focus-pocket", "topomt")]
    assert view._addon_context_action["addon_action_id"] == "focus-pocket"
    addons.clear()


def test_view_handles_frontend_addon_context_action_event():
    addons.clear()
    events: list[tuple[str, str]] = []

    def _on_context_action(view, action_id, payload):
        events.append((action_id, payload["addon"]))
        view._last_addon_context_payload = payload

    addons.register(
        AddonSpec(
            name="topomt",
            context_actions=(
                AddonContextActionSpec(
                    id="focus-pocket",
                    title="Focus Pocket",
                    entry="topomt.context.focus_pocket",
                    target_kinds=("structure",),
                ),
            ),
        ),
        lifecycle=addons_module.AddonLifecycleSpec(on_context_action=_on_context_action),
    )

    view = MolSysView(debug_js=True)
    payload = {
        "event": "interaction_context_action",
        "action": "addon_context_action",
        "addon": "topomt",
        "addon_action_id": "focus-pocket",
        "addon_action_title": "Focus Pocket",
        "context": {"kind": "structure", "atom_indices": [3, 4, 5]},
    }

    view._handle_frontend_event(payload)  # noqa: SLF001

    assert events == [("focus-pocket", "topomt")]
    assert view.get_last_context_action_event()["addon"] == "topomt"
    assert view._last_addon_context_payload["context"]["kind"] == "structure"
    addons.clear()


def test_view_addons_sync_runtime_summary_message():
    addons.clear()
    view = MolSysView()
    sent: list[dict] = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]
    try:
        addons.register(
            AddonSpec(
                name="topomt",
                workspaces=(
                    AddonWorkspaceSpec(
                        id="topomt",
                        title="TopoMT",
                        entry_panel="topo",
                    ),
                ),
                panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel.topo"),),
                context_actions=(
                    AddonContextActionSpec(
                        id="focus-pocket",
                        title="Focus Pocket",
                        entry="topomt.context.focus_pocket",
                        target_kinds=("structure", "shape"),
                    ),
                ),
                workbench_sections=(
                    AddonWorkbenchSectionSpec(
                        id="pockets",
                        title="Pockets",
                        entry="topomt.workbench.pockets",
                    ),
                ),
                export_helpers=(
                    AddonExportHelperSpec(
                        id="topography-figure",
                        title="Topography Figure Export",
                        entry="topomt.export.figure",
                        formats=("png",),
                    ),
                ),
            )
        )
        view.addons.enable("topomt")
        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["addons"] == ["topomt"]
        assert addon_msg["workspace_specs"][0]["title"] == "TopoMT"
        assert addon_msg["panel_specs"][0]["title"] == "Topo"
        assert addon_msg["context_action_specs"][0]["id"] == "focus-pocket"
        assert addon_msg["workbench_sections"][0]["title"] == "Pockets"
        assert addon_msg["export_helper_specs"][0]["title"] == "Topography Figure Export"

        view.addons.disable("topomt")
        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["addons"] == []
        assert addon_msg["workspace_specs"] == []
        assert addon_msg["panel_specs"] == []
        assert addon_msg["context_action_specs"] == []
        assert addon_msg["workbench_sections"] == []
        assert addon_msg["export_helper_specs"] == []
    finally:
        addons.clear()
