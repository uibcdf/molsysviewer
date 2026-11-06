from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


def _new_view():
    with msv.demo["pentalanine"] as seed:
        view = msv.new_view(seed.molsys, structure_indices=[0, 8, 3])
    sent: list[dict] = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    view.measurements.add_distance([0], [5], tag="d1")
    return view, sent


def initial_payload() -> dict:
    view, sent = _new_view()
    try:
        initial_messages = view._build_embedded_runtime_snapshot()  # noqa: SLF001
        coordinates = puw.get_value(view.get_coordinates(selection=[0, 5]), to_unit="nm")
        expected = np.linalg.norm(coordinates[:, 0] - coordinates[:, 1], axis=1)
        sent.clear()
        view.player.go_to_structure(1)
        return {
            "initial_messages": initial_messages,
            "frame_messages": list(sent),
            "expected_text": [f"{value:.3f} nm" for value in expected],
        }
    finally:
        view.close()


def lifecycle_payload(events: list[dict]) -> dict:
    view, sent = _new_view()
    try:
        view.history.clear()
        sent.clear()
        message_batches = []
        states = []
        for event in events:
            view._handle_frontend_event(event)  # noqa: SLF001
            message_batches.append(list(sent))
            sent.clear()
            states.append(
                {
                    "contains": view.measurements.contains("d1"),
                    "visible": (view.measurements.info("d1")["visible"] if view.measurements.contains("d1") else None),
                }
            )

        view._handle_frontend_event({"event": "scene_history_undo"})  # noqa: SLF001
        message_batches.append(list(sent))
        states.append(
            {
                "contains": view.measurements.contains("d1"),
                "visible": view.measurements.info("d1")["visible"],
            }
        )
        return {"message_batches": message_batches, "states": states}
    finally:
        view.close()


def main() -> None:
    raw = sys.stdin.read().strip()
    with puw.context(standard_units=["nm", "ps"]):
        payload = lifecycle_payload(json.loads(raw)) if raw else initial_payload()
    print(json.dumps(payload, default=lambda value: value.item()))


if __name__ == "__main__":
    main()
