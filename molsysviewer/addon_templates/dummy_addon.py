"""Dummy reference add-on for testing and illustrating extension capabilities."""

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
    name="dummy-addon",
    package="molsysviewer-dummy-addon",
    version="0.1.0",
    description="Dummy reference add-on for testing and illustrating extension capabilities.",
    workspaces=(
        AddonWorkspaceSpec(
            id="dummy",
            title="Dummy",
            entry_panel="main",
            description="Reference workspace contribution for testing.",
            order=10,
        ),
    ),
    panels=(
        AddonPanelSpec(
            id="main",
            title="Main Panel",
            entry="molsysviewer_dummy_addon.panel.main",
            description="Reference panel contribution for testing.",
            order=20,
        ),
        AddonPanelSpec(
            id="secondary",
            title="Secondary Panel",
            entry="molsysviewer_dummy_addon.panel.secondary",
            description="Reference secondary panel contribution.",
            order=30,
        ),
    ),
    context_actions=(
        AddonContextActionSpec(
            id="focus-dummy",
            title="Focus Dummy",
            entry="molsysviewer_dummy_addon.context.focus_dummy",
            target_kinds=("structure", "shape"),
            group="testing",
            order=10,
        ),
        AddonContextActionSpec(
            id="inspect-dummy",
            title="Inspect Dummy",
            entry="molsysviewer_dummy_addon.context.inspect_dummy",
            target_kinds=("structure", "shape"),
            group="testing",
            order=20,
        ),
    ),
    addon_sections=(
        AddonSectionSpec(
            id="controls",
            title="Controls",
            entry="molsysviewer_dummy_addon.workbench.controls",
            target_panel="addons",
            order=30,
        ),
    ),
    shape_providers=(
        AddonShapeProviderSpec(
            id="dummy-shape",
            title="Dummy Shape",
            entry="molsysviewer_dummy_addon.shapes.dummy_shape",
            kinds=("surface", "cavity"),
            order=50,
        ),
    ),
    export_helpers=(
        AddonExportHelperSpec(
            id="dummy-export",
            title="Dummy Export Helper",
            entry="molsysviewer_dummy_addon.export.helper",
            formats=("png", "html"),
            order=60,
        ),
    ),
    meta={"domain": "testing", "template": True},
)


def on_enable(view) -> None:
    """Reference hook for per-view initialization."""
    view._dummy_addon_enabled = True
    view._dummy_addon_events = getattr(view, "_dummy_addon_events", [])
    view._dummy_addon_events.append(("enable", "dummy-addon"))
    view._dummy_addon_runtime = {
        "enabled": True,
        "workspace": "dummy",
        "panels": ["main", "secondary"],
        "sections": ["controls"],
        "context_actions": ["focus-dummy", "inspect-dummy"],
        "export_helpers": ["dummy-export"],
        "last_context_action": None,
    }


def on_disable(view) -> None:
    """Reference hook for per-view teardown."""
    view._dummy_addon_enabled = False
    view._dummy_addon_events = getattr(view, "_dummy_addon_events", [])
    view._dummy_addon_events.append(("disable", "dummy-addon"))
    runtime = getattr(view, "_dummy_addon_runtime", None)
    if isinstance(runtime, dict):
        runtime["enabled"] = False


def on_context_action(view, action_id: str, payload: dict) -> None:
    """Reference hook for Python-side handling of context actions."""
    view._dummy_addon_last_context_action = {
        "action_id": action_id,
        "payload": payload,
    }
    view._dummy_addon_events = getattr(view, "_dummy_addon_events", [])
    view._dummy_addon_events.append(("context", action_id))
    runtime = getattr(view, "_dummy_addon_runtime", None)
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
