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
