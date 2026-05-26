from types import ModuleType
import sys
import importlib

addons_module = importlib.import_module("molsysviewer.addons")
from molsysviewer import (
    AddonContextActionSpec,
    AddonExportHelperSpec,
    AddonPanelSpec,
    AddonPanelWidget,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonStyleHelperSpec,
    AddonToolModeSpec,
    AddonWorkbenchSectionSpec,
    AddonWorkspaceSpec,
    MolSysView,
    addon_templates,
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
            "widget_class": None,
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

    from importlib.machinery import ModuleSpec
    module.get_addon = _get_addon
    module.__spec__ = ModuleSpec(module.__name__, None)
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


def test_addons_registry_emits_smonitor_warning_on_discovery_failure(monkeypatch):
    import smonitor
    addons.clear()
    module = ModuleType("molsysviewer_topomt")

    def _get_addon():
        raise ValueError("Simulated load failure")

    from importlib.machinery import ModuleSpec
    module.get_addon = _get_addon
    module.__spec__ = ModuleSpec(module.__name__, None)
    sys.modules[module.__name__] = module
    monkeypatch.setattr(addons_module, "KNOWN_ADDON_MODULES", ("molsysviewer_topomt",))

    manager = smonitor.get_manager()
    before_warnings = manager.report().get("warnings_total", 0)

    try:
        discovered = addons.discover()
        assert len(discovered) == 0
        after_warnings = manager.report().get("warnings_total", 0)
        assert after_warnings == before_warnings + 1
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
        assert [item["id"] for item in addons.panel_specs()] == ["topo", "channels", "regions"]
        assert [item["id"] for item in addons.context_action_specs()] == ["focus-pocket", "inspect-channel"]
        assert [item["id"] for item in addons.workbench_section_specs()] == ["pockets", "channels"]
        assert addons.shape_provider_specs()[0]["id"] == "pocket-surface"
        assert addons.export_helper_specs()[0]["id"] == "topography-figure"
        assert addons.lifecycle_for("topomt-template") is not None
        assert addons.lifecycle_for("topomt-template").info() == {
            "has_on_enable": True,
            "has_on_disable": True,
            "has_on_context_action": True,
        }
    finally:
        addons.clear()


def test_elasnetmt_addon_template_module_is_importable_and_registerable():
    addons.clear()
    try:
        addon = addons.register_module("molsysviewer.addon_templates.minimal_elasnetmt")
        assert addon.name == "elasnetmt-template"
        assert addons.available() == ["elasnetmt-template"]
        assert addons.workspace_specs()[0]["id"] == "elasnetmt"
        assert [item["id"] for item in addons.panel_specs()] == ["model", "modes", "figures"]
        assert [item["id"] for item in addons.context_action_specs()] == ["show-contact-network", "show-mode-vectors"]
        assert [item["id"] for item in addons.workbench_section_specs()] == ["modes", "network-overlays"]
        assert [item["id"] for item in addons.shape_provider_specs()] == ["contact-links", "mode-ellipsoids"]
        assert addons.export_helper_specs()[0]["id"] == "enm-figure"
        assert addons.lifecycle_for("elasnetmt-template") is not None
        assert addons.lifecycle_for("elasnetmt-template").info() == {
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
        assert view._topomt_template_runtime["enabled"] is True
        assert view._topomt_template_runtime["workspace"] == "topomt"
        assert view._topomt_template_runtime["panels"] == ["topo", "channels", "regions"]
        assert view._topomt_template_runtime["sections"] == ["pockets", "channels"]
        assert view._topomt_template_runtime["context_actions"] == ["focus-pocket", "inspect-channel"]
        assert view._topomt_template_runtime["export_helpers"] == ["topography-figure"]

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
        assert view._topomt_template_runtime["last_context_action"]["action_id"] == "focus-pocket"
        assert ("context", "focus-pocket") in view._topomt_template_events

        view.addons.disable("topomt-template")
        assert view._topomt_template_enabled is False
        assert view._topomt_template_runtime["enabled"] is False
        assert ("disable", "topomt-template") in view._topomt_template_events
    finally:
        addons.clear()


def test_elasnetmt_addon_template_module_has_visible_runtime_lifecycle_flow():
    addons.clear()
    try:
        addons.register_module("molsysviewer.addon_templates.minimal_elasnetmt")
        view = MolSysView(debug_js=True)

        assert view._elasnetmt_template_enabled is True
        assert ("enable", "elasnetmt-template") in view._elasnetmt_template_events
        assert view._elasnetmt_template_runtime["enabled"] is True
        assert view._elasnetmt_template_runtime["workspace"] == "elasnetmt"
        assert view._elasnetmt_template_runtime["panels"] == ["model", "modes", "figures"]
        assert view._elasnetmt_template_runtime["sections"] == ["modes", "network-overlays"]
        assert view._elasnetmt_template_runtime["context_actions"] == ["show-contact-network", "show-mode-vectors"]
        assert view._elasnetmt_template_runtime["export_helpers"] == ["enm-figure"]

        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "interaction_context_action",
                "action": "addon_context_action",
                "addon": "elasnetmt-template",
                "addon_action_id": "show-mode-vectors",
                "addon_action_title": "Show Mode Vectors",
                "context": {"kind": "structure", "atom_indices": [1, 2, 3]},
            }
        )

        assert view._elasnetmt_template_last_context_action["action_id"] == "show-mode-vectors"
        assert view._elasnetmt_template_last_context_action["payload"]["addon"] == "elasnetmt-template"
        assert view._elasnetmt_template_runtime["last_context_action"]["action_id"] == "show-mode-vectors"
        assert ("context", "show-mode-vectors") in view._elasnetmt_template_events

        view.addons.disable("elasnetmt-template")
        assert view._elasnetmt_template_enabled is False
        assert view._elasnetmt_template_runtime["enabled"] is False
        assert ("disable", "elasnetmt-template") in view._elasnetmt_template_events
    finally:
        addons.clear()


