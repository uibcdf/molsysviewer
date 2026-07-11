
from __future__ import annotations

from typing import Any, Sequence, Union, Literal
import warnings

from smonitor import signal

from .viewer import MolSysView
from ._private.arg_digestion import digest
from depdigest import dep_digest

Selection = Union[str, Sequence[int]]
StructureIndices = Union[str, Sequence[int]]


def _new_view_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    molecular_system = kwargs.get("molecular_system", args[0] if args else None)
    reused_view = kwargs.get("view") is not None
    load_mode = kwargs.get("load_mode", "selection")
    syntax = kwargs.get("syntax", "MolSysMT")
    molecular_system_form = None
    if molecular_system is not None:
        try:
            import molsysmt as msm
            molecular_system_form = msm.get_form(molecular_system)
        except Exception:
            molecular_system_form = type(molecular_system).__name__
    return {
        "load_mode": load_mode,
        "syntax": syntax,
        "reused_view": reused_view,
        "molecular_system_form": molecular_system_form,
    }

@dep_digest('molsysmt')
@signal(tags=["load", "factory"], extra_factory=_new_view_signal_extra)
@digest()
def new_view(
    molecular_system: Any = None,
    selection: Selection = "all",
    structure_indices: StructureIndices = "all",
    *,
    syntax: str = "MolSysMT",
    load_mode: Literal["selection", "all"] = "selection",
    debug_js: bool | None = None,
    view: MolSysView | None = None,
    skip_digestion: bool = False,
    viewer_mode: str | None = None,
    controls_mode: str | None = None,
    panel_mode_style: str | None = None,
    height: str = "480px",
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

    if view is None:
        view = MolSysView(
            debug_js=debug_js,
            viewer_mode=viewer_mode,
            controls_mode=controls_mode,
            panel_mode_style=panel_mode_style,
            height=height,
        )
    if load_mode not in ("selection", "all"):
        raise ValueError("load_mode must be 'selection' or 'all'")

    if molecular_system is None:
        return view

    if load_mode == "selection":
        view.load(
            molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True
        )
        return view

    view.load(
        molecular_system,
        selection="all",
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=True
    )
    selected_atoms = None
    select = getattr(view, "select", None)
    if callable(select):
        selected_atoms = list(select(selection=selection, syntax=syntax, skip_digestion=True))
    if selected_atoms == []:
        warnings.warn(
            f"The selection query {selection!r} resolved to zero atoms. "
            "Showing the whole molecular system instead to prevent an empty screen.",
            UserWarning,
            stacklevel=2,
        )
        return view

    view.whole.hide()
    region = view.regions.add(selection, tag="selection", syntax=syntax, skip_digestion=True)
    region.set_representation("inherit", skip_digestion=True)
    return view
