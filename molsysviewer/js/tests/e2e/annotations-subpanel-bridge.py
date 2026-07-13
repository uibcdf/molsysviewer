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
    view.annotations.add(
        "Catalytic site",
        atom_indices=[0],
        tag="note",
        label_style={
            "color": "#ff4040",
            "size_em": 1.2,
            "background": True,
            "background_opacity": 0.7,
        },
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
        info = view.annotations.info("note")
        states.append({
            "text": info["text"],
            "visible": info["visible"],
            "undo_depth": len(view.history._undo),  # noqa: SLF001
        })
    return {"message_batches": message_batches, "states": states}


def main() -> None:
    raw = sys.stdin.read().strip()
    payload = lifecycle_payload(json.loads(raw)) if raw else initial_payload()
    print(json.dumps(payload, default=lambda value: value.item()))


if __name__ == "__main__":
    main()
