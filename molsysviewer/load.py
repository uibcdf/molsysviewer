
from __future__ import annotations

from typing import Any, Sequence, Union

from .viewer import MolSysView

Selection = Union[str, Sequence[int]]
StructureIndices = Union[str, Sequence[int]]

def load(
    molecular_system: Any,
    selection: Selection = "all",
    structure_indices: StructureIndices = "all",
    view: MolSysView | None = None,
) -> MolSysView:

    view = MolSysView() if view is None else view
    view.load(
        molecular_system,
        selection=selection,
        structure_indices=structure_indices,
    )
    return view


