"""Minimal reference add-on shaped like a future ElasNetMT integration."""

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
    name="elasnetmt-template",
    package="molsysviewer-elasnetmt",
    version="0.1.0",
    description="Minimal ElasNetMT-shaped reference add-on for extension authors.",
    workspaces=(
        AddonWorkspaceSpec(
            id="elasnetmt",
            title="Elastic Networks",
            entry_panel="modes",
            description="Reference workspace contribution for elastic-network workflows.",
            order=20,
        ),
    ),
    panels=(
        AddonPanelSpec(
            id="model",
            title="Model",
            entry="molsysviewer_elasnetmt.panel.model",
            description="Reference panel contribution for ENM model setup.",
            order=20,
        ),
        AddonPanelSpec(
            id="modes",
            title="Modes",
            entry="molsysviewer_elasnetmt.panel.modes",
            description="Reference panel contribution for mode exploration.",
            order=30,
        ),
        AddonPanelSpec(
            id="figures",
            title="Figures",
            entry="molsysviewer_elasnetmt.panel.figures",
            description="Reference panel contribution for ENM figure recipes.",
            order=40,
        ),
    ),
    context_actions=(
        AddonContextActionSpec(
            id="show-contact-network",
            title="Show Contact Network",
            entry="molsysviewer_elasnetmt.context.show_contact_network",
            target_kinds=("structure", "shape"),
            group="elastic-network",
            order=10,
        ),
        AddonContextActionSpec(
            id="show-mode-vectors",
            title="Show Mode Vectors",
            entry="molsysviewer_elasnetmt.context.show_mode_vectors",
            target_kinds=("structure", "shape"),
            group="elastic-network",
            order=20,
        ),
    ),
    workbench_sections=(
        AddonWorkbenchSectionSpec(
            id="modes",
            title="Modes",
            entry="molsysviewer_elasnetmt.workbench.modes",
            target_panel="workbench",
            order=30,
        ),
        AddonWorkbenchSectionSpec(
            id="network-overlays",
            title="Network Overlays",
            entry="molsysviewer_elasnetmt.workbench.network_overlays",
            target_panel="workbench",
            order=40,
        ),
    ),
    shape_providers=(
        AddonShapeProviderSpec(
            id="contact-links",
            title="Contact Links",
            entry="molsysviewer_elasnetmt.shapes.contact_links",
            kinds=("network", "contact"),
            order=50,
        ),
        AddonShapeProviderSpec(
            id="mode-ellipsoids",
            title="Mode Ellipsoids",
            entry="molsysviewer_elasnetmt.shapes.mode_ellipsoids",
            kinds=("anisotropy", "ellipsoid"),
            order=60,
        ),
    ),
    export_helpers=(
        AddonExportHelperSpec(
            id="enm-figure",
            title="ENM Figure Export",
            entry="molsysviewer_elasnetmt.export.figure",
            formats=("png", "html"),
            order=70,
        ),
    ),
    meta={"domain": "elastic-networks", "template": True},
)


def on_enable(view) -> None:
    """Reference hook for per-view initialization."""
    view._elasnetmt_template_enabled = True
    view._elasnetmt_template_events = getattr(view, "_elasnetmt_template_events", [])
    view._elasnetmt_template_events.append(("enable", "elasnetmt-template"))
    view._elasnetmt_template_runtime = {
        "enabled": True,
        "workspace": "elasnetmt",
        "model_kind": "ANM",
        "cutoff": "12 angstroms",
        "selection": 'atom_name=="CA"',
        "panels": ["model", "modes", "figures"],
        "sections": ["modes", "network-overlays"],
        "context_actions": ["show-contact-network", "show-mode-vectors"],
        "export_helpers": ["enm-figure"],
        "last_context_action": None,
    }


def on_disable(view) -> None:
    """Reference hook for per-view teardown."""
    view._elasnetmt_template_enabled = False
    view._elasnetmt_template_events = getattr(view, "_elasnetmt_template_events", [])
    view._elasnetmt_template_events.append(("disable", "elasnetmt-template"))
    runtime = getattr(view, "_elasnetmt_template_runtime", None)
    if isinstance(runtime, dict):
        runtime["enabled"] = False


def on_context_action(view, action_id: str, payload: dict) -> None:
    """Reference hook for Python-side handling of ElasNetMT actions."""
    view._elasnetmt_template_last_context_action = {
        "action_id": action_id,
        "payload": payload,
    }
    view._elasnetmt_template_events = getattr(view, "_elasnetmt_template_events", [])
    view._elasnetmt_template_events.append(("context", action_id))
    runtime = getattr(view, "_elasnetmt_template_runtime", None)
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
