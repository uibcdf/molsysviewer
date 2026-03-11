from __future__ import annotations

from typing import Any

from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "edit"])
def remove(
    view: Any,
    *,
    selection: Any | None = None,
    structure_indices: Any | None = None,
    syntax: str = "MolSysMT",
    skip_digestion: bool = False,
) -> None:
    """Functional wrapper over ``MolSysView.remove(...)``."""
    view.remove(
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=False,
    )
