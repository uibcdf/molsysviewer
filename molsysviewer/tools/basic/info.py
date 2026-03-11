from __future__ import annotations

from typing import Any

from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "query"])
def info(
    view: Any,
    *,
    element: str = "system",
    selection: Any = "all",
    syntax: str = "MolSysMT",
    mask: Any = "all",
    skip_digestion: bool = False,
):
    """Functional wrapper over ``MolSysView.info(...)``."""
    return view.info(
        element=element,
        selection=selection,
        syntax=syntax,
        mask=mask,
        skip_digestion=False,
    )
