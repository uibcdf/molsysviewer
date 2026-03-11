from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

from ...new_view import new_view


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "extract"])
def extract(
    view: Any,
    selection: Any = "all",
    structure_indices: Any = "all",
    *,
    syntax: str = "MolSysMT",
    debug_js: bool | None = None,
    skip_digestion: bool = False,
):
    """Return a new view built from a subset of another ``MolSysView``."""
    extracted = msm.extract(
        view._molsys,  # noqa: SLF001
        selection=selection,
        structure_indices=structure_indices,
        to_form="molsysmt.MolSys",
        syntax=syntax,
        skip_digestion=False,
    )
    return new_view(
        extracted,
        selection="all",
        structure_indices="all",
        syntax=syntax,
        debug_js=view._debug_js if debug_js is None else debug_js,  # noqa: SLF001
        skip_digestion=True,
    )
