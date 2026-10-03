from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

from ..._private.argdigest import digest
from ...new_view import new_view
from ._scene_transfer import _copy_auxiliary, _transfer_state


def _build_atom_index_map(molsys: Any, selection: Any, syntax: str) -> dict[int, int]:
    """Return ``{old_atom_index: new_atom_index}`` for the atoms kept by *selection*."""
    selected = msm.select(molsys, selection=selection, syntax=syntax, skip_digestion=False)
    return {int(old): new for new, old in enumerate(selected)}


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "extract"])
@digest()
def extract(
    view: Any,
    selection: Any = "all",
    structure_indices: Any = "all",
    *,
    syntax: str = "MolSysMT",
    debug_js: bool | None = None,
    skip_digestion: bool = False,
):
    """Return a new view built from a structural subset of an existing view.

    Unlike a plain structural extract, the relevant scene state is migrated to
    the new view with atom indices remapped to the extracted subset:

    * **Regions** — recreated for any region that has at least one atom in the
      selection (surviving atoms only).
    * **Shapes** — atom-anchored shapes are migrated only if their anchor atoms
      survive; world-space shapes (no atom reference) are always migrated.
    * **Measurements** — remapped; missing endpoints are explicitly broken.
    * **Annotations** — migrated only when their anchor atoms survive.
    * **Saved selections** — remapped; dropped if no atoms survive.
    * **Sections** — always migrated (world-space clipping planes).
    * **Interactions** — named analyses and displays remapped by atoms and structures.
    * **Global settings** — whole representation, background, camera snapshot,
      and widget controls are copied from the source.

    Parameters
    ----------
    view
        Source ``MolSysView``.
    selection
        Atom selection expression (default ``"all"``).
    structure_indices
        Structure / frame indices to keep (default ``"all"``).
    syntax
        Selection syntax (default ``"MolSysMT"``).
    debug_js
        Override the JS debug flag.  Defaults to the source view's setting.
    """
    atom_index_map = _build_atom_index_map(view._molsys, selection, syntax)  # noqa: SLF001

    extracted = msm.extract(
        view._molsys,  # noqa: SLF001
        selection=selection,
        structure_indices=structure_indices,
        to_form="molsysmt.MolSys",
        syntax=syntax,
        skip_digestion=False,
    )
    result = new_view(
        extracted,
        selection="all",
        structure_indices="all",
        syntax=syntax,
        debug_js=view._debug_js if debug_js is None else debug_js,  # noqa: SLF001
        skip_digestion=True,
    )
    from ...interactions import _indices
    frames = None if structure_indices is None or isinstance(structure_indices, str) and structure_indices == "all" else _indices(structure_indices, view._molsys.structures.n_structures, "structure_indices", unique=False)
    if frames is None:
        frames = range(view._molsys.structures.n_structures)
    result.import_state(_transfer_state(view, result, atom_index_map, list(frames)))
    _copy_auxiliary(view, result, atom_index_map)
    return result
