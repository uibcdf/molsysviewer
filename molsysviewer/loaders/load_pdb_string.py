# molsysviewer/loaders/load_pdb_string.py

from __future__ import annotations

from typing import TYPE_CHECKING

import molsysmt as msm
import numpy as np

if TYPE_CHECKING:
    from ..viewer import MolSysView


def ensure_view(view: "MolSysView" | None = None) -> "MolSysView":
    if view is None:
        from ..viewer import MolSysView
        view = MolSysView()
    return view


def load_pdb_string(
    pdb_string: str,
    *,
    label: str | None = None,
    view: "MolSysView" | None = None,
) -> "MolSysView":
    """Backend interno para MolSysView.load_pdb_string(...)."""

    view = ensure_view(view)

    view.molecular_system = pdb_string
    view.selection = "all"
    view.structure_indices = "all"

    view._molsys = msm.convert(
        pdb_string,
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
            "format": "pdb",
            "data": pdb_string,
            "label": label,
        }
    )

    return view
