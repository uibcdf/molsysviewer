"""Real demo trajectory edits supplied to the browser through public Python."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv
from molsysviewer import pyunitwizard as puw

view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
initial = view._build_embedded_runtime_snapshot()
before = puw.get_value(view.get_coordinates(), to_unit="nm")
view._ready = True
sent = []
view.widget.send = sent.append
stages = []
for indices, shift in (([2], 1.0), ([2, 0], 2.0)):
    coordinates = puw.get_value(view.get_coordinates(structure_indices=indices), to_unit="nm")[:, 2:3, :].copy()
    coordinates[:, :, 0] += shift
    view.partial_coordinates_update(puw.quantity(coordinates, "nm"), selection=[2], structure_indices=indices,
                                    transaction_id=f"edit-{len(stages)}")
    stages.append({"messages": list(sent), "after": puw.get_value(view.get_coordinates(), to_unit="nm").tolist()})
    sent.clear()
box_stages = []
for cells, indices in (
    (np.array([[[2 + i, 0, 0], [0.5, 3 + i, 0], [0.2, 0.3, 4 + i]] for i in range(3)]), "all"),
    (np.array([np.diag([8, 9, 10]), np.diag([5, 6, 7])]), [2, 0]),
    (None, "all"),
):
    view.set_box(None if cells is None else puw.quantity(cells, "nm"), structure_indices=indices)
    if not box_stages:
        view.show_box(color="red", width=0.2)
    box = view.molsys.structures.box
    box_stages.append({"messages": list(sent), "cells": None if box is None else puw.get_value(box, to_unit="nm").tolist()})
    sent.clear()
print(json.dumps({"initial": initial, "before": before.tolist(), "stages": stages, "box_stages": box_stages}))
