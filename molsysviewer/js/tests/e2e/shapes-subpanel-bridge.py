from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from molsysviewer import pyunitwizard as puw
from molsysviewer.demo import demo


def _new_view():
    view = demo["dialanine"]
    sent: list[dict] = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    view.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "angstrom"),
        radius=puw.quantity(3.0, "angstrom"),
        color="#ff4040",
        alpha=0.8,
        tag="site",
        skip_digestion=True,
    )
    view.shapes.add_set_alpha_spheres(
        centers=puw.quantity([[5.0, 0.0, 0.0]], "angstrom"),
        radii=puw.quantity([1.0], "angstrom"),
        tag="alpha-set",
        skip_digestion=True,
    )
    return view, sent


def initial_payload() -> dict:
    _view, sent = _new_view()
    return {"initial_messages": sent}


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
        shape = view.shapes.get("site", skip_digestion=True)
        info = None if shape is None else view.shapes.info("site", skip_digestion=True)
        states.append({
            "exists": shape is not None,
            "visible": info["visible"] if info else None,
            "color": info["color"] if info else None,
            "undo_depth": len(view.history._undo),  # noqa: SLF001
        })
    return {"message_batches": message_batches, "states": states}


def main() -> None:
    raw = sys.stdin.read().strip()
    payload = lifecycle_payload(json.loads(raw)) if raw else initial_payload()
    print(json.dumps(payload, default=lambda value: value.item()))


if __name__ == "__main__":
    main()
