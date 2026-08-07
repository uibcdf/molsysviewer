from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

from ..._private.argdigest import digest
from ...new_view import new_view
from ...viewer import MolSysView


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "structure"])
@digest()
def concatenate_structures(
    molecular_systems: Any,
    selections: Any = "all",
    structure_indices: Any = "all",
    *,
    syntax: str = "MolSysMT",
    debug_js: bool | None = None,
    skip_digestion: bool = False,
) -> MolSysView:
    """Return a new view built from the concatenated structures of multiple inputs.

    Inputs may be MolSysMT-compatible molecular systems or existing ``MolSysView``
    objects. The resulting topology is inherited from the first input, following
    MolSysMT's ``concatenate_structures(...)`` contract.
    """

    concatenated = msm.concatenate_structures(
        molecular_systems,
        selections=selections,
        structure_indices=structure_indices,
        syntax=syntax,
        to_form="molsysmt.MolSys",
        skip_digestion=True,
    )

    return new_view(
        concatenated,
        selection="all",
        structure_indices="all",
        syntax=syntax,
        debug_js=debug_js,
        skip_digestion=True,
    )
