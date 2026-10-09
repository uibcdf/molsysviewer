"""Real pentalanine Studio state and Python action replies for browser review."""

import contextlib
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))


def replay(events):
    from molsysviewer.interactions import _to_plain
    from molsysviewer.viewer.panel_actions import dispatch_panel_action

    import molsysviewer as msv
    from molsysviewer import FigureSpec

    source = msv.demo["pentalanine"]
    try:
        view = msv.new_view(source.molsys, structure_indices=[0, 8, 3])
    finally:
        source.close()
    try:
        view.whole.set_representation("ball-and-stick")
        view.set_figure_spec(FigureSpec(scale=1.5, background="white"))
        view.interactions.hbonds.get_buch_hbonds(name="review", structure_indices="all", distance_threshold="0.4 nm")
        view.interactions.add("review", tag="hbonds")
        initial = view._build_embedded_runtime_snapshot()  # noqa: SLF001
        transmitted = []
        original_send = view.widget.send

        def observe_send(message, buffers=None):
            transmitted.append(message)
            return original_send(message, buffers=buffers)

        view.widget.send = observe_send
        view._ready = True  # noqa: SLF001
        batches = []
        for event in events:
            before = len(transmitted)
            dispatch_panel_action(view, event)
            batches.append(transmitted[before:])
        return _to_plain({"initial_messages": initial, "message_batches": batches})
    finally:
        view.close()


def main():
    for line in sys.stdin:
        request_id = None
        try:
            request = json.loads(line)
            request_id = request["id"]
            with contextlib.redirect_stdout(sys.stderr):
                result = replay(request.get("events", []))
            response = {"id": request_id, "result": result}
        except Exception:
            response = {"id": request_id, "error": traceback.format_exc()}
        print(json.dumps(response, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