def test_addon_template_module_syncs_richer_runtime_summary_message():
    addons.clear()
    view = MolSysView()
    sent: list[dict] = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]
    try:
        addons.register_module("molsysviewer.addon_templates.minimal_topomt")
        view.addons.enable("topomt-template")
        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["addons"] == ["topomt-template"]
        assert [item["id"] for item in addon_msg["panel_specs"]] == ["topo", "channels", "regions"]
        assert [item["id"] for item in addon_msg["context_action_specs"]] == ["focus-pocket", "inspect-channel"]
        assert [item["id"] for item in addon_msg["workbench_sections"]] == ["pockets", "channels"]
        assert [item["id"] for item in addon_msg["export_helper_specs"]] == ["topography-figure"]
    finally:
        addons.clear()


def test_addon_templates_helper_lists_and_registers_reference_addons():
    addons.clear()
    try:
        assert addon_templates.list_reference_addons() == ["elasnetmt", "topomt"]
        assert addon_templates.resolve_reference_addon("elasnetmt") == "molsysviewer.addon_templates.minimal_elasnetmt"
        assert addon_templates.resolve_reference_addon("minimal_elasnetmt") == "molsysviewer.addon_templates.minimal_elasnetmt"
        assert addon_templates.resolve_reference_addon("topomt") == "molsysviewer.addon_templates.minimal_topomt"
        assert addon_templates.resolve_reference_addon("minimal_topomt") == "molsysviewer.addon_templates.minimal_topomt"

        addon = addon_templates.register_reference_addon("elasnetmt")
        assert addon.name == "elasnetmt-template"
        assert addons.available() == ["elasnetmt-template"]

        imported = addon_templates.import_reference_module("elasnetmt")
        assert imported.__name__ == "molsysviewer.addon_templates.minimal_elasnetmt"
    finally:
        addons.clear()


def test_addon_templates_helper_can_register_all_reference_addons():
    addons.clear()
    try:
        registered = addon_templates.register_all_reference_addons()
        assert [item.name for item in registered] == ["elasnetmt-template", "topomt-template"]
        assert addons.available() == ["elasnetmt-template", "topomt-template"]
    finally:
        addons.clear()


def test_addon_templates_helper_can_build_reference_demo_view():
    addons.clear()
    try:
        view = addon_templates.build_reference_demo_view("topomt")
        assert view.addons.enabled() == ["topomt-template"]
        assert [item["id"] for item in view.addons.workspace_specs()] == ["topomt"]
        assert [item["id"] for item in view.addons.panel_specs()] == ["topo", "channels", "regions"]
        assert view._topomt_template_enabled is True
        assert view._topomt_template_runtime["workspace"] == "topomt"
        assert view._topomt_template_runtime["panels"] == ["topo", "channels", "regions"]
        messages = view._message_history  # noqa: SLF001
        assert next(msg for msg in reversed(messages) if msg.get("op") == "set_panel_mode") == {
            "op": "set_panel_mode",
            "panel": "workbench",
            "expanded": True,
        }
        assert next(msg for msg in reversed(messages) if msg.get("op") == "set_workspace") == {
            "op": "set_workspace",
            "workspace": "topomt",
        }
        assert next(msg for msg in reversed(messages) if msg.get("op") == "set_workspace_panel") == {
            "op": "set_workspace_panel",
            "panel": "topo",
            "workspace": "topomt",
        }

        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "panel_mode_state",
                "panel": "workbench",
                "expanded": True,
                "workspace": "topomt",
                "workspace_panel": "topo",
            }
        )
        runtime = view.workspace_runtime()
        assert runtime["current_workspace"] == "topomt"
        assert runtime["current_workspace_record"]["id"] == "topomt"
        assert runtime["current_panel"]["id"] == "topo"
        assert [item["id"] for item in runtime["current_panels"]] == ["topo", "channels", "regions"]
        assert [item["id"] for item in runtime["current_sections"]] == ["pockets", "channels"]
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


