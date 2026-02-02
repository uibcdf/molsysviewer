
from __future__ import annotations

from typing import Any, Sequence, Union, Literal

from .viewer import MolSysView
from ._private.digestion import digest

Selection = Union[str, Sequence[int]]
StructureIndices = Union[str, Sequence[int]]

@digest()
def new_view(
    molecular_system: Any,
    selection: Selection = "all",
    structure_indices: StructureIndices = "all",
    *,
    syntax: str = "MolSysMT",
    load_mode: Literal["selection", "all"] = "selection",
    debug_js: bool | None = None,
    view: MolSysView | None = None,
    skip_digestion: bool = False,
) -> MolSysView:
    """Create and return a MolSysView, optionally loading a molecular system.

    This is a convenience factory. It instantiates a MolSysView (unless one is
    provided via ``view``), calls ``view.load(...)`` with the given inputs, and
    returns the view.

    Parameters
    ----------
    syntax
        Selection syntax understood by MolSysMT.
    skip_digestion
        Whether to skip MolSysViewer digestion for this call.
    load_mode
        - ``"selection"`` (default): the selection is used to subset the system
          before loading. The view only contains the selected atoms.
        - ``"all"``: the full system is loaded, the global representation is
          hidden, and a region tagged ``"selection"`` is created for the given
          selection (it inherits the global representation or uses ``"auto"``).
    """

    view = MolSysView(debug_js=debug_js) if view is None else view
    if load_mode not in ("selection", "all"):
        raise ValueError("load_mode must be 'selection' or 'all'")

    if load_mode == "selection":
        view.load(
            molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True
        )
        return view

    view.whole.hide()
    view.load(
        molecular_system,
        selection="all",
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=True
    )
    region = view.new_region(selection, tag="selection", syntax=syntax, skip_digestion=True)
    preset = getattr(view.whole, "_preset", None)
    representation = getattr(view.whole, "_representation", None)
    params = getattr(view.whole, "_repr_params", {}) or {}
    if preset is None and representation is None:
        preset = "auto"
    region.set_representation(representation, preset=preset, skip_digestion=True, **params)
    return view
