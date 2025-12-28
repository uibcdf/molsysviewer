
from __future__ import annotations

from typing import Any, Sequence, Union

from .viewer import MolSysView

Selection = Union[str, Sequence[int]]
StructureIndices = Union[str, Sequence[int]]

def new_view(
    molecular_system: Any,
    selection: Selection = "all",
    structure_indices: StructureIndices = "all",
    *,
    debug_js: bool | None = None,
    view: MolSysView | None = None,
) -> MolSysView:
    """Create and return a MolSysView, optionally loading a molecular system.

    This is a convenience factory. It instantiates a MolSysView (unless one is
    provided via ``view``), calls ``view.load(...)`` with the given inputs, and
    returns the view.
    """

    view = MolSysView(debug_js=debug_js) if view is None else view
    view.load(
        molecular_system,
        selection=selection,
        structure_indices=structure_indices,
    )
    return view
