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
    AddonSectionSpec,
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
        addon_sections=(
            AddonSectionSpec(
                id="pockets",
                title="Pockets",
                entry="topomt.workbench.pockets",
                target_panel="addons",
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
    assert records[0]["addon_sections"][0]["id"] == "pockets"
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
    assert addons.addon_section_specs()[0]["target_panel"] == "addons"
    assert addons.shape_provider_specs()[0]["kinds"] == ["surface", "cavity"]
    assert addons.style_helper_specs()[0]["tags"] == ["topography-publication"]
    assert addons.export_helper_specs()[0]["formats"] == ["png", "html"]
    assert addons.tool_mode_specs()[0]["id"] == "pocket-pick"



def test_addons_registry_rejects_incompatible_molsysviewer_requirement():
    addons.clear()
    try:
        addon = AddonSpec(name="future-addon", requires_molsysviewer=">=999.0.0")
        try:
            addons.register(addon)
        except ValueError as exc:
            message = str(exc)
        else:
            raise AssertionError("Expected incompatible add-on requirement to be rejected.")

        assert "future-addon" in message
        assert "requires MolSysViewer >=999.0.0" in message
        assert addons.available() == []
    finally:
        addons.clear()


def test_addon_spec_rejects_invalid_molsysviewer_requirement():
    try:
        AddonSpec(name="bad-requirement", requires_molsysviewer="not a specifier")
    except ValueError as exc:
        assert "requires_molsysviewer" in str(exc)
    else:
        raise AssertionError("Expected invalid requires_molsysviewer specifier to be rejected.")


def test_addons_registry_rejects_duplicate_addon_namespace():
    addons.clear()
    first = AddonSpec(name="topomt", package="first")
    second = AddonSpec(name="topomt", package="second")
    try:
        addons.register(first)
        try:
            addons.register(second)
        except ValueError as exc:
            message = str(exc)
        else:
            raise AssertionError("Expected duplicate add-on namespace to be rejected.")

        assert message == "Add-on namespace 'topomt' is already registered."
        assert addons.records()[0]["package"] == "first"
    finally:
        addons.clear()


def test_addons_registry_rejects_duplicate_workspace_id():
    addons.clear()
    try:
        addons.register(
            AddonSpec(
                name="first",
                workspaces=(AddonWorkspaceSpec(id="shared", title="First"),),
            )
        )
        try:
            addons.register(
                AddonSpec(
                    name="second",
                    workspaces=(AddonWorkspaceSpec(id="shared", title="Second"),),
                )
            )
        except ValueError as exc:
            message = str(exc)
        else:
            raise AssertionError("Expected duplicate add-on workspace id to be rejected.")

        assert message == "Add-on workspace id 'shared' from 'second' is already registered by 'first'."
        assert addons.available() == ["first"]
    finally:
        addons.clear()


def test_addon_spec_info_includes_molsysviewer_requirement():
    addon = AddonSpec(name="compatible-addon", requires_molsysviewer=">=0.1")

    assert addon.info()["requires_molsysviewer"] == ">=0.1"


def test_view_addons_expose_lazy_state_namespace_and_manager_proxy():
    addons.clear()

    class State:
        def __init__(self, view):
            self.view = view
            self.enabled = False

    try:
        addons.register(
            AddonSpec(
                name="topomt",
                state_factory=State,
                panels=(AddonPanelSpec(id="topo", title="Topo", entry="topomt.panel"),),
            )
        )
        view = MolSysView()

        assert sorted(dir(view.addons)) == ["manager", "topomt"]
        assert view.addons.manager.enabled() == ["topomt"]
        assert view.addons.enabled() == ["topomt"]
        assert isinstance(view.addons.topomt, State)
        assert view.addons.topomt is view.addons.topomt
        assert view.addons.topomt.view is view
    finally:
        addons.clear()


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
            "has_on_active_selection_changed": False,
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
    monkeypatch.setattr(addons_module, "metadata_entry_points", lambda: {})
    try:
        discovered = addons.discover(include_known_modules=True)
        assert [item.name for item in discovered] == ["topomt"]
        assert addons.known_modules() == ["molsysviewer_topomt", "molsysviewer_missing"]
        assert addons.records()[0]["module"] == "molsysviewer_topomt"
    finally:
        sys.modules.pop(module.__name__, None)
        addons.clear()


def test_addons_registry_does_not_import_known_modules_by_default(monkeypatch):
    addons.clear()
    module = ModuleType("molsysviewer_topomt")

    def _get_addon():
        return AddonSpec(name="topomt", package="molsysviewer-topomt")

    from importlib.machinery import ModuleSpec
    module.get_addon = _get_addon
    module.__spec__ = ModuleSpec(module.__name__, None)
    sys.modules[module.__name__] = module
    monkeypatch.setattr(addons_module, "KNOWN_ADDON_MODULES", ("molsysviewer_topomt",))
    monkeypatch.setattr(addons_module, "metadata_entry_points", lambda: {})
    try:
        discovered = addons.discover()
        assert discovered == []
        assert addons.available() == []
    finally:
        sys.modules.pop(module.__name__, None)
        addons.clear()


def test_addons_registry_discovers_entry_point_addons(monkeypatch):
    addons.clear()
    module = ModuleType("molsysviewer_epaddon")
    module.addon = AddonSpec(
        name="ep-addon",
        package="molsysviewer-epaddon",
        panels=(AddonPanelSpec(id="ep", title="Entry Point", entry="ep.panel"),),
    )

    class FakeEntryPoint:
        name = "ep-addon"
        value = "molsysviewer_epaddon"

        def load(self):
            return module

    monkeypatch.setattr(addons_module, "KNOWN_ADDON_MODULES", ())
    monkeypatch.setattr(addons_module, "metadata_entry_points", lambda: {"molsysviewer.addons": [FakeEntryPoint()]})

    discovered = addons.discover()

    assert [item.name for item in discovered] == ["ep-addon"]
    assert addons.records()[0]["module"] == "molsysviewer_epaddon"
    assert addons.discovery_failures() == []
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
    monkeypatch.setattr(addons_module, "metadata_entry_points", lambda: {})

    manager = smonitor.get_manager()
    before_warnings = manager.report().get("warnings_total", 0)

    try:
        discovered = addons.discover(include_known_modules=True)
        assert len(discovered) == 0
        after_warnings = manager.report().get("warnings_total", 0)
        assert after_warnings == before_warnings + 1
    finally:
        sys.modules.pop(module.__name__, None)
        addons.clear()



def test_addons_registry_records_entry_point_discovery_failures(monkeypatch):
    addons.clear()

    class BrokenEntryPoint:
        name = "broken-addon"
        value = "molsysviewer_broken:get_addon"

        def load(self):
            raise RuntimeError("broken entry point")

    monkeypatch.setattr(addons_module, "KNOWN_ADDON_MODULES", ())
    monkeypatch.setattr(addons_module, "metadata_entry_points", lambda: {"molsysviewer.addons": [BrokenEntryPoint()]})

    discovered = addons.discover()

    assert discovered == []
    failures = addons.discovery_failures()
    assert len(failures) == 1
    assert failures[0]["source"] == "entry-point:broken-addon"
    assert failures[0]["reason"] == "broken entry point"
    assert "RuntimeError: broken entry point" in failures[0]["traceback"]
    addons.clear()



def test_view_addons_runtime_summary_includes_discovery_failures(monkeypatch):
    addons.clear()

    class BrokenEntryPoint:
        name = "broken-addon"
        value = "molsysviewer_broken:get_addon"

        def load(self):
            raise RuntimeError("broken entry point")

    monkeypatch.setattr(addons_module, "metadata_entry_points", lambda: {"molsysviewer.addons": [BrokenEntryPoint()]})
    addons.discover()

    view = MolSysView()
    sent: list[dict] = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]
    try:
        assert view.addons.discovery_failures()[0]["source"] == "entry-point:broken-addon"

        view._sync_addons_runtime()  # noqa: SLF001
        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["discovery_failures"][0]["source"] == "entry-point:broken-addon"
        assert addon_msg["discovery_failures"][0]["reason"] == "broken entry point"
    finally:
        addons.clear()


def test_view_addons_refresh_context_items_from_active_selection_hook():
    addons.clear()
    sent = []

    def on_active_selection_changed(_view, selection):
        assert selection["atom_indices"] == [1, 2, 3]
        return [
            {
                "id": "inspect-simplex",
                "title": "Inspect simplex",
                "group": "Selection",
                "order": 5,
                "target_kinds": ["shape"],
                "payload": {"kind": "face", "face_id": 7},
            },
            {"id": "broken"},
        ]

    try:
        addon = AddonSpec(name="topomt")
        lifecycle = addons_module.AddonLifecycleSpec(
            on_active_selection_changed=on_active_selection_changed
        )
        addons.register(addon, lifecycle=lifecycle)
        view = MolSysView()
        view._send = lambda message: sent.append(message)

        items = view.addons.refresh_context_items({"atom_indices": [1, 2, 3]})

        assert items == [
            {
                "addon": "topomt",
                "id": "inspect-simplex",
                "title": "Inspect simplex",
                "group": "Selection",
                "order": 5,
                "enabled": True,
                "target_kinds": ["shape"],
                "payload": {"kind": "face", "face_id": 7},
            }
        ]
        assert sent == [{"op": "set_addon_context_items", "items": items}]
    finally:
        addons.clear()


def test_addon_template_module_is_importable_and_registerable():
    addons.clear()
    try:
        addon = addons.register_module("molsysviewer.addon_templates.dummy_addon")
        assert addon.name == "dummy-addon"
        assert addons.available() == ["dummy-addon"]
        assert addons.workspace_specs()[0]["id"] == "dummy"
        assert [item["id"] for item in addons.panel_specs()] == ["main", "secondary"]
        assert [item["id"] for item in addons.context_action_specs()] == ["focus-dummy", "inspect-dummy"]
        assert [item["id"] for item in addons.addon_section_specs()] == ["interactive", "inputs", "status"]
        assert addons.shape_provider_specs()[0]["id"] == "dummy-shape"
        assert addons.export_helper_specs()[0]["id"] == "dummy-export"
        assert addons.lifecycle_for("dummy-addon") is not None
        assert addons.lifecycle_for("dummy-addon").info() == {
            "has_on_enable": True,
            "has_on_disable": True,
            "has_on_context_action": True,
            "has_on_active_selection_changed": False,
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
        assert [item["id"] for item in addons.addon_section_specs()] == ["modes", "network-overlays"]
        assert [item["id"] for item in addons.shape_provider_specs()] == ["contact-links", "mode-ellipsoids"]
        assert addons.export_helper_specs()[0]["id"] == "enm-figure"
        assert addons.lifecycle_for("elasnetmt-template") is not None
        assert addons.lifecycle_for("elasnetmt-template").info() == {
            "has_on_enable": True,
            "has_on_disable": True,
            "has_on_context_action": True,
            "has_on_active_selection_changed": False,
        }
    finally:
        addons.clear()


def test_addon_template_module_has_visible_runtime_lifecycle_flow():
    addons.clear()
    try:
        addons.register_module("molsysviewer.addon_templates.dummy_addon")
        view = MolSysView(debug_js=True)

        assert view._dummy_addon_enabled is True
        assert ("enable", "dummy-addon") in view._dummy_addon_events
        assert view._dummy_addon_runtime["enabled"] is True
        assert view._dummy_addon_runtime["workspace"] == "dummy"
        assert view._dummy_addon_runtime["panels"] == ["main", "secondary"]
        assert view._dummy_addon_runtime["sections"] == ["interactive", "inputs", "status"]
        assert view._dummy_addon_runtime["context_actions"] == ["focus-dummy", "inspect-dummy"]
        assert view._dummy_addon_runtime["export_helpers"] == ["dummy-export"]

        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "interaction_context_action",
                "action": "addon_context_action",
                "addon": "dummy-addon",
                "addon_action_id": "focus-dummy",
                "addon_action_title": "Focus Dummy",
                "context": {"kind": "structure", "atom_indices": [1, 2, 3]},
            }
        )

        assert view._dummy_addon_last_context_action["action_id"] == "focus-dummy"
        assert view._dummy_addon_last_context_action["payload"]["addon"] == "dummy-addon"
        assert view._dummy_addon_runtime["last_context_action"]["action_id"] == "focus-dummy"
        assert ("context", "focus-dummy") in view._dummy_addon_events

        view.addons.disable("dummy-addon")
        assert view._dummy_addon_enabled is False
        assert view._dummy_addon_runtime["enabled"] is False
        assert ("disable", "dummy-addon") in view._dummy_addon_events
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
        addons.register_module("molsysviewer.addon_templates.dummy_addon")
        view.addons.enable("dummy-addon")
        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["addons"] == ["dummy-addon"]
        assert [item["id"] for item in addon_msg["panel_specs"]] == ["main", "secondary"]
        assert [item["id"] for item in addon_msg["context_action_specs"]] == ["focus-dummy", "inspect-dummy"]
        assert [item["id"] for item in addon_msg["addon_sections"]] == ["interactive", "inputs", "status"]
        assert [item["id"] for item in addon_msg["export_helper_specs"]] == ["dummy-export"]
    finally:
        addons.clear()


