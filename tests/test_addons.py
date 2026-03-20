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
    assert records[0]["panels"][0]["id"] == "topo"
    assert records[0]["context_actions"][0]["id"] == "focus-pocket"
    assert records[0]["workbench_sections"][0]["id"] == "pockets"
    assert records[0]["shape_providers"][0]["id"] == "pocket-surface"
    assert records[0]["style_helpers"][0]["id"] == "topography-publication"
    assert records[0]["export_helpers"][0]["id"] == "topography-figure"
    assert records[0]["tool_modes"][0]["id"] == "pocket-pick"

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
    sys.modules[module.__name__] = module
    try:
        addon = addons.register_module(module)
        assert addon.name == "topomt-dev"
        assert addons.available() == ["topomt-dev"]
        assert addons.records()[0]["module"] == "molsysviewer_topomt_dev"
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
        assert addons.panel_specs()[0]["id"] == "topo"
        assert addons.context_action_specs()[0]["id"] == "focus-pocket"
        assert addons.workbench_section_specs()[0]["id"] == "pockets"
        assert addons.shape_provider_specs()[0]["id"] == "pocket-surface"
    finally:
        addons.clear()
