"""Real demo annotations and trajectory for the final design-review browser guard."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv
from molsysviewer import pyunitwizard as puw

view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
coordinates = puw.get_value(view.get_coordinates(), to_unit="angstrom")
point = coordinates[0, 0].tolist()
for pattern in ("solid", "dashed", "dotted"):
    view.annotations.add(
        pattern,
        tag=f"world-{pattern}",
        position=puw.quantity(point, "angstrom"),
        offset_mode="world",
        offset=puw.quantity([3, 2, 1], "angstrom"),
        leader_line=True,
        leader_line_style=pattern,
    )
view.annotations.add(
    "camera", tag="camera-dotted", atom_indices=[0], offset=[3, 2, 1], leader_line=True, leader_line_style="dotted"
)
print(
    json.dumps(
        {
            "messages": view._build_embedded_runtime_snapshot(),
            "point": point,
            "atom_at_last_frame": coordinates[2, 0].tolist(),
        }
    )
)
