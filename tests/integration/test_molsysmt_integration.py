import pytest

msm = pytest.importorskip("molsysmt")

from molsysviewer import MolSysView
from molsysviewer.loaders.load_molsysmt import _serialize_molsys_payload


PDB_TEXT = """\
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
"""


def test_load_pdb_string_uses_molsysmt():
    view = MolSysView()
    view.load_pdb_string(PDB_TEXT)
    assert view._molsys is not None
    assert view.atom_mask is not None
    expected_atoms = msm.get(view._molsys, element="atom", n_atoms=True)
    assert len(view.atom_mask) == expected_atoms
    assert any(msg.get("op") == "load_structure_from_string" for msg in view._pending_messages)


def test_load_molsys_payload_or_fallback():
    molsys = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")
    payload = _serialize_molsys_payload(molsys)
    assert payload is not None

    view = MolSysView()
    view.load(molsys)
    assert view._molsys is not None
    assert view.atom_mask is not None
    expected_atoms = msm.get(view._molsys, element="atom", n_atoms=True)
    assert len(view.atom_mask) == expected_atoms
    ops = {msg.get("op") for msg in view._pending_messages}
    assert ops & {"load_molsys_payload", "load_structure_from_string"}
