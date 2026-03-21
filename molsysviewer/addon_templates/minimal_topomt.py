"""Minimal reference add-on shaped like a future TopoMT integration."""

from molsysviewer.addons import (
    AddonContextActionSpec,
    AddonExportHelperSpec,
    AddonLifecycleSpec,
    AddonPanelSpec,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonWorkbenchSectionSpec,
    AddonWorkspaceSpec,
)


addon = AddonSpec(
    name="topomt-template",
    package="molsysviewer-topomt",
    version="0.1.0",
    description="Minimal TopoMT-shaped reference add-on for extension authors.",
    workspaces=(
        AddonWorkspaceSpec(
            id="topomt",
            title="TopoMT",
            entry_panel="topo",
            description="Reference workspace contribution for topography workflows.",
            order=10,
        ),
    ),
    panels=(
        AddonPanelSpec(
            id="topo",
            title="Topo",
            entry="molsysviewer_topomt.panel.topo",
            description="Reference panel contribution for topography workflows.",
            order=20,
        ),
        AddonPanelSpec(
            id="channels",
            title="Channels",
            entry="molsysviewer_topomt.panel.channels",
            description="Reference channel-analysis panel contribution.",
            order=30,
        ),
        AddonPanelSpec(
            id="regions",
            title="Regions",
            entry="molsysviewer_topomt.panel.regions",
            description="Reference region-oriented panel contribution.",
            order=40,
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
        AddonContextActionSpec(
            id="inspect-channel",
            title="Inspect Channel",
            entry="molsysviewer_topomt.context.inspect_channel",
            target_kinds=("structure", "shape"),
            group="topography",
            order=20,
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
        AddonWorkbenchSectionSpec(
            id="channels",
            title="Channels",
            entry="molsysviewer_topomt.workbench.channels",
            target_panel="workbench",
            order=40,
        ),
    ),
    shape_providers=(
        AddonShapeProviderSpec(
            id="pocket-surface",
            title="Pocket Surface",
            entry="molsysviewer_topomt.shapes.pocket_surface",
            kinds=("surface", "cavity"),
            order=50,
        ),
    ),
    export_helpers=(
        AddonExportHelperSpec(
            id="topography-figure",
            title="Topography Figure Export",
            entry="molsysviewer_topomt.export.figure",
            formats=("png", "html"),
            order=60,
        ),
    ),
    meta={"domain": "topography", "template": True},
)


def on_enable(view) -> None:
    """Reference hook for per-view initialization."""
    view._topomt_template_enabled = True
    view._topomt_template_events = getattr(view, "_topomt_template_events", [])
    view._topomt_template_events.append(("enable", "topomt-template"))
    view._topomt_template_runtime = {
        "enabled": True,
        "workspace": "topomt",
        "panels": ["topo", "channels", "regions"],
        "sections": ["pockets", "channels"],
        "context_actions": ["focus-pocket", "inspect-channel"],
        "export_helpers": ["topography-figure"],
        "last_context_action": None,
    }


def on_disable(view) -> None:
    """Reference hook for per-view teardown."""
    view._topomt_template_enabled = False
    view._topomt_template_events = getattr(view, "_topomt_template_events", [])
    view._topomt_template_events.append(("disable", "topomt-template"))
    runtime = getattr(view, "_topomt_template_runtime", None)
    if isinstance(runtime, dict):
        runtime["enabled"] = False


def on_context_action(view, action_id: str, payload: dict) -> None:
    """Reference hook for Python-side handling of context actions."""
    view._topomt_template_last_context_action = {
        "action_id": action_id,
        "payload": payload,
    }
    view._topomt_template_events = getattr(view, "_topomt_template_events", [])
    view._topomt_template_events.append(("context", action_id))
    runtime = getattr(view, "_topomt_template_runtime", None)
    if isinstance(runtime, dict):
        runtime["last_context_action"] = {
            "action_id": action_id,
            "payload": payload,
        }


lifecycle = AddonLifecycleSpec(
    on_enable=on_enable,
    on_disable=on_disable,
    on_context_action=on_context_action,
)


def get_addon() -> AddonSpec:
    return addon
