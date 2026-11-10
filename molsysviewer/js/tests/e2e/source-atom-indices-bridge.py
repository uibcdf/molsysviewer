"""Ordered real-demo extraction with native/model atom axes and recovery."""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysmt as msm
from molsysviewer.colors import scalar_to_color_list

import molsysviewer as msv


def fixture():
    with msv.demo["pentalanine"] as seed:
        groups = msm.get(seed.molsys, element="group", atom_index=True)
        a, b = [list(g[:3]) for g in groups if len(g) >= 3][:2]
        # Extraction has canonical ascending-source order. Explicit atom order
        # belongs to the independent public permutation tool, not selection.
        selected = sorted(a + b)
        base = msm.extract(seed.molsys, selection=selected, structure_indices=[0, 8, 3])
        coordinates = msm.pyunitwizard.get_value(seed.molsys.structures.coordinates, to_unit="nm")[[0, 8, 3]][
            :, selected
        ]
        orders = [list(range(6)), [0, 3, 1, 4, 2, 5]]
        result = []
        for order in orders:
            declared = msm.basic.permute_atoms(base, order, return_report=True)
            np.testing.assert_array_equal(declared["report"]["output_to_source_atom_indices"], order)
            np.testing.assert_array_equal(
                msm.pyunitwizard.get_value(declared["molecular_system"].structures.coordinates, to_unit="nm"),
                coordinates[:, order],
            )
            with msv.new_view(declared["molecular_system"]) as view:
                view.whole.set_representation("ball-and-stick")
                values = np.arange(6, dtype=float)
                view.whole.set_color_by_values(values, palette=["#112233", "#ddeeff"])
                view.regions.add(selection=[1, 4], tag="mapped", representation="ball-and-stick")
                view.measurements.add_distance([1, 4], [0], tag="mapped-distance", endpoint_policy="centroid")
                view.annotations.add("Mapped anchor", atom_indices=[1, 4], tag="mapped-label")
                view.annotations.add("Mapped callout", atom_indices=[1, 4], tag="mapped-callout", leader_line=True)
                view.shapes.add_sphere(atom_indices=[1, 4], radius="0.05 nm", tag="mapped-static-sphere")
                view.shapes.add_sphere(structures_atom_indices=[[1, 4]] * 3, radius="0.05 nm", tag="mapped-sphere")
                coords = msm.pyunitwizard.get_value(view.molsys.structures.coordinates, to_unit="angstrom")
                expected = dict(
                    coordinates=coords.tolist(),
                    colors=scalar_to_color_list(values, palette=["#112233", "#ddeeff"]),
                    groups=np.asarray(msm.get(view.molsys, element="atom", group_index=True)).tolist(),
                )
                with tempfile.TemporaryDirectory(prefix="source-index-roundtrip-") as directory:
                    path = Path(directory) / "mapped.msv"
                    view.save_session(path)
                    with msv.load_session(path) as recovered:
                        result.append(
                            dict(
                                input_order=order,
                                initial=view._build_embedded_runtime_snapshot(),
                                restored=recovered._build_embedded_runtime_snapshot(),
                                expected=expected,
                            )
                        )
        return result


if __name__ == "__main__":
    print(json.dumps(fixture()))
