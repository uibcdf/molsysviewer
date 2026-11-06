"""Persistent real-Python authority for deferred molecular edit receiving."""

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import molsysmt as msm
from molsysviewer.widget import MolSysViewerWidget

import molsysviewer as msv


class NativeReader(msv.AddonPanelWidget):
    read_only_actions = ("inspect",)
    _esm = """
export function render({model,el}) {
    el.innerHTML='<label>Reader draft<input data-reader-draft></label><button data-reader-inspect>Inspect current box</button><button data-reader-write>Undeclared edit</button><output data-reader-result></output>';
    const inspect=()=>model.send({type:'action',id:'inspect',payload:{draft:el.querySelector('input').value}});
    const write=()=>model.send({type:'action',id:'write',payload:{}});
    const receive=msg=>{if(msg.type==='state')el.querySelector('output').textContent=JSON.stringify(msg.state);};
    el.querySelector('[data-reader-inspect]').addEventListener('click',inspect);
    el.querySelector('[data-reader-write]').addEventListener('click',write);
    model.on('msg:custom',receive);
    return()=>model.off('msg:custom',receive);
}
"""

    def handle_action(self, view, action_id, payload, *, skip_digestion=False):
        assert action_id == "inspect"
        box = view.addons.manager.system_edits.read(
            lambda target: msm.pyunitwizard.get_value(msm.get(target, box=True), to_unit="nm").tolist()
        )
        self.push_state({"box": box, "unit": "nm", "draft": payload["draft"]})


msv.addons.register(
    msv.AddonSpec(
        name="native-reader",
        panels=(msv.AddonPanelSpec(id="report", title="Native box", widget_class=f"{__name__}.NativeReader"),),
    )
)


class ReceivingWidget(MolSysViewerWidget):
    def send(self, content, buffers=None):
        messages.append(content)


messages = []
with msv.demo["pentalanine"] as source:
    with msv.MolSysView(transport=ReceivingWidget()) as view:
        view.load(source.molsys, structure_indices=[0, 8, 3])
        view.regions.add(selection=[0, 2, 4], tag="receiving-region")
        tools = view.addons.molsysmt if msv.addons.contains("molsysmt") else None
        view.addons.enable("native-reader")
        view._ready = True
        for line in sys.stdin:
            request = json.loads(line)
            messages.clear()
            try:
                family = request.get("family")
                if family == "initial":
                    messages.extend(view._build_embedded_runtime_snapshot())
                elif family == "defer":

                    def prepare(target):
                        coordinates = msm.get(target, element="atom", coordinates=True).copy()
                        coordinates += msm.pyunitwizard.quantity([0.2, 0.0, 0.0], "nm")
                        return {
                            "run": lambda: msm.set(target, coordinates=coordinates),
                            "changed": True,
                        }

                    if tools is not None and hasattr(tools.basic, "set"):
                        coordinates = msm.get(view.molsys, element="atom", coordinates=True).copy()
                        coordinates += msm.pyunitwizard.quantity([0.2, 0.0, 0.0], "nm")
                        tools.basic.set(coordinates=coordinates, update_view=False)
                    else:
                        view.addons.manager.system_edits.execute(
                            prepare, name="receiving.coordinates", update_view=False
                        )
                elif family == "defer_box":
                    import numpy as np

                    box = msm.pyunitwizard.quantity(np.tile(np.diag([3, 4, 5]), (3, 1, 1)), "nm")
                    if tools is not None and hasattr(tools.basic, "set"):
                        tools.basic.set(box=box, update_view=False)
                    else:
                        view.addons.manager.system_edits.execute(
                            lambda target, value=box: {"run": lambda: msm.set(target, box=value), "changed": True},
                            name="receiving.box",
                            update_view=False,
                        )
                elif family == "late_endpoint":
                    messages.append(view.addons.manager.system_edits._message())
                elif family == "reader_mount":
                    view._mount_addon_panel("native-reader", "report")
                elif family == "reader_defer":
                    import numpy as np

                    box = msm.pyunitwizard.quantity(np.tile(np.diag([4, 5, 6]), (3, 1, 1)), "nm")
                    view.addons.manager.system_edits.execute(
                        lambda target, value=box: {"run": lambda: msm.set(target, box=value), "changed": True},
                        name="receiving.reader.box",
                        update_view=False,
                    )
                for event in request.get("events", []):
                    view._handle_frontend_event(event)
                result = {
                    "messages": list(messages),
                    "status": view.addons.manager.system_edits.get_status(),
                    "atom_count": view.molsys.get_n_atoms(),
                    "addon_set": tools is not None and hasattr(tools.basic, "set"),
                }
                print(json.dumps({"id": request["id"], "result": result}), flush=True)
            except Exception:
                print(json.dumps({"id": request["id"], "error": traceback.format_exc()}), flush=True)
