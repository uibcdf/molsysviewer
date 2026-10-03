# molsysviewer/loaders/load_molsysmt.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import molsysmt as msm
from smonitor import signal

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


def _prepare_molsysmt_load(
    molecular_system: Any,
    *,
    selection: str | Any = "all",
    structure_indices: str | Any = "all",
    syntax: str = "MolSysMT",
):
    """Convert and resolve source mappings before changing any Viewer state."""
    converted_molsys = msm.convert(
        molecular_system,
        to_form="molsysmt.MolSys",
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        # Complementary forms still need the provider's correspondence/domain
        # validation. Viewer digestion validates selectors, not scientific file
        # composition; bypassing this lets incomplete H5MSM domains reach native
        # conversion internals (uibcdf/molsysmt#309).
        skip_digestion=not isinstance(molecular_system, (list, tuple)),
    )
    # Keep original <-> loaded-system mapping only as reference/provenance.
    # Runtime state and frontend payloads use the converted MolSys index space.
    atom_index_mapper = None
    structure_index_mapper = None
    from ..viewer.index_mapper import IndexMapper

    if not _is_all_selector(selection):
        atom_index_mapper = IndexMapper(
            molecular_system,
            selection=selection,
            structure_indices="all",
            syntax=syntax,
            build_atoms=True,
            build_structures=False,
        )
    if not _is_all_selector(structure_indices):
        structure_index_mapper = IndexMapper(
            molecular_system,
            selection="all",
            structure_indices=structure_indices,
            syntax=syntax,
            build_atoms=False,
            build_structures=True,
        )
    if _is_all_selector(selection) and _is_all_selector(structure_indices):
        analyses = getattr(molecular_system, "interactions", {})
        if analyses and msm.get_form(molecular_system) == "molsysmt.MolSys":
            # A full load retains immutable analysis snapshots and occurrence
            # identities. Generic conversion can remap even unchanged axes,
            # reordering evaluated coverage; extraction still uses its remap.
            converted_molsys.interactions = dict(analyses)
    n_atoms = int(converted_molsys.get_n_atoms())
    n_structures = int(converted_molsys.structures.n_structures)

    # This warning concerns materialized coordinates and therefore applies to
    # both the binary path and the lazy JSON fallback.
    if n_structures:
        check_structure_scale(
            n_atoms,
            n_structures,
            budget_bytes=scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES,
        )

    return (converted_molsys, molecular_system, selection, structure_indices,
            atom_index_mapper, structure_index_mapper)


def _commit_molsysmt_load(view, prepared, *, label=None):
    (converted_molsys, molecular_system, selection, structure_indices,
     atom_index_mapper, structure_index_mapper) = prepared
    view.molecular_system = molecular_system
    view.selection = selection
    view.structure_indices = structure_indices
    view._atom_index_mapper = atom_index_mapper
    view._structure_index_mapper = structure_index_mapper
    view._current_structure_index = 0
    view.interactions._system_changed()
    view._molsys = converted_molsys
    view._invalidate_system_identity()
    view._send(view._new_lazy_molecular_projection(label=label))
    return view


@signal()
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
    prepared = _prepare_molsysmt_load(
        molecular_system, selection=selection, structure_indices=structure_indices, syntax=syntax,
    )
    view.trajectory_plot._check_structure_axis(prepared[0].structures.n_structures)
    return _commit_molsysmt_load(view, prepared, label=label)
