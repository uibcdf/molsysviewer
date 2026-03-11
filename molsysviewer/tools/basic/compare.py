from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "query"])
def compare(
    view: Any,
    view_2: Any,
    *,
    selection: Any = "all",
    structure_indices: Any = "all",
    selection_2: Any = "all",
    structure_indices_2: Any = "all",
    syntax: str = "MolSysMT",
    rule: str = "equal",
    output_type: str = "boolean",
    attribute_type: str | None = None,
    include_none: bool = False,
    redefine_indices: bool = False,
    skip_digestion: bool = False,
    **kwargs: Any,
):
    """Compare the loaded molecular systems of two views.

    This compares the underlying molecular systems, not the visual scene state.
    """
    return msm.compare(
        view._molsys,  # noqa: SLF001
        view_2._molsys,  # noqa: SLF001
        selection=selection,
        structure_indices=structure_indices,
        selection_2=selection_2,
        structure_indices_2=structure_indices_2,
        syntax=syntax,
        rule=rule,
        output_type=output_type,
        attribute_type=attribute_type,
        include_none=include_none,
        redefine_indices=redefine_indices,
        skip_digestion=False,
        **kwargs,
    )
