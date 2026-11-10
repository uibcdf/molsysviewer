from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import molsysmt as msm
from molsysviewer.demo import demo


def dynamic_fixture():
    with demo["pentalanine"] as seed:
        with seed.extract(structure_indices=[0, 8, 3]) as view:
            coordinates = msm.pyunitwizard.get_value(view.get_coordinates(), to_unit="nm")
            distances = np.linalg.norm(coordinates - coordinates[:, [0]], axis=-1)
            atom = int(np.argmax(np.abs(distances[0] - distances[1])))
            assert atom > 0 and abs(distances[0, atom] - distances[1, atom]) > 1e-5
            threshold = float((distances[0, atom] + distances[1, atom]) / 2)
            population = np.array([0, atom])
            expression = f"atom_index in [0, {atom}] within {threshold:.17g} nm without pbc of atom_index==0"
            memberships = []
            for frame in range(3):
                expected = population[distances[frame, population] <= threshold]
                actual = msm.select(view.molsys, selection=expression, structure_indices=frame)
                np.testing.assert_array_equal(actual, expected)
                memberships.append(expected.tolist())
            assert memberships[0] != memberships[1]
            region = view.regions.add(selection=expression, tag="dyn", representation="ball-and-stick")
            region.mode = "dynamic"
            return {"messages": view._build_embedded_runtime_snapshot(), "memberships": memberships}


def main() -> None:
    source = demo["dialanine"]
    source.scene.add_section(
        point=[0.1, 0.2, 0.3],
        normal=[2.0, 0.0, 0.0],
        invert=True,
        tag="cut",
    )
    document = source.export_state()

    restored = demo["dialanine"]
    sent: list[dict] = []
    restored.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    restored._ready = True  # noqa: SLF001
    restored.import_state(document)

    section = restored.scene.sections()[0]
    section.set_point([0.4, 0.2, 0.3])
    set_sections = [message for message in sent if message.get("op") == "set_sections"]
    print(
        json.dumps(
            {
                "document": document,
                "restored": restored.export_state()["sections"],
                "message": set_sections[-1],
                "dynamic": dynamic_fixture(),
            }
        )
    )


if __name__ == "__main__":
    main()
