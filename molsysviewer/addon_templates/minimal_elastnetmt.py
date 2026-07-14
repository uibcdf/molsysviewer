"""Minimal reference add-on shaped like a future ElastNetMT integration."""

from molsysviewer.addons import (
    AddonContextActionSpec,
    AddonExportHelperSpec,
    AddonLifecycleSpec,
    AddonPanelSpec,
    AddonShapeProviderSpec,
    AddonSpec,
    AddonSectionSpec,
    AddonWorkspaceSpec,
)


addon = AddonSpec(
    name="elastnetmt-template",
    package="molsysviewer-elastnetmt",
    version="0.1.0",
    description="Minimal ElastNetMT-shaped reference add-on for extension authors.",
    workspaces=(
        AddonWorkspaceSpec(
            id="elastnetmt",
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
            entry="molsysviewer_elastnetmt.panel.model",
            description="Reference panel contribution for ENM model setup.",
            order=20,
        ),
        AddonPanelSpec(
            id="modes",
            title="Modes",
            entry="molsysviewer_elastnetmt.panel.modes",
            description="Reference panel contribution for mode exploration.",
            order=30,
        ),
        AddonPanelSpec(
            id="figures",
            title="Figures",
            entry="molsysviewer_elastnetmt.panel.figures",
            description="Reference panel contribution for ENM figure recipes.",
            order=40,
        ),
    ),
    context_actions=(
        AddonContextActionSpec(
            id="show-contact-network",
            title="Show Contact Network",
            entry="molsysviewer_elastnetmt.context.show_contact_network",
            target_kinds=("structure", "shape"),
            group="elastic-network",
            order=10,
        ),
        AddonContextActionSpec(
            id="show-mode-vectors",
            title="Show Mode Vectors",
            entry="molsysviewer_elastnetmt.context.show_mode_vectors",
            target_kinds=("structure", "shape"),
            group="elastic-network",
            order=20,
        ),
    ),
    addon_sections=(
        AddonSectionSpec(
            id="modes",
            title="Modes",
            entry="molsysviewer_elastnetmt.workbench.modes",
            target_panel="addons",
            order=30,
        ),
        AddonSectionSpec(
            id="network-overlays",
            title="Network Overlays",
            entry="molsysviewer_elastnetmt.workbench.network_overlays",
            target_panel="addons",
            order=40,
        ),
    ),
    shape_providers=(
        AddonShapeProviderSpec(
            id="contact-links",
            title="Contact Links",
            entry="molsysviewer_elastnetmt.shapes.contact_links",
            kinds=("network", "contact"),
            order=50,
        ),
        AddonShapeProviderSpec(
            id="mode-ellipsoids",
            title="Mode Ellipsoids",
            entry="molsysviewer_elastnetmt.shapes.mode_ellipsoids",
            kinds=("anisotropy", "ellipsoid"),
            order=60,
        ),
    ),
    export_helpers=(
        AddonExportHelperSpec(
            id="enm-figure",
            title="ENM Figure Export",
            entry="molsysviewer_elastnetmt.export.figure",
            formats=("png", "html"),
            order=70,
        ),
    ),
    meta={"domain": "elastic-networks", "template": True},
)


def on_enable(view) -> None:
    """Reference hook for per-view initialization."""
    view._elastnetmt_template_enabled = True
    view._elastnetmt_template_events = getattr(view, "_elastnetmt_template_events", [])
    view._elastnetmt_template_events.append(("enable", "elastnetmt-template"))
    view._elastnetmt_template_runtime = {
        "enabled": True,
        "workspace": "elastnetmt",
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
    view._elastnetmt_template_enabled = False
    view._elastnetmt_template_events = getattr(view, "_elastnetmt_template_events", [])
    view._elastnetmt_template_events.append(("disable", "elastnetmt-template"))
    runtime = getattr(view, "_elastnetmt_template_runtime", None)
    if isinstance(runtime, dict):
        runtime["enabled"] = False


def on_context_action(view, action_id: str, payload: dict) -> None:
    """Reference hook for Python-side handling of ElastNetMT actions."""
    view._elastnetmt_template_last_context_action = {
        "action_id": action_id,
        "payload": payload,
    }
    view._elastnetmt_template_events = getattr(view, "_elastnetmt_template_events", [])
    view._elastnetmt_template_events.append(("context", action_id))
    runtime = getattr(view, "_elastnetmt_template_runtime", None)
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
