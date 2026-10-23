"""Persistent real-Python authority for deferred molecular edit receiving."""

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import molsysmt as msm
from molsysviewer.widget import MolSysViewerWidget

import molsysviewer as msv


class ReceivingWidget(MolSysViewerWidget):
    def send(self, content, buffers=None):
        messages.append(content)


messages = []
with msv.demo["pentalanine"] as source:
    with msv.MolSysView(transport=ReceivingWidget()) as view:
        view.load(source.molsys, structure_indices=[0, 8, 3])
        view.regions.add(selection=[0, 2, 4], tag="receiving-region")
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

                    view.addons.manager.system_edits.execute(prepare, name="receiving.coordinates", update_view=False)
                elif family == "late_endpoint":
                    messages.append(view.addons.manager.system_edits._message())
                for event in request.get("events", []):
                    view._handle_frontend_event(event)
                result = {
                    "messages": list(messages),
                    "status": view.addons.manager.system_edits.get_status(),
                    "atom_count": view.molsys.get_n_atoms(),
                }
                print(json.dumps({"id": request["id"], "result": result}), flush=True)
            except Exception:
                print(json.dumps({"id": request["id"], "error": traceback.format_exc()}), flush=True)
