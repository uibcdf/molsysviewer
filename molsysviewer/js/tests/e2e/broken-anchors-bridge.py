from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import molsysmt as msm

from molsysviewer.demo import demo


def main() -> None:
    view = demo["dialanine"]
    sent: list[dict] = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    last_atom = int(view.molsys.get_n_atoms()) - 1
    view.annotations.add("terminal", atom_indices=[last_atom], tag="broken-note")
    view.measurements.add_distance([0], [last_atom], tag="broken-distance")
    sent.clear()

    atom_index_map = {index: index for index in range(last_atom)}
    edited = msm.remove(
        view.molsys,
        selection=[last_atom],
        to_form="molsysmt.MolSys",
        skip_digestion=True,
    )
    view.apply_system_edit(
        edited,
        atom_index_map=atom_index_map,
        load_blocks="collapse",
        skip_digestion=True,
    )

    print(json.dumps({
        "messages": sent,
        "annotation": view.annotations.info("broken-note"),
        "measurement": view.measurements.info("broken-distance"),
    }))


if __name__ == "__main__":
    main()
