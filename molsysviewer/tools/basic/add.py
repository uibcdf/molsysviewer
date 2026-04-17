from __future__ import annotations

from typing import Any

from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "edit"])
def add(
    view: Any,
    from_molecular_system: Any,
    *,
    selection: Any = "all",
    structure_indices: Any = "all",
    keep_ids: bool = True,
    syntax: str = "MolSysMT",
    label: str | None = None,
    skip_digestion: bool = False,
) -> None:
    """Functional wrapper over ``MolSysView.add(...)``."""
    view.add(
        from_molecular_system,
        selection=selection,
        structure_indices=structure_indices,
        keep_ids=keep_ids,
        syntax=syntax,
        label=label,
        skip_digestion=False,
    )
