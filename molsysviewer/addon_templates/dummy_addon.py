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
            <div style="padding: 16px; font-family: 'IBM Plex Sans', system-ui, sans-serif; color: #f4f4f5; display: flex; flex-direction: column; gap: 16px; box-sizing: border-box; width: 100%;">
                
                <!-- Header -->
                <div>
                    <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #ffffff; letter-spacing: -0.01em;">Dummy Add-on Tester</h3>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: rgba(244,244,245,0.6); line-height: 1.4;">
                        Reference tool illustrating design consistency, UI controls, and live state synchronization.
                    </p>
                </div>

                <!-- Section 1: Interactive Utilities -->
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
                    <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: rgba(244,244,245,0.4); letter-spacing: 0.05em;">
                        1. Interactive Counter
                    </div>
                    <div style="display: flex; gap: 8px; align-items: center; margin-top: 4px;">
                        <button id="btn-count" style="background: #6366f1; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: 500; transition: background 0.2s;">
                            Click Me: 0
                        </button>
                        <button id="btn-reset" style="background: rgba(255,255,255,0.06); color: #f4f4f5; border: 1px solid rgba(255,255,255,0.12); padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: background 0.2s;">
                            Reset
                        </button>
                    </div>
                    <!-- Live progress bar -->
                    <div style="margin-top: 6px; display: flex; flex-direction: column; gap: 4px;">
                        <div style="display: flex; justify-content: space-between; font-size: 10px; color: rgba(244,244,245,0.5);">
                            <span>Progress Index:</span>
                            <span id="progress-text">0%</span>
                        </div>
                        <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden;">
                            <div id="progress-bar" style="width: 0%; height: 100%; background: #6366f1; transition: width 0.3s ease;"></div>
                        </div>
                    </div>
                </div>

                <!-- Section 2: Input & State Sync -->
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 10px;">
                    <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: rgba(244,244,245,0.4); letter-spacing: 0.05em;">
                        2. Controls & Sync
                    </div>
                    
                    <!-- Text input -->
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                        <label style="font-size: 11px; color: rgba(244,244,245,0.6);">Custom Display Text:</label>
                        <input id="input-text" type="text" value="Hello World" placeholder="Type here..." style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 8px; color: #f4f4f5; font-size: 12px; font-family: inherit;" />
                    </div>

                    <!-- Dropdown select -->
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                        <label style="font-size: 11px; color: rgba(244,244,245,0.6);">Projection Mode:</label>
                        <select id="select-mode" style="background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px 8px; color: #f4f4f5; font-size: 12px; font-family: inherit;">
                            <option value="Perspective">Perspective Camera</option>
                            <option value="Orthographic">Orthographic Camera</option>
                        </select>
                    </div>

                    <!-- Realtime display feedback box -->
                    <div style="background: rgba(0,0,0,0.15); border-radius: 4px; padding: 8px 10px; font-size: 11px; color: rgba(244,244,245,0.8); display: flex; flex-direction: column; gap: 4px; border-left: 2px solid #6366f1;">
                        <div><strong>Typed:</strong> <span id="val-text">Hello World</span></div>
                        <div><strong>Camera:</strong> <span id="val-mode">Perspective</span></div>
                    </div>
                </div>

                <!-- Section 3: Property Monitor Table -->
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
                    <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: rgba(244,244,245,0.4); letter-spacing: 0.05em; display: flex; justify-content: space-between; align-items: center;">
                        <span>3. Status & Properties</span>
                        <span style="background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.25); font-size: 9px; padding: 1px 4px; border-radius: 3px; font-weight: 600;">ACTIVE</span>
                    </div>
                    <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 4px; text-align: left;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.06); color: rgba(244,244,245,0.5);">
                                <th style="padding: 4px 0; font-weight: 500;">Parameter</th>
                                <th style="padding: 4px 0; font-weight: 500; text-align: right;">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                                <td style="padding: 6px 0; color: rgba(244,244,245,0.7);">Test Atoms</td>
                                <td style="padding: 6px 0; text-align: right; font-weight: 500;">104 atoms</td>
                            </tr>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                                <td style="padding: 6px 0; color: rgba(244,244,245,0.7);">Domain Registry</td>
                                <td style="padding: 6px 0; text-align: right; color: #60a5fa; font-weight: 500;">testing</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: rgba(244,244,245,0.7);">Latency (Mock)</td>
                                <td style="padding: 6px 0; text-align: right; color: #facc15; font-weight: 500;">0.04s</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

            </div>
        `;

        // Event hooks
        const btnCount = el.querySelector('#btn-count');
        const btnReset = el.querySelector('#btn-reset');
        const progressBar = el.querySelector('#progress-bar');
        const progressText = el.querySelector('#progress-text');
        
        const inputText = el.querySelector('#input-text');
        const selectMode = el.querySelector('#select-mode');
        const valText = el.querySelector('#val-text');
        const valMode = el.querySelector('#val-mode');

        let count = 0;
        const updateCountUi = () => {
            btnCount.textContent = `Click Me: ${count}`;
            // progress capped at 10 clicks = 100%
            const pct = Math.min(count * 10, 100);
            progressBar.style.width = `${pct}%`;
            progressText.textContent = `${pct}%`;
        };

        btnCount.addEventListener('click', () => {
            count++;
            updateCountUi();
        });

        btnReset.addEventListener('click', () => {
            count = 0;
            updateCountUi();
        });

        // Input sync listeners
        inputText.addEventListener('input', (e) => {
            valText.textContent = e.target.value || '(empty)';
        });

        selectMode.addEventListener('change', (e) => {
            valMode.textContent = e.target.value;
        });

        return () => {
            console.log('[Dummy Addon] Rich Main Panel cleanup callback executed successfully!');
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
