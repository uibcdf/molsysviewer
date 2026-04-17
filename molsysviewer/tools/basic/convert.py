from __future__ import annotations

from typing import Any

from depdigest import dep_digest
from smonitor import signal


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "convert"])
def convert(
    view: Any,
    to_form: Any = "molsysmt.MolSys",
    *,
    selection: Any = "all",
    structure_indices: Any = "all",
    syntax: str = "MolSysMT",
    skip_digestion: bool = False,
    **kwargs: Any,
):
    """Functional wrapper over ``MolSysView.convert(...)``."""
    return view.convert(
        to_form=to_form,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=False,
        **kwargs,
    )
