"""Keep the real notebook authority alive for canvas-popup browser checks."""

import base64
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from molsysviewer.interactions import _to_plain
from molsysviewer.runtime_contract import wrap_outbound

import molsysviewer as msv


def serve():
    view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3], controls_mode="classic")
    view.set_controls_visible(True, autohide=False, position=["top", "left"])
    sent = []

    def capture(content, buffers=None):
        sent.append(
            {
                "content": wrap_outbound(content, view.widget.runtime_viewer_id, view.widget.runtime_session_id),
                "buffers": [base64.b64encode(memoryview(buffer)).decode("ascii") for buffer in buffers or []],
            }
        )

    view.widget.send = capture
    try:
        for line in sys.stdin:
            request = json.loads(line)
            try:
                sent.clear()
                for event in request.get("events", []):
                    if "review_traits" in event:
                        # This is the notebook's normal trait synchronization,
                        # separate from its custom-message channel.
                        for trait, value in event["review_traits"].items():
                            setattr(view.widget, trait, value)
                    else:
                        view._handle_inbound_message(event)
                state = _to_plain(view.widget.get_state(drop_defaults=False))
                result = {"messages": list(sent), "traits": state}
                print(json.dumps({"id": request["id"], "result": result}), flush=True)
            except Exception:
                print(json.dumps({"id": request["id"], "error": traceback.format_exc()}), flush=True)
    finally:
        view.close()


if __name__ == "__main__":
    serve()
