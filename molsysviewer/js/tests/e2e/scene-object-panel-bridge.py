from __future__ import annotations

import json
import sys

from molsysviewer.demo import demo
from molsysviewer import pyunitwizard as puw


content = json.loads(sys.stdin.read())
view = demo["dialanine"]
sent = []
view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
view._ready = True  # noqa: SLF001
view.annotations.add("site", atom_indices=[0], tag="note")
section = view.scene.add_section([0.1, 0.2, 0.3], [1.0, 0.0, 0.0], tag="cut")
sent.clear()

view._handle_frontend_event(content)  # noqa: SLF001

print(json.dumps({
    "visible": view.annotations.info("note")["visible"],
    "section_point_nm": (
        puw.get_value(section.get_point(), to_unit="nm").tolist()
        if view.scene.sections()
        else None
    ),
    "section_count": len(view.scene.sections()),
    "messages": [
        message for message in sent
        if message.get("op") in {
            "hide_layer", "set_annotation_summaries", "set_sections", "set_section_summaries",
        }
    ],
}))
