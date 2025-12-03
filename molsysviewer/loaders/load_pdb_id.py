# molsysviewer/loaders/load_pdb_id.py

from __future__ import annotations

from typing import TYPE_CHECKING

import molsysmt as msm
import numpy as np

if TYPE_CHECKING:
    from ..viewer import MolSysView


def ensure_view(view: "MolSysView" | None = None) -> "MolSysView":
    view = ensure_view(view)
    return view


def load_pdb_id(
    pdb_id: str,
    *,
    label: str | None = None,
    view: "MolSysView" | None = None,
) -> "MolSysView":
    """Backend interno para MolSysView.load_pdb_id(...)."""

    if view is None:
        from ..viewer import MolSysView
        view = MolSysView()

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

    return view
