"""Real public add-on and shape API exercised by the empty-workspace browser guard."""

import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from molsysviewer.addons import AddonPanelSpec, AddonPanelWidget, AddonSpec, AddonWorkspaceSpec

import molsysviewer as msv


class WorkspacePanel(AddonPanelWidget):
    _esm = """
    export function render({model, el}) {
        let stateCount = 0;
        const state = message => {
            if (message.type === 'state') {
                el.dataset.workspaceStateCount = String(++stateCount);
                if (message.state.initial) el.dataset.workspaceReady = 'true';
            }
        };
        model.on('msg:custom', state);
        for (const id of ['render', 'clear']) {
            const button = document.createElement('button');
            button.textContent = id === 'render' ? 'Render geometry' : 'Clear geometry';
            button.dataset.workspaceGeometry = id;
            button.onclick = () => model.send({type:'action', id});
            el.appendChild(button);
        }
        return () => { model.off('msg:custom', state); el.replaceChildren(); };
    }
    """

    def on_mount(self, view, *, skip_digestion=False):
        self.push_state({"initial": True})

    def handle_action(self, view, action_id, payload, *, skip_digestion=False):
        if action_id == "render":
            if view.shapes.contains("workspace-sphere"):
                view.shapes.delete("workspace-sphere")
            view.shapes.add_sphere(center="[1,0,0] nm", radius="0.3 nm", tag="workspace-sphere")
        elif action_id == "clear" and view.shapes.contains("workspace-sphere"):
            view.shapes.delete("workspace-sphere")


def fixture_event(view, event):
    action = event.get("workspace_fixture")
    if action is None:
        return False
    if action == "caller-shape":
        view.shapes.add_sphere(center="[0,0,0] nm", radius="0.3 nm", tag="caller-sphere")
    elif action == "delete-caller":
        view.shapes.delete("caller-sphere")
    elif action == "hide-caller":
        view.shapes["caller-sphere"].hide()
    elif action == "distant-shape":
        view.shapes.add_sphere(center="[100,0,0] nm", radius="0.3 nm", tag="distant-sphere")
    elif action == "load-molecule":
        view.load(msv.demo["dialanine"].molsys)
        view.player.set_fps(17)
    elif action == "enable":
        view.addons.enable("geometry-review")
    else:
        raise ValueError(f"Unknown workspace fixture action: {action}")
    return True


def main():
    msv.addons.register(
        AddonSpec(
            name="geometry-review",
            workspaces=(AddonWorkspaceSpec(id="geometry-review", title="Geometry Review", entry_panel="geometry"),),
            panels=(
                AddonPanelSpec(
                    id="geometry", title="Geometry", widget_class="shape_only_workspace_fixture.WorkspacePanel"
                ),
            ),
        )
    )
    view = msv.MolSysView(viewer_mode="standard", controls_mode="compact")
    # Start genuinely empty; registration/activation is tested after mounting.
    runpy.run_path(str(Path(__file__).with_name("canvas-popup-bridge.py")))["serve"](view, fixture_event)


if __name__ == "__main__":
    main()
