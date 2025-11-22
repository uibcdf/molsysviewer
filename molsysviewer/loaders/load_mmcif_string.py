# molsysviewer/loaders/load_mmcif_string.py

from __future__ import annotations

from typing import Any

import molsysmt as msm
import numpy as np


def load_mmcif_string(
    view: Any,
    *,
    mmcif_string: str,
    label: str | None = None,
) -> None:
    """Backend interno para MolSysView.load_mmcif_string(...)."""

    view.molecular_system = mmcif_string
    view.selection = "all"
    view.structure_indices = "all"

    view._molsys = msm.convert(
        mmcif_string,
        to_form="molsysmt.MolSys",
        selection="all",
        structure_indices="all",
        syntax="MolSysMT",
    )
    n_atoms = msm.get(view._molsys, element="atom", n_atoms=True)
    view.atom_mask = np.ones(n_atoms, dtype=bool)

    view._send(
        {
            "op": "load_structure_from_string",
            "format": "mmcif",
            "data": mmcif_string,
            "label": label,
        }
    )
