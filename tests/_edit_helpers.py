"""Test helpers reproducing live molecular edits via the public
``view.apply_system_edit(...)`` primitive.

The former ``view.remove/add/set/append_structures`` methods were removed: the
molecular-edit semantics now live in the MolSysMT addon
(``view.addons.molsysmt.basic.*``), while MolSysViewer core keeps only the
low-level reconciliation primitive ``view.apply_system_edit(...)``.

These helpers compute the molecular edit with MolSysMT and then apply it through
the primitive, so the reconciliation-focused core tests exercise
``apply_system_edit`` directly without depending on the addon.
"""

from __future__ import annotations

from typing import Any

import molsysmt as msm


def apply_remove(
    view: Any,
    *,
    selection: Any | None = None,
    structure_indices: Any | None = None,
    syntax: str = "MolSysMT",
) -> None:
    atom_index_map: dict[int, int] | None = None
    if selection is not None:
        removed = set(msm.select(view.molsys, selection=selection, syntax=syntax, skip_digestion=True))
        n_atoms = int(msm.get(view.molsys, element="system", n_atoms=True, skip_digestion=True))
        kept = [i for i in range(n_atoms) if i not in removed]
        atom_index_map = {old: new for new, old in enumerate(kept)}
    new_molsys = msm.remove(
        view.molsys,
        selection=selection,
        structure_indices=structure_indices,
        to_form="molsysmt.MolSys",
        syntax=syntax,
        skip_digestion=True,
    )
    view.apply_system_edit(new_molsys, atom_index_map=atom_index_map, load_blocks="collapse")


def apply_add(
    view: Any,
    from_molecular_system: Any,
    *,
    selection: Any = "all",
    structure_indices: Any = "all",
    keep_ids: bool = True,
    syntax: str = "MolSysMT",
    label: str | None = None,
) -> None:
    added = msm.convert(
        from_molecular_system,
        to_form="molsysmt.MolSys",
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=True,
    )
    added_n_atoms = int(added.get_n_atoms())
    msm.add(
        view.molsys,
        added,
        selection="all",
        structure_indices="all",
        keep_ids=keep_ids,
        in_place=True,
        syntax=syntax,
        skip_digestion=True,
    )
    view.apply_system_edit(
        view.molsys,
        label=label,
        load_blocks="append",
        appended_n_atoms=added_n_atoms,
    )


def apply_append_structures(
    view: Any,
    from_molecular_system: Any,
    *,
    selection: Any = "all",
    structure_indices: Any = "all",
    syntax: str = "MolSysMT",
) -> None:
    msm.append_structures(
        view.molsys,
        from_molecular_system,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        in_place=True,
        skip_digestion=True,
    )
    view.apply_system_edit(view.molsys)


def apply_set(
    view: Any,
    *,
    element: str | None = None,
    selection: Any = "all",
    structure_indices: Any = "all",
    syntax: str = "MolSysMT",
    **kwargs: Any,
) -> None:
    msm.set(
        view.molsys,
        element=element,
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=True,
        **kwargs,
    )
    view.apply_system_edit(view.molsys)
