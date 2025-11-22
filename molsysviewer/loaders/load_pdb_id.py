# molsysviewer/loaders/load_pdb_id.py

from __future__ import annotations

from typing import Any

import molsysmt as msm
import numpy as np


def load_pdb_id(
    view: Any,
    *,
    pdb_id: str,
    label: str | None = None,
) -> None:
    """Backend interno para MolSysView.load_pdb_id(...)."""

    if pdb_id is None:
        raise ValueError("pdb_id must be a non-empty string.")

    pdb_id_str = str(pdb_id).strip()
    if not pdb_id_str:
        raise ValueError("pdb_id must be a non-empty string.")

    # Estado Python
    view.molecular_system = pdb_id
    view.selection = "all"
    view.structure_indices = "all"

    view._molsys = msm.convert(
        pdb_id,
        to_form="molsysmt.MolSys",
        selection="all",
        structure_indices="all",
        syntax="MolSysMT",
    )
    n_atoms = msm.get(view._molsys, element="atom", n_atoms=True)
    view.atom_mask = np.ones(n_atoms, dtype=bool)

    # Normalizamos a minúsculas por consistencia
    pdb_id_str = pdb_id_str.lower()

    view._send(
        {
            "op": "load_pdb_id",
            "pdb_id": pdb_id_str,
            "label": label,
        }
    )