def test_view_addons_materialize_workbench_and_export_entry_payloads():
    addons.clear()
    module = ModuleType("fake_addon_runtime")

    def _workbench(view):
        count = getattr(view, "_fake_overlay_count", 0)
        return {
            "key": "fake:workbench",
            "item_title": f"{count} overlays",
            "item_subtitle": "runtime from python entry",
        }

    def _export(view):
        count = getattr(view, "_fake_overlay_count", 0)
        return {
            "title": "Fake Export",
            "figure_recipe": {"overlay_count": count},
        }

    module.workbench = _workbench
    module.export = _export
    sys.modules[module.__name__] = module

    sent: list[dict] = []
    view = MolSysView()
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    try:
        addons.register(
            AddonSpec(
                name="runtime-addon",
                workspaces=(AddonWorkspaceSpec(id="runtime", title="Runtime", entry_panel="panel"),),
                panels=(AddonPanelSpec(id="panel", title="Panel", entry="runtime.panel"),),
                workbench_sections=(
                    AddonWorkbenchSectionSpec(
                        id="summary",
                        title="Summary",
                        entry="fake_addon_runtime.workbench",
                    ),
                ),
                export_helpers=(
                    AddonExportHelperSpec(
                        id="figure",
                        title="Figure",
                        entry="fake_addon_runtime.export",
                        formats=("html",),
                    ),
                ),
            )
        )
        view.addons.enable("runtime-addon")

        sections = view.workspace_sections("runtime")
        assert sections[0]["item_title"] == "0 overlays"
        assert sections[0]["runtime_payload"]["item_subtitle"] == "runtime from python entry"

        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["workbench_sections"][0]["runtime_payload"]["item_title"] == "0 overlays"
        assert addon_msg["export_helper_specs"][0]["runtime_payload"]["figure_recipe"]["overlay_count"] == 0
    finally:
        addons.clear()
        sys.modules.pop(module.__name__, None)


def test_view_addons_refresh_runtime_summary_after_context_action():
    addons.clear()
    module = ModuleType("fake_addon_runtime_refresh")

    def _workbench(view):
        count = getattr(view, "_fake_overlay_count", 0)
        return {"key": "fake:workbench", "item_title": f"{count} overlays"}

    module.workbench = _workbench
    sys.modules[module.__name__] = module

    def _on_context_action(view, action_id, payload):
        view._fake_overlay_count = getattr(view, "_fake_overlay_count", 0) + 1

    sent: list[dict] = []
    view = MolSysView(debug_js=True)
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]

    try:
        addons.register(
            AddonSpec(
                name="runtime-addon",
                workspaces=(AddonWorkspaceSpec(id="runtime", title="Runtime", entry_panel="panel"),),
                panels=(AddonPanelSpec(id="panel", title="Panel", entry="runtime.panel"),),
                context_actions=(
                    AddonContextActionSpec(
                        id="increment",
                        title="Increment",
                        entry="runtime.increment",
                        target_kinds=("structure",),
                    ),
                ),
                workbench_sections=(
                    AddonWorkbenchSectionSpec(
                        id="summary",
                        title="Summary",
                        entry="fake_addon_runtime_refresh.workbench",
                    ),
                ),
            ),
            lifecycle=addons_module.AddonLifecycleSpec(on_context_action=_on_context_action),
        )
        view.addons.enable("runtime-addon")
        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "interaction_context_action",
                "action": "addon_context_action",
                "addon": "runtime-addon",
                "addon_action_id": "increment",
                "context": {"kind": "structure", "atom_indices": [0]},
            }
        )

        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["workbench_sections"][0]["runtime_payload"]["item_title"] == "1 overlays"
    finally:
        addons.clear()
        sys.modules.pop(module.__name__, None)


# ---------------------------------------------------------------------------
# AddonPanelWidget
# ---------------------------------------------------------------------------

