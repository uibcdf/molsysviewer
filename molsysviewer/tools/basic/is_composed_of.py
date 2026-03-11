from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "query"])
def is_composed_of(
    view: Any,
    selection: Any = "all",
    *,
    syntax: str = "MolSysMT",
    skip_digestion: bool = False,
    **kwargs: Any,
) -> bool:
    """Viewer-centric wrapper over ``molsysmt.is_composed_of(...)``."""
    return bool(
        msm.is_composed_of(
            view._molsys,  # noqa: SLF001
            selection=selection,
            syntax=syntax,
            skip_digestion=False,
            **kwargs,
        )
    )
