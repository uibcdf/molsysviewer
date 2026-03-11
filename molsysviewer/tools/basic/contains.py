from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "query"])
def contains(
    view: Any,
    selection: Any = "all",
    *,
    syntax: str = "MolSysMT",
    skip_digestion: bool = False,
    **kwargs: Any,
) -> bool:
    """Viewer-centric wrapper over ``molsysmt.contains(...)``."""
    return bool(
        msm.contains(
            view._molsys,  # noqa: SLF001
            selection=selection,
            syntax=syntax,
            skip_digestion=False,
            **kwargs,
        )
    )
