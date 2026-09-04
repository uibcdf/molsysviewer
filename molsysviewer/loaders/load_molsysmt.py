# molsysviewer/loaders/load_molsysmt.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import molsysmt as msm

from .._private import scale_budget
from .._private.argdigest import digest
from .._private.scale_budget import check_structure_scale

if TYPE_CHECKING:
    from ..viewer import MolSysView


def _is_all_selector(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value == "all")


def ensure_view(view: "MolSysView" | None = None) -> "MolSysView":
    if view is None:
        from ..viewer import MolSysView

        view = MolSysView()
    return view


@digest()
def load_from_molsysmt(
    molecular_system: Any,
    *,
    selection: str | Any = "all",
    structure_indices: str | Any = "all",
    syntax: str = "MolSysMT",
    label: str | None = None,
    view: "MolSysView | None" = None,
    skip_digestion: bool = False,
) -> "MolSysView":
    """Convert a MolSysMT-compatible input and register a lazy load projection."""

    view = ensure_view(view)
    view.molecular_system = molecular_system
    view.selection = selection
    view.structure_indices = structure_indices

    # Keep original <-> loaded-system mapping only as reference/provenance.
    # Runtime state and frontend payloads use the converted MolSys index space.
    view._atom_index_mapper = None
    view._structure_index_mapper = None
    from ..viewer.index_mapper import IndexMapper

    if not _is_all_selector(selection):
        view._atom_index_mapper = IndexMapper(
            molecular_system,
            selection=selection,
            structure_indices="all",
            syntax=syntax,
            build_atoms=True,
            build_structures=False,
        )
    if not _is_all_selector(structure_indices):
        view._structure_index_mapper = IndexMapper(
            molecular_system,
            selection="all",
            structure_indices=structure_indices,
            syntax=syntax,
            build_atoms=False,
            build_structures=True,
        )
    view._current_structure_index = 0

    view._molsys = msm.convert(
        molecular_system,
        to_form="molsysmt.MolSys",
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=True,
    )

    n_atoms = int(view._molsys.get_n_atoms())
    n_structures = int(view._molsys.structures.n_structures)

    # This warning concerns materialized coordinates and therefore applies to
    # both the binary path and the lazy JSON fallback.
    if n_structures:
        check_structure_scale(
            n_atoms,
            n_structures,
            budget_bytes=scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES,
        )

    view._send(view._new_lazy_molecular_projection(label=label))
    return view
