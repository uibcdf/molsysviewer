from __future__ import annotations

import json
import sys

from molsysviewer.demo import demo


content = json.loads(sys.stdin.read())
view = demo["dialanine"]
sent = []
view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
view._ready = True  # noqa: SLF001
view.annotations.add("site", atom_indices=[0], tag="note")
sent.clear()

view._handle_frontend_event(content)  # noqa: SLF001

print(json.dumps({
    "visible": view.annotations.info("note")["visible"],
    "messages": [
        message for message in sent
        if message.get("op") in {"hide_layer", "set_annotation_summaries"}
    ],
}))
