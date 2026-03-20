"""Minimal reference add-on shaped like a future TopoMT integration."""

from molsysviewer.addons import (
    AddonContextActionSpec,
    AddonPanelSpec,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonWorkbenchSectionSpec,
)


addon = AddonSpec(
    name="topomt-template",
    package="molsysviewer-topomt",
    version="0.1.0",
    description="Minimal TopoMT-shaped reference add-on for extension authors.",
    panels=(
        AddonPanelSpec(
            id="topo",
            title="Topo",
            entry="molsysviewer_topomt.panel.topo",
            description="Reference panel contribution for topography workflows.",
            order=20,
        ),
    ),
    context_actions=(
        AddonContextActionSpec(
            id="focus-pocket",
            title="Focus Pocket",
            entry="molsysviewer_topomt.context.focus_pocket",
            target_kinds=("structure", "shape"),
            group="topography",
            order=10,
        ),
    ),
    workbench_sections=(
        AddonWorkbenchSectionSpec(
            id="pockets",
            title="Pockets",
            entry="molsysviewer_topomt.workbench.pockets",
            target_panel="workbench",
            order=30,
        ),
    ),
    shape_providers=(
        AddonShapeProviderSpec(
            id="pocket-surface",
            title="Pocket Surface",
            entry="molsysviewer_topomt.shapes.pocket_surface",
            kinds=("surface", "cavity"),
            order=40,
        ),
    ),
    meta={"domain": "topography", "template": True},
)


def get_addon() -> AddonSpec:
    return addon
