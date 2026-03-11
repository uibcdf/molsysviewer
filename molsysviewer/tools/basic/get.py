from __future__ import annotations

from typing import Any

from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "query"])
def get(
    view: Any,
    *,
    element: str = "system",
    selection: Any = "all",
    structure_indices: Any = "all",
    mask: Any = None,
    syntax: str = "MolSysMT",
    get_missing_bonds: bool = True,
    output_type: str = "values",
    skip_digestion: bool = False,
    **kwargs: Any,
):
    """Functional wrapper over ``MolSysView.get(...)``."""
    return view.get(
        element=element,
        selection=selection,
        structure_indices=structure_indices,
        mask=mask,
        syntax=syntax,
        get_missing_bonds=get_missing_bonds,
        output_type=output_type,
        skip_digestion=False,
        **kwargs,
    )
