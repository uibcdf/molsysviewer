from __future__ import annotations

import pytest

from molsysviewer import MolSysView


PDB_TEXT = """\
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
"""

PDB_TEXT_B = """\
ATOM      1  N   ALA B   1      20.000  20.000  20.000  1.00 20.00           N
ATOM      2  CA  ALA B   1      21.000  20.000  20.000  1.00 20.00           C
ATOM      3  C   ALA B   1      22.000  20.000  20.000  1.00 20.00           C
END
"""

PDB_TEXT_C = """\
ATOM      1  N   GLY C   1      30.000  30.000  30.000  1.00 20.00           N
ATOM      2  CA  GLY C   1      31.000  30.000  30.000  1.00 20.00           C
END
"""


def _import_molsysmt():
    """Import molsysmt or skip the integration test if it is not installed."""
    try:
        import molsysmt as msm  # type: ignore
        return msm
    except ImportError:
        pytest.skip("molsysmt not available for load() integration test")


def test_molsysview_load_uses_molsysmt_payload():
    msm = _import_molsysmt()
    molsys = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")

    view = MolSysView(debug_js=True)
    sent = []
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[attr-defined]

    result = view.load(molsys)
    assert result is None
    assert view.molecular_system is molsys
    assert view.selection == "all"
    assert view.structure_indices == "all"

    assert view._molsys is not None  # noqa: SLF001
    n_atoms = msm.get(view._molsys, element="atom", n_atoms=True)  # noqa: SLF001
    assert n_atoms == 4
    assert view._atom_mask is not None  # noqa: SLF001
    assert view._atom_mask.tolist() == [True] * n_atoms  # noqa: SLF001

    # The scene is retained for the ready handshake, but not sent before the widget is ready.
    msg = next(  # noqa: SLF001
        message
        for message in reversed(view._test_message_log)
        if message.get("op") == "load_molsys_payload"
    )
    assert sent == []

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


# ---------------------------------------------------------------------------
# BUG 1 — load accounting: _load_blocks populated after first load
# ---------------------------------------------------------------------------

def test_first_load_populates_load_blocks():
    """After the first load(), _load_blocks must have exactly one entry and _empty must be False."""
    msm = _import_molsysmt()
    molsys = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")

    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(molsys, label="A")

    assert view._empty is False  # noqa: SLF001
    assert len(view._load_blocks) == 1  # noqa: SLF001

    block = view._load_blocks[0]  # noqa: SLF001
    assert block["index"] == 0
    assert block["n_atoms"] == 4
    assert block["label"] == "A"
    assert block["start"] == 0
    assert block["stop"] == 4


def test_first_load_no_regions_created():
    """After a single load, no regions are created (nothing to distinguish the whole from)."""
    msm = _import_molsysmt()
    molsys = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")

    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(molsys, label="A")

    assert len(view._regions) == 0  # noqa: SLF001


# ---------------------------------------------------------------------------
# Race condition fix — registry_cleared must not wipe Python state
# ---------------------------------------------------------------------------

def test_registry_cleared_does_not_reset_load_blocks():
    """Simulates the async registry_cleared event arriving after load(); _load_blocks must survive."""
    msm = _import_molsysmt()
    molsys = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")

    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(molsys, label="A")
    assert len(view._load_blocks) == 1  # noqa: SLF001

    # Simulate the async registry_cleared event from the frontend.
    view._handle_frontend_event({"event": "registry_cleared"})  # noqa: SLF001

    assert view._empty is False  # noqa: SLF001
    assert len(view._load_blocks) == 1  # noqa: SLF001


def test_registry_cleared_does_not_wipe_regions():
    """Regions created by _ensure_load_regions_after_addition must survive registry_cleared."""
    msm = _import_molsysmt()
    molsys_a = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")
    molsys_b = msm.convert(PDB_TEXT_B, to_form="molsysmt.MolSys")

    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(molsys_a, label="A")
    view.load(molsys_b, label="B")

    assert len(view._regions) == 2  # noqa: SLF001

    # Simulate the async registry_cleared event (e.g. from the rebuild's clear_all).
    view._handle_frontend_event({"event": "registry_cleared"})  # noqa: SLF001

    assert len(view._regions) == 2  # noqa: SLF001


# ---------------------------------------------------------------------------
# BUG 3 — additive load region creation
# ---------------------------------------------------------------------------

def test_second_load_creates_two_regions():
    """After two additive loads, exactly two regions must exist covering each load's atoms."""
    msm = _import_molsysmt()
    molsys_a = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")
    molsys_b = msm.convert(PDB_TEXT_B, to_form="molsysmt.MolSys")

    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(molsys_a, label="A")
    view.load(molsys_b, label="B")

    assert len(view._load_blocks) == 2  # noqa: SLF001
    assert len(view._regions) == 2  # noqa: SLF001

    # Each block must have a region_tag assigned.
    for block in view._load_blocks:  # noqa: SLF001
        assert block["region_tag"] is not None

    # Region A must cover the first 4 atoms; region B the next 3.
    tags = [b["region_tag"] for b in view._load_blocks]  # noqa: SLF001
    region_a = view._regions[tags[0]]  # noqa: SLF001
    region_b = view._regions[tags[1]]  # noqa: SLF001
    assert list(region_a.atom_indices) == list(range(0, 4))
    assert list(region_b.atom_indices) == list(range(4, 7))


def test_third_load_adds_one_region_keeps_existing():
    """After three additive loads, three regions exist and the first two are unchanged."""
    msm = _import_molsysmt()
    molsys_a = msm.convert(PDB_TEXT, to_form="molsysmt.MolSys")
    molsys_b = msm.convert(PDB_TEXT_B, to_form="molsysmt.MolSys")
    molsys_c = msm.convert(PDB_TEXT_C, to_form="molsysmt.MolSys")

    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.load(molsys_a, label="A")
    view.load(molsys_b, label="B")

    # Capture the region tags already assigned after the second load.
    tags_after_2 = {b["region_tag"] for b in view._load_blocks}  # noqa: SLF001

    view.load(molsys_c, label="C")

    assert len(view._load_blocks) == 3  # noqa: SLF001
    assert len(view._regions) == 3  # noqa: SLF001

    # The two original region tags must still be present.
    current_tags = {b["region_tag"] for b in view._load_blocks}  # noqa: SLF001
    assert tags_after_2.issubset(current_tags)

    # The third region covers the last 2 atoms (4+3 = offset 7, 7+2 = 9).
    last_block = view._load_blocks[2]  # noqa: SLF001
    region_c = view._regions[last_block["region_tag"]]  # noqa: SLF001
    assert list(region_c.atom_indices) == list(range(7, 9))
