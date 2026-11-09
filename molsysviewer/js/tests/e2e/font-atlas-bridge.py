"""Real pentalanine trajectory and public measurement creation for GPU receiving."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv

with msv.demo["pentalanine"] as source:
    with source.extract(structure_indices=[0, 8, 3]) as view:
        view.measurements.add_distance([0], [1], tag="font-distance")
        view.measurements.add_angle([0], [1], [2], tag="font-angle")
        view.measurements.add_dihedral([0], [1], [2], [3], tag="font-dihedral")
        coordinates = msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="angstrom").tolist()
        print(json.dumps({"messages": view._build_embedded_runtime_snapshot(), "coordinates": coordinates}))
