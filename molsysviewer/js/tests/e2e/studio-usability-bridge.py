"""Real pentalanine Studio state and Python action replies for browser review."""

import contextlib
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))


def replay(events, family=None):
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
        if family == "refinement":
            view.active_selection.set([0, 1])
            for index, tag in enumerate(["alpha-one", "alpha-two", "beta"]):
                view.regions.add(atom_indices=[index], tag=tag)
                view.selections.add(tag, atom_indices=[index])
                view.annotations.add(text=tag, atom_indices=[index], tag=tag)
                view.measurements.add_distance([index], [index + 5], tag=tag)
                view.shapes.add_sphere(atom_indices=[index], tag=tag)
            layer = view.layers.add("presentation")
            layer.attach(view.shapes.get("beta"))
        initial = view._build_embedded_runtime_snapshot()  # noqa: SLF001
        transmitted = []
        original_send = view.widget.send

        def observe_send(message, buffers=None):
            transmitted.append(message)
            return original_send(message, buffers=buffers)

        view.widget.send = observe_send
        view._ready = True  # noqa: SLF001
        selection_messages = []
        if family == "refinement":
            # Embedded snapshots omit transient active selection. Use the real
            # runtime projection, as a live Python selection would do.
            view.active_selection.set([0, 1])
            view._sync_region_summaries_runtime()  # noqa: SLF001
            view._sync_annotation_summaries_runtime()  # noqa: SLF001
            view._sync_measurement_summaries_runtime()  # noqa: SLF001
            selection_messages.extend(transmitted)
            transmitted.clear()
        batches = []
        for event in events:
            before = len(transmitted)
            if event.get("event") == "scene_history_undo":
                view.history.undo()
            elif event.get("event") == "scene_history_redo":
                view.history.redo()
            else:
                try:
                    dispatch_panel_action(view, event)
                except Exception:
                    if family != "refinement" or not any(
                        message.get("op") == "studio_action_result" and not message["ok"]
                        for message in transmitted[before:]
                    ):
                        raise
            if family == "refinement" and event.get("action") == "set_trajectory_frame":
                # Exercise background repaint explicitly with real live summaries.
                view._sync_region_summaries_runtime()  # noqa: SLF001
                view._sync_annotation_summaries_runtime()  # noqa: SLF001
                view._sync_measurement_summaries_runtime()  # noqa: SLF001
            batches.append(transmitted[before:])
        return _to_plain(
            {"initial_messages": initial, "selection_messages": selection_messages, "message_batches": batches}
        )
    finally:
        view.close()


def main():
    for line in sys.stdin:
        request_id = None
        try:
            request = json.loads(line)
            request_id = request["id"]
            with contextlib.redirect_stdout(sys.stderr):
                result = replay(request.get("events", []), request.get("family"))
            response = {"id": request_id, "result": result}
        except Exception:
            response = {"id": request_id, "error": traceback.format_exc()}
        print(json.dumps(response, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
