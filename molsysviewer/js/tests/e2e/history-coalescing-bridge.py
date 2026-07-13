from __future__ import annotations

import json
import sys

from molsysviewer.demo import demo


def main() -> None:
    events = json.load(sys.stdin)
    view = demo["dialanine"]
    view.widget.send = lambda _message: None
    region = view.regions.add(atom_indices=[0, 1, 2], tag="pocket", skip_digestion=True)
    region.set_representation("line", alpha=0.2, skip_digestion=True)
    view.history.clear()

    depth_before_undo = None
    alpha_before_undo = None
    for event in events:
        if event.get("event") == "scene_history_undo":
            depth_before_undo = len(view.history._undo)  # noqa: SLF001
            alpha_before_undo = view.regions["pocket"].repr_params.get("alpha")
        view._handle_frontend_event(event)  # noqa: SLF001

    print(json.dumps({
        "depth_before_undo": depth_before_undo,
        "alpha_before_undo": alpha_before_undo,
        "alpha_after_undo": view.regions["pocket"].repr_params.get("alpha"),
    }))


if __name__ == "__main__":
    main()
