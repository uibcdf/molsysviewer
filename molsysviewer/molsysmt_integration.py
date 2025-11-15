
from __future__ import annotations

from typing import Any, Sequence, Union

import molsysmt as msm

from .viewer import MolSysView


Selection = Union[str, Sequence[int]]
StructureIndices = Union[str, Sequence[int]]


def load(
    item: Any,
    selection: Selection = "all",
    structure_indices: StructureIndices = "all",
    view: MolSysView | None = None,
    *,
    to_form: str = "string:pdb_text",
    **convert_kwargs,
) -> MolSysView:
    """Create or update a MolSysView from a MolSysMT-compatible item.

    Parameters
    ----------
    item
        Cualquier objeto aceptado por `molsysmt.convert`:
        - ruta a fichero (PDB, mmCIF, etc.),
        - identificador PDB,
        - objeto MolSysMT (MolSys, MolSysDict, etc.),
        - o cualquier otro form soportado por MolSysMT.
    selection
        Selección atómica (cadena MolSysMT o lista de índices).
    structure_indices
        Índices de estructura/frame a extraer.
    view
        Vista existente. Si es None, se crea una nueva `MolSysView`.
    to_form
        Nombre del form de salida para `molsysmt.convert`.
        Ajusta este valor al canonical que tengas en MolSysMT
    **convert_kwargs
        Parámetros extra que quieras pasar a `molsysmt.convert`.
    """

    # 1) Convertir usando MolSysMT
    #    Aquí usa el nombre de form real de tu ecosistema.
    #    Ejemplos posibles (ajusta al que tengas definido):
    #    - to_form="pdb: string"
    #    - to_form="string:pdb"
    pdb_string = msm.convert(
        item,
        to_form=to_form,
        selection=selection,
        structure_indices=structure_indices,
        **convert_kwargs,
    )

    # 2) Crear o reutilizar la vista
    if view is None:
        view = MolSysView()

    # 3) Alimentar Mol* vía el canal que ya funciona
    view.load_pdb_string(pdb_string)

    return view
