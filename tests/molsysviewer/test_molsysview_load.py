from __future__ import annotations

import sys
from pathlib import Path

import pytest

from molsysviewer import MolSysView


PDB_TEXT = """\
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
"""


def _import_molsysmt():
    """Import molsysmt, adding the sibling repo path if needed."""
    try:
        import molsysmt as msm  # type: ignore
        return msm
    except ImportError:
        repo_root = Path(__file__).resolve().parents[2]
        sibling_repo = repo_root.parent / "molsysmt"
        if sibling_repo.exists():
            sys.path.insert(0, str(sibling_repo))
            try:
                import molsysmt as msm  # type: ignore
                return msm
            except ImportError:
                pass
    pytest.skip("molsysmt not available for load() integration test")


def test_molsysview_load_uses_molsysmt_payload():
    msm = _import_molsysmt()
    molsys = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")

    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    result = view.load(molsys)
    assert result is None
    assert view.molecular_system is molsys
    assert view.selection == "all"
    assert view.structure_indices == "all"

    assert view._molsys is not None  # noqa: SLF001
    n_atoms = msm.get(view._molsys, element="atom", n_atoms=True)  # noqa: SLF001
    assert n_atoms == 4
    assert view.atom_mask is not None  # noqa: SLF001
    assert view.atom_mask.tolist() == [True] * n_atoms  # noqa: SLF001

    # Message is queued because the widget isn't ready yet.
    assert view._pending_messages  # noqa: SLF001
    msg = view._pending_messages[-1]  # noqa: SLF001
    assert msg["op"] == "load_molsys_payload"

    payload = msg["payload"]
    atoms = payload["atoms"]
    assert atoms["atom_id"] == list(range(1, n_atoms + 1))

    structures = payload["structures"]
    assert isinstance(structures, list) and len(structures) == 1
    coords = structures[0]["coordinates"]
    assert len(coords) == n_atoms
    # Coordinates should match the PDB input (Å) after MolSysMT conversion.
    assert coords[0][0] == pytest.approx(11.104)
    assert coords[0][1] == pytest.approx(13.207)
    assert coords[0][2] == pytest.approx(8.551)
