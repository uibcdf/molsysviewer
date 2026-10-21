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


def serve(view=None, fixture_event_handler=None):
    if view is None:
        view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3], controls_mode="compact")
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
                    if fixture_event_handler is not None and fixture_event_handler(view, event):
                        continue
                    if "mirror_fixture" in event:
                        action = event["mirror_fixture"]
                        if action == "seed":
                            view.regions.add(selection=[0, 1, 2, 3, 4], tag="mirror-region")
                            view.shapes.add_sphere(
                                center="[3, 3, 3] nm", radius="0.3 nm", alpha=1.0, tag="mirror-sphere"
                            )
                            view.annotations.add(
                                text="Mirror label",
                                position="[0, 3, 0] nm",
                                tag="mirror-label",
                                label_style={"size_em": 2.0, "background": True, "background_opacity": 1.0},
                            )
                            view.interactions.hbonds.get_buch_hbonds(
                                name="mirror-analysis", structure_indices="all", distance_threshold="0.4 nm"
                            )
                            view.interactions.add("mirror-analysis", tag="mirror-hbonds")
                        elif action == "camera":
                            view.camera.set_snapshot(event["snapshot"])
                        elif action == "selection":
                            view.active_selection.set(event["indices"])
                        elif action == "fps":
                            view.player.set_fps(event["fps"])
                        elif action == "update-label":
                            view.annotations["mirror-label"].set_text("Mirror revised")
                        elif action == "hide":
                            view.regions["mirror-region"].hide()
                            view.shapes["mirror-sphere"].hide()
                            view.annotations["mirror-label"].hide()
                        elif action == "show":
                            view.regions["mirror-region"].show()
                            view.shapes["mirror-sphere"].show()
                            view.annotations["mirror-label"].show()
                        else:
                            raise ValueError(f"Unknown mirror fixture action: {action}")
                    elif "review_traits" in event:
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
