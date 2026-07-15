from __future__ import annotations

import json
import sys

from molsysviewer import pyunitwizard as puw
from molsysviewer.demo import demo


actions = json.loads(sys.stdin.read())
view = demo["dialanine"]
sent = []
view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
view._ready = True  # noqa: SLF001

view.regions.add(
    atom_indices=[0, 1, 2],
    tag="pocket",
    representation="ball-and-stick",
    skip_digestion=True,
)
view.shapes.add(
    "sphere",
    center=puw.quantity([0.0, 0.0, 0.0], "nm"),
    radius=puw.quantity(0.15, "nm"),
    tag="marker",
    skip_digestion=True,
)
sent.clear()

batches = []
states = []
for action in actions:
    view._handle_frontend_event(action)  # noqa: SLF001
    batches.append(list(sent))
    sent.clear()
    shape = view.shapes.get("marker", skip_digestion=True)
    states.append({
        "layer_exists": "analysis" in view.layers,
        "region_exists": "pocket" in view.regions,
        "region_layer": view.regions["pocket"].layer if "pocket" in view.regions else None,
        "region_visible": view.regions["pocket"].visible if "pocket" in view.regions else None,
        "shape_exists": shape is not None,
        "shape_layer": shape.layer_tag if shape is not None else None,
        "shape_visible": view.shapes.info("marker")["visible"] if shape is not None else None,
    })

print(json.dumps({"batches": batches, "states": states}))
