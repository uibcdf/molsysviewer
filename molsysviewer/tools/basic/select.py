from __future__ import annotations

from typing import Any

from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "selection"])
def select(
    view: Any,
    selection: Any = "all",
    structure_indices: Any = "all",
    *,
    element: str = "atom",
    mask: Any = None,
    syntax: str = "MolSysMT",
    skip_digestion: bool = False,
):
    """Functional wrapper over ``MolSysView.select(...)``."""
    return view.select(
        selection=selection,
        structure_indices=structure_indices,
        element=element,
        mask=mask,
        syntax=syntax,
        skip_digestion=False,
    )
