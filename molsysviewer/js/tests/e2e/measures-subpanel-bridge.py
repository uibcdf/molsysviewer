from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from molsysviewer.demo import demo


def _new_view():
    view = demo["dialanine"]
    sent: list[dict] = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    view.measurements.add_distance([0], [1], tag="d1")
    return view, sent


def initial_payload() -> dict:
    view, sent = _new_view()
    initial_messages = list(sent)
    view._measurement_history[0]["options"]["value_series"] = [1.09, 2.18]  # noqa: SLF001
    sent.clear()
    view._handle_frontend_event({  # noqa: SLF001
        "event": "trajectory_frame_changed",
        "frame": 1,
        "is_playing": False,
    })
    return {
        "initial_messages": initial_messages,
        "frame_messages": [
            message for message in sent
            if message.get("op") == "set_measurement_summaries"
        ],
    }


def lifecycle_payload(events: list[dict]) -> dict:
    view, sent = _new_view()
    view.history.clear()
    sent.clear()
    message_batches = []
    states = []
    for event in events:
        view._handle_frontend_event(event)  # noqa: SLF001
        message_batches.append(list(sent))
        sent.clear()
        states.append({
            "contains": view.measurements.contains("d1"),
            "visible": (
                view.measurements.info("d1")["visible"]
                if view.measurements.contains("d1")
                else None
            ),
        })

    view._handle_frontend_event({"event": "scene_history_undo"})  # noqa: SLF001
    message_batches.append(list(sent))
    states.append({
        "contains": view.measurements.contains("d1"),
        "visible": view.measurements.info("d1")["visible"],
    })
    return {"message_batches": message_batches, "states": states}


def main() -> None:
    raw = sys.stdin.read().strip()
    if raw:
        payload = lifecycle_payload(json.loads(raw))
    else:
        payload = initial_payload()
    print(json.dumps(payload, default=lambda value: value.item()))


if __name__ == "__main__":
    main()
