"""Regression tests for the demo catalog after switching to MolSysMT systems.

MolSysViewer no longer vendors its own ``.h5msm`` demo files; every demo is
resolved through ``molsysmt.systems`` (the ecosystem's single source of truth).
These tests pin the two properties that motivated the change:

- the resolved systems are equivalent to the historical ones (atom counts), and
- crystal structures keep their per-atom ``b_factor`` (the original defect was
  that the bundled copies had silently dropped it).
"""

from __future__ import annotations

import warnings

import molsysmt as msm

from molsysviewer.demo import demo


def _attributes(view):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return set(
            msm.get_attributes(
                view.molsys,
                include_none=False,
                output_type="list",
                skip_digestion=True,
            )
        )


EXPECTED_N_ATOMS = {
    "dialanine": 22,
    "1TCD": 3983,
    "181L": 1441,
    "pentalanine": 62,
    "chicken_villin_HP35": 4369,
}


def test_all_demos_resolve_with_expected_atom_counts():
    for key, n_atoms in EXPECTED_N_ATOMS.items():
        view = demo[key]
        assert int(view.molsys.get_n_atoms()) == n_atoms, key


def test_crystal_demos_expose_b_factor():
    # 181L and 1TCD are crystal structures; b_factor must be present. This is the
    # root fix: the previously bundled copies (and even MolSysMT's 1tcd.h5msm) had
    # dropped it, so the demos are resolved from the .pdb form that carries it.
    for key in ("181L", "1TCD"):
        assert "b_factor" in _attributes(demo[key]), key


def test_non_crystal_demo_has_no_b_factor():
    # dialanine is a minimal capped peptide with no experimental b-factors.
    assert "b_factor" not in _attributes(demo["dialanine"])
