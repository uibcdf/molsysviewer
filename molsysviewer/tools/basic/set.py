from __future__ import annotations

from typing import Any

from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "edit"])
def set(
    view: Any,
    *,
    element: str | None = None,
    selection: Any = "all",
    structure_indices: Any = "all",
    syntax: str = "MolSysMT",
    skip_digestion: bool = False,
    **kwargs: Any,
) -> None:
    """Functional wrapper over ``MolSysView.set(...)``."""
    view.set(
        element=element,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=False,
        **kwargs,
    )
