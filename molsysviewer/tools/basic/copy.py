from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

from ...new_view import new_view
from .merge import _import_view_state


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "view"])
def copy(
    view: Any,
    *,
    debug_js: bool | None = None,
    skip_digestion: bool = False,
):
    """Return an independent copy of a view, including useful scene state."""
    copied = msm.copy(view._molsys, skip_digestion=False)  # noqa: SLF001
    result = new_view(
        copied,
        selection="all",
        structure_indices="all",
        debug_js=view._debug_js if debug_js is None else debug_js,  # noqa: SLF001
        skip_digestion=True,
    )
    _import_view_state(result, [view])
    return result