def test_addon_templates_helper_lists_and_registers_reference_addons():
    addons.clear()
    try:
        assert addon_templates.list_reference_addons() == ["dummy", "elasnetmt"]
        assert addon_templates.resolve_reference_addon("elasnetmt") == "molsysviewer.addon_templates.minimal_elasnetmt"
        assert addon_templates.resolve_reference_addon("minimal_elasnetmt") == "molsysviewer.addon_templates.minimal_elasnetmt"
        assert addon_templates.resolve_reference_addon("dummy") == "molsysviewer.addon_templates.dummy_addon"
        assert addon_templates.resolve_reference_addon("minimal_dummy") == "molsysviewer.addon_templates.dummy_addon"

        addon = addon_templates.register_dummy_addon()
        assert addon.name == "dummy-addon"
        assert addons.available() == ["dummy-addon"]

        addons.clear()
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
        assert [item.name for item in registered] == ["dummy-addon", "elasnetmt-template"]
        assert addons.available() == ["dummy-addon", "elasnetmt-template"]
    finally:
        addons.clear()


def test_addon_templates_helper_can_build_reference_demo_view():
    addons.clear()
    try:
        view = addon_templates.build_reference_demo_view("dummy")
        assert view.addons.enabled() == ["dummy-addon"]
        assert [item["id"] for item in view.addons.workspace_specs()] == ["dummy"]
        assert [item["id"] for item in view.addons.panel_specs()] == ["main", "secondary"]
        assert view._dummy_addon_enabled is True
        assert view._dummy_addon_runtime["workspace"] == "dummy"
        assert view._dummy_addon_runtime["panels"] == ["main", "secondary"]
        messages = view._message_history  # noqa: SLF001
        assert next(msg for msg in reversed(messages) if msg.get("op") == "set_panel_mode") == {
            "op": "set_panel_mode",
            "panel": "addons",
            "expanded": True,
        }
        assert next(msg for msg in reversed(messages) if msg.get("op") == "set_workspace") == {
            "op": "set_workspace",
            "workspace": "dummy",
        }
        assert next(msg for msg in reversed(messages) if msg.get("op") == "set_workspace_panel") == {
            "op": "set_workspace_panel",
            "panel": "main",
            "workspace": "dummy",
        }

        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "panel_mode_state",
                "panel": "addons",
                "expanded": True,
                "workspace": "dummy",
                "workspace_panel": "main",
            }
        )
        runtime = view.workspace_runtime()
        assert runtime["current_workspace"] == "dummy"
        assert runtime["current_workspace_record"]["id"] == "dummy"
        assert runtime["current_panel"]["id"] == "main"
        assert [item["id"] for item in runtime["current_panels"]] == ["main", "secondary"]
        assert [item["id"] for item in runtime["current_sections"]] == ["interactive", "inputs", "status"]
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



