from __future__ import annotations

import molsysmt as msm

from molsysviewer import MolSysView, demo, tools


def test_tools_basic_concatenate_structures_returns_new_view_from_views():
    view_a = demo["dialanine"]
    view_b = demo["dialanine"]

    result = tools.basic.concatenate_structures([view_a, view_b], debug_js=True)

    assert isinstance(result, MolSysView)
    assert result is not view_a
    assert result is not view_b
    assert msm.get(result._molsys, element="system", n_structures=True, skip_digestion=True) == 2  # noqa: SLF001
    assert result.atom_mask is not None
    assert len(result.atom_mask) == msm.get(result._molsys, element="system", n_atoms=True, skip_digestion=True)  # noqa: SLF001


def test_tools_basic_concatenate_structures_accepts_molecular_systems():
    molsys_a = demo["dialanine"]._molsys  # noqa: SLF001
    molsys_b = demo["dialanine"]._molsys  # noqa: SLF001

    result = tools.concatenate_structures([molsys_a, molsys_b], debug_js=True)

    assert isinstance(result, MolSysView)
    assert msm.get(result._molsys, element="system", n_structures=True, skip_digestion=True) == 2  # noqa: SLF001
