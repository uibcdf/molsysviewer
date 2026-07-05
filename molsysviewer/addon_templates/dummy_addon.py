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
    AddonPanelWidget,
)


class DummyMainPanelWidget(AddonPanelWidget):
    """Main panel widget with count state and cleanup logging."""
    _esm = """
    export function render({ model, el }) {
        el.innerHTML = `
            <div style="padding: 16px; font-family: 'IBM Plex Sans', system-ui, sans-serif; color: #f4f4f5; display: flex; flex-direction: column; gap: 12px;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #ffffff;">Dummy Add-on Main Panel</h3>
                <p style="margin: 0; font-size: 13px; color: rgba(244,244,245,0.7); line-height: 1.5;">
                    This is a live preview of the dummy add-on panel, illustrating standard styles, dark mode consistency, and ESM rendering.
                </p>
                <div style="display: flex; gap: 8px; margin-top: 8px;">
                    <button id="btn-count" style="background: #6366f1; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 500; transition: background 0.2s;">
                        Click Me: 0
                    </button>
                    <button id="btn-reset" style="background: rgba(255,255,255,0.08); color: #f4f4f5; border: 1px solid rgba(255,255,255,0.15); padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; transition: background 0.2s;">
                        Reset
                    </button>
                </div>
            </div>
        `;
        const btnCount = el.querySelector('#btn-count');
        const btnReset = el.querySelector('#btn-reset');
        let count = 0;

        btnCount.addEventListener('click', () => {
            count++;
            btnCount.textContent = `Click Me: ${count}`;
        });

        btnReset.addEventListener('click', () => {
            count = 0;
            btnCount.textContent = `Click Me: ${count}`;
        });

        return () => {
            console.log('[Dummy Addon] Main Panel cleanup callback executed successfully!');
        };
    }
    """


class DummySecondaryPanelWidget(AddonPanelWidget):
    """Secondary panel widget demonstrating custom shapes summary."""
    _esm = """
    export function render({ model, el }) {
        el.innerHTML = `
            <div style="padding: 16px; font-family: 'IBM Plex Sans', system-ui, sans-serif; color: #f4f4f5; display: flex; flex-direction: column; gap: 12px;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #ffffff;">Secondary Panel</h3>
                <p style="margin: 0; font-size: 13px; color: rgba(244,244,245,0.7); line-height: 1.5;">
                    This secondary panel illustrates workspace navigation within the same add-on.
                </p>
                <div style="padding: 10px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 4px; font-size: 12px; color: rgba(244,244,245,0.6);">
                    Active Workspace: <strong>Dummy</strong>
                </div>
            </div>
        `;
        return () => {
            console.log('[Dummy Addon] Secondary Panel cleanup callback executed successfully!');
        };
    }
    """


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
            entry="molsysviewer.addon_templates.dummy_addon.main",
            widget_class="molsysviewer.addon_templates.dummy_addon.DummyMainPanelWidget",
            description="Reference panel contribution for testing.",
            order=20,
        ),
        AddonPanelSpec(
            id="secondary",
            title="Secondary Panel",
            entry="molsysviewer.addon_templates.dummy_addon.secondary",
            widget_class="molsysviewer.addon_templates.dummy_addon.DummySecondaryPanelWidget",
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