def test_view_addons_lifecycle_on_enable_failure_isolated_and_reported():
    addons.clear()

    def _on_enable(_view):
        raise RuntimeError("enable exploded")

    addons.register(
        AddonSpec(
            name="broken-lifecycle",
            panels=(AddonPanelSpec(id="broken", title="Broken", entry="broken.panel"),),
        ),
        lifecycle=addons_module.AddonLifecycleSpec(on_enable=_on_enable),
    )

    view = MolSysView()
    sent: list[dict] = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[assignment]
    try:
        assert view.addons.is_enabled("broken-lifecycle") is False
        failures = view.addons.lifecycle_failures()
        assert failures[0]["source"] == "lifecycle:broken-lifecycle.on_enable"
        assert failures[0]["reason"] == "enable exploded"
        assert "RuntimeError: enable exploded" in failures[0]["traceback"]

        view._sync_addons_runtime()  # noqa: SLF001
        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["addons"] == []
        assert addon_msg["lifecycle_failures"][0]["source"] == "lifecycle:broken-lifecycle.on_enable"
    finally:
        addons.clear()


def test_view_addons_lifecycle_on_disable_failure_isolated_and_reported():
    addons.clear()

    def _on_disable(_view):
        raise RuntimeError("disable exploded")

    addons.register(
        AddonSpec(name="broken-disable"),
        lifecycle=addons_module.AddonLifecycleSpec(on_disable=_on_disable),
    )

    view = MolSysView()
    try:
        view.addons.disable("broken-disable")
        assert view.addons.is_enabled("broken-disable") is False
        failures = view.addons.lifecycle_failures()
        assert failures[0]["source"] == "lifecycle:broken-disable.on_disable"
        assert failures[0]["reason"] == "disable exploded"
    finally:
        addons.clear()


