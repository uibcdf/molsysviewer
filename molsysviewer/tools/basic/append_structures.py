from __future__ import annotations

from typing import Any

from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "edit"])
def append_structures(
    view: Any,
    from_molecular_system: Any,
    *,
    selection: Any = "all",
    structure_indices: Any = "all",
    syntax: str = "MolSysMT",
    skip_digestion: bool = False,
) -> None:
    """Functional wrapper over ``MolSysView.append_structures(...)``."""
    view.append_structures(
        from_molecular_system,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=False,
    )