class _EchoPanel(AddonPanelWidget):
    _esm = "export function render() {}"

    def __init__(self, view=None, **kwargs):
        super().__init__(view=view, **kwargs)
        self.mounted_views = []
        self.unmounted_views = []
        self.received_actions = []

    def handle_action(self, view, action_id, payload):
        self.received_actions.append((action_id, payload))

    def on_mount(self, view):
        self.mounted_views.append(view)

    def on_unmount(self, view):
        self.unmounted_views.append(view)


def test_addon_panel_widget_is_subclass():
    import anywidget
    assert issubclass(AddonPanelWidget, anywidget.AnyWidget)
    assert issubclass(_EchoPanel, AddonPanelWidget)


def test_addon_panel_widget_push_state_sends_message():
    sent = []
    panel = _EchoPanel(view=None)
    panel.send = lambda msg, buffers=None: sent.append(msg)

    panel.push_state({"n_nodes": 42, "cutoff": "7.5 angstroms"})

    assert len(sent) == 1
    assert sent[0] == {"type": "state", "state": {"n_nodes": 42, "cutoff": "7.5 angstroms"}}


def test_addon_panel_widget_request_context_no_view():
    sent = []
    panel = _EchoPanel(view=None)
    panel.send = lambda msg, buffers=None: sent.append(msg)

    ctx = panel.request_context()

    assert ctx == {"has_system": False}
    assert sent[0] == {"type": "context", "context": {"has_system": False}}


def test_addon_panel_widget_routes_action_message():
    panel = _EchoPanel(view="fake-view")
    panel._route_frontend_message(panel, {"type": "action", "id": "compute", "payload": {"cutoff": 7.5}}, [])

    assert panel.received_actions == [("compute", {"cutoff": 7.5})]


def test_addon_panel_widget_routes_context_query():
    sent = []
    panel = _EchoPanel(view=None)
    panel.send = lambda msg, buffers=None: sent.append(msg)

    panel._route_frontend_message(panel, {"type": "query", "id": "viewer.context"}, [])

    assert len(sent) == 1
    assert sent[0]["type"] == "context"
    assert sent[0]["context"]["has_system"] is False


def test_addon_panel_widget_lifecycle_hooks():
    panel = _EchoPanel(view=None)
    panel.on_mount("view-a")
    panel.on_unmount("view-a")

    assert panel.mounted_views == ["view-a"]
    assert panel.unmounted_views == ["view-a"]


def test_addon_panel_spec_widget_class_field():
    spec = AddonPanelSpec(
        id="model",
        title="Model",
        entry="myaddon.panels.model",
        widget_class="myaddon.panels.ModelPanel",
    )
    assert spec.widget_class == "myaddon.panels.ModelPanel"
    info = spec.info()
    assert info["widget_class"] == "myaddon.panels.ModelPanel"


def test_addon_panel_spec_widget_class_optional():
    spec = AddonPanelSpec(id="model", title="Model")
    assert spec.widget_class is None
    assert spec.info()["widget_class"] is None


def test_resolve_panel_widget_returns_none_when_no_widget_class():
    addons.clear()
    try:
        addon = AddonSpec(
            name="nopanel-addon",
            package="NoPanelAddon",
            version="0.1.0",
            description="Addon without widget_class",
            panels=(
                AddonPanelSpec(id="main", title="Main", entry="nopanel.panels.main"),
            ),
        )
        addons.register(addon)
        view = MolSysView.__new__(MolSysView)
        from molsysviewer.addons import ViewAddonsManager
        mgr = ViewAddonsManager(view, addons)
        result = mgr.resolve_panel_widget("nopanel-addon", "main")
        assert result is None
    finally:
        addons.clear()


def test_resolve_panel_widget_returns_instance():
    import types
    addons.clear()
    module = types.ModuleType("_test_panel_mod")

    class _TestPanel(AddonPanelWidget):
        _esm = "export function render() {}"

    module._TestPanel = _TestPanel
    sys.modules[module.__name__] = module

    try:
        addon = AddonSpec(
            name="panel-addon",
            package="PanelAddon",
            version="0.1.0",
            description="Addon with widget_class",
            panels=(
                AddonPanelSpec(
                    id="main",
                    title="Main",
                    widget_class="_test_panel_mod._TestPanel",
                ),
            ),
        )
        addons.register(addon)
        view = MolSysView.__new__(MolSysView)
        from molsysviewer.addons import ViewAddonsManager
        mgr = ViewAddonsManager(view, addons)
        widget = mgr.resolve_panel_widget("panel-addon", "main")
        assert isinstance(widget, AddonPanelWidget)
        assert widget._view is view
    finally:
        addons.clear()
        sys.modules.pop(module.__name__, None)