def test_view_addons_context_action_failure_isolated_and_reported():
    addons.clear()

    def _on_context_action(_view, _action_id, _payload):
        raise RuntimeError("context exploded")

    addons.register(
        AddonSpec(
            name="broken-context",
            context_actions=(
                AddonContextActionSpec(
                    id="focus-pocket",
                    title="Focus Pocket",
                    entry="broken.context.focus_pocket",
                    target_kinds=("structure",),
                ),
            ),
        ),
        lifecycle=addons_module.AddonLifecycleSpec(on_context_action=_on_context_action),
    )

    view = MolSysView()
    try:
        handled = view.addons.handle_context_action(
            "broken-context",
            "focus-pocket",
            {
                "event": "interaction_context_action",
                "action": "addon_context_action",
                "addon": "broken-context",
                "addon_action_id": "focus-pocket",
                "context": {"kind": "structure", "atom_indices": [0]},
            },
        )

        assert handled is False
        assert view.addons.is_enabled("broken-context") is True
        failures = view.addons.lifecycle_failures()
        assert failures[0]["source"] == "lifecycle:broken-context.on_context_action:focus-pocket"
        assert failures[0]["reason"] == "context exploded"
    finally:
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


def test_view_handles_addon_manager_context_actions():
    addons.clear()
    addons.register(
        AddonSpec(
            name="topomt",
        )
    )
    view = MolSysView(debug_js=True)
    assert view.addons.is_enabled("topomt") is True

    # Test addon_disable
    view._handle_frontend_event({
        "event": "interaction_context_action",
        "action": "addon_disable",
        "name": "topomt",
    })
    assert view.addons.is_enabled("topomt") is False

    # Test addon_enable
    view._handle_frontend_event({
        "event": "interaction_context_action",
        "action": "addon_enable",
        "name": "topomt",
    })
    assert view.addons.is_enabled("topomt") is True

    # Test addon_rescan
    view._handle_frontend_event({
        "event": "interaction_context_action",
        "action": "addon_rescan",
    })

    # Test addon_register_module with a failing import (recorded failure)
    view._handle_frontend_event({
        "event": "interaction_context_action",
        "action": "addon_register_module",
        "name": "non_existent_addon_module_test",
    })
    failures = view.addons.discovery_failures()
    assert any(f["source"] == "non_existent_addon_module_test" for f in failures)

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
                addon_sections=(
                    AddonSectionSpec(
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
        assert addon_msg["addon_sections"][0]["title"] == "Pockets"
        assert addon_msg["export_helper_specs"][0]["title"] == "Topography Figure Export"

        view.addons.disable("topomt")
        addon_msg = next(msg for msg in reversed(sent) if msg.get("op") == "set_addon_runtime_summary")
        assert addon_msg["addons"] == []
        assert addon_msg["workspace_specs"] == []
        assert addon_msg["panel_specs"] == []
        assert addon_msg["context_action_specs"] == []
        assert addon_msg["addon_sections"] == []
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
                addon_sections=(
                    AddonSectionSpec(
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
        assert addon_msg["addon_sections"][0]["runtime_payload"]["item_title"] == "0 overlays"
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
                addon_sections=(
                    AddonSectionSpec(
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
        assert addon_msg["addon_sections"][0]["runtime_payload"]["item_title"] == "1 overlays"
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


def test_addon_panel_widget_state_is_bound_to_widget_addon_namespace():
    import types
    addons.clear()
    module = types.ModuleType("_test_state_panel_mod")

    class _PanelA(AddonPanelWidget):
        _esm = "export function render() {}"

    class _PanelB(AddonPanelWidget):
        _esm = "export function render() {}"

    module._PanelA = _PanelA
    module._PanelB = _PanelB
    sys.modules[module.__name__] = module

    try:
        addons.register(
            AddonSpec(
                name="addon-a",
                panels=(AddonPanelSpec(id="main", title="A", widget_class="_test_state_panel_mod._PanelA"),),
            )
        )
        addons.register(
            AddonSpec(
                name="addon-b",
                panels=(AddonPanelSpec(id="main", title="B", widget_class="_test_state_panel_mod._PanelB"),),
            )
        )
        view = types.SimpleNamespace(
            widget=types.SimpleNamespace(addon_states={}),
            _active_panel_widget=None,
        )
        from molsysviewer.addons import ViewAddonsManager
        mgr = ViewAddonsManager(view, addons)
        panel_a = mgr.resolve_panel_widget("addon-a", "main")
        panel_b = mgr.resolve_panel_widget("addon-b", "main")

        view._active_panel_widget = ("addon-b", "main", panel_b)
        panel_a.set_state({"progress": 0.5})
        assert view.widget.addon_states == {"addon-a": {"progress": 0.5}}
        assert panel_a.state == {"progress": 0.5}
        assert panel_b.state == {}

        view._active_panel_widget = None
        panel_b.set_state({"progress": 1.0})
        assert view.widget.addon_states == {
            "addon-a": {"progress": 0.5},
            "addon-b": {"progress": 1.0},
        }
        assert panel_a._addon_name == "addon-a"
        assert panel_b._addon_name == "addon-b"
    finally:
        addons.clear()
        sys.modules.pop(module.__name__, None)


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
        assert widget._addon_name == "panel-addon"
    finally:
        addons.clear()
        sys.modules.pop(module.__name__, None)
