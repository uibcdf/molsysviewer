"""What a state document promises when it is loaded onto a different system.

Issue #38 asks what `save_state` promises. This file covers the first of its answers:
a document records the system it was written from, and when that is not the system you
load it onto, the objects are **re-resolved** rather than replayed at indices that mean
something else here.

The design in one line: an atom index is where an atom sat, not what it is. A document
carries both -- indices for the fast path back onto the same system, and identity
(`chain_id`, `group_id`, `group_name`, `atom_name`) for everything else. Regions carry
neither: Contract R already says a region *is* its recipe, so a region is re-evaluated.

An earlier draft of this work refused the import outright when the atom counts differed.
That was both too strict, since loading onto a related structure is a capability
Contract S7 tests, and too weak, since it never fired on the case that actually hurts --
a system of the same size whose indices address different atoms.
"""

from __future__ import annotations

import warnings

import molsysmt as msm
import pytest
from molsysviewer._private.smonitor.warnings import StateStructureDiffersWarning
from molsysviewer.demo import demo

import molsysviewer as msv


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


@pytest.fixture(scope="module")
def shifted_181l():
    """181L with its first group removed, so every remaining atom keeps its identity
    and loses its index. This is the fixture the whole design is for."""
    source = _mute(demo["181L"])
    return msm.extract(source._molsys, selection="group_index>0",  # noqa: SLF001
                       to_form="molsysmt.MolSys")


def test_export_state_records_the_system_it_was_written_from():
    view = _mute(demo["dialanine"])

    recorded = view.export_state()["structure"]

    assert recorded["n_atoms"] == view._molsys.get_n_atoms()  # noqa: SLF001
    assert recorded["fingerprint"].startswith("sha256:")


def test_the_fingerprint_is_topological_so_a_state_saved_at_one_frame_loads_at_another():
    """A fingerprint over coordinates would make every document valid at exactly one
    frame, which is not a portability guarantee anybody wants."""
    view = _mute(demo["pentalanine"])

    view.structure_index = 0
    at_first_frame = view.export_state()["structure"]["fingerprint"]
    view.structure_index = 500
    at_later_frame = view.export_state()["structure"]["fingerprint"]

    assert at_first_frame == at_later_frame


def test_a_document_written_before_this_key_existed_still_imports_in_silence():
    """Contract S5's additive-key rule, which is the reason this is v2 and not v3."""
    view = _mute(demo["dialanine"])
    view.annotations.add("site", atom_indices=[0, 1], tag="note1")
    document = view.export_state()
    older = {key: value for key, value in document.items() if key != "structure"}

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        view.import_state(older)

    assert view.annotations.tags() == ["note1"]


def test_returning_to_the_same_system_says_nothing_and_re_resolves_nothing():
    """The fast path. Re-resolution is for documents that travelled; most do not."""
    view = _mute(demo["181L"])
    view.annotations.add("site", atom_indices=[0, 1], tag="note1")
    document = view.export_state()

    with warnings.catch_warnings():
        warnings.simplefilter("error", StateStructureDiffersWarning)
        view.import_state(document)

    assert view.annotations.info("note1")["broken"] is False


def test_an_annotation_follows_its_atoms_to_their_new_indices(shifted_181l):
    """The point of the whole mechanism: the same atom, at a different index.

    Removing 181L's first group shifts every later atom down by eight. An annotation
    written at index 10 must come back at index 2 -- because both are
    ``(A, 2, ASN, C)`` -- and not at index 10, which is now a different atom entirely.
    """
    source = _mute(demo["181L"])
    query = "chain_id=='A' and group_id==2 and atom_name=='C'"
    index_here = int(msm.select(source._molsys, selection=query, syntax="MolSysMT")[0])  # noqa: SLF001
    source.annotations.add("same atom", atom_indices=[index_here], tag="follow")
    document = source.export_state()

    target = _mute(msv.new_view(shifted_181l))
    index_there = int(msm.select(shifted_181l, selection=query, syntax="MolSysMT")[0])
    assert index_there != index_here, "the fixture must actually move the atom"

    with pytest.warns(StateStructureDiffersWarning):
        target.import_state(document)

    restored = target.annotations.info("follow")
    assert restored["broken"] is False
    assert restored["atom_indices"] == [index_there]


def test_a_region_is_re_evaluated_from_its_recipe_not_replayed_from_its_atoms():
    """Contract R, which the document has always carried and import used to ignore.

    Before this, a region built on 181L arrived on dialanine still holding 162 atom
    indices reaching past 1200 -- on a system of 22 atoms.
    """
    source = _mute(demo["181L"])
    source.regions.add(selection="atom_name=='CA'", tag="cas")
    document = source.export_state()

    target = _mute(demo["dialanine"])
    expected = len(msm.select(target._molsys, selection="atom_name=='CA'", syntax="MolSysMT"))  # noqa: SLF001

    with pytest.warns(StateStructureDiffersWarning):
        target.import_state(document)

    restored = target.regions.info("cas")
    assert restored["n_atoms"] == expected
    assert max(restored["atom_indices"]) < target._molsys.get_n_atoms()  # noqa: SLF001


def test_objects_whose_atoms_are_absent_break_rather_than_land_somewhere_plausible():
    """Contract S7: a believable wrong value is the worst outcome in this codebase."""
    source = _mute(demo["181L"])
    source.annotations.add("site", atom_indices=[0, 1], tag="a1")
    source.measurements.add_distance([0], [1], tag="m1")
    source.selections.add("s1", atom_indices=[0, 1])
    document = source.export_state()

    target = _mute(demo["dialanine"])
    with pytest.warns(StateStructureDiffersWarning):
        target.import_state(document)

    assert target.annotations.info("a1")["broken"] is True
    assert target.measurements.info("m1")["broken"] is True
    assert target.measurements.info("m1")["value"] is None, "a stale number survived"
    # A saved selection has no broken state to fall into, so it is not restored at all
    # rather than restored holding indices that address other atoms.
    assert "s1" not in target.selections.tags()


def test_the_warning_carries_its_catalog_code_and_both_atom_counts():
    source = _mute(demo["181L"])
    document = source.export_state()
    target = _mute(demo["dialanine"])

    with pytest.warns(StateStructureDiffersWarning) as caught:
        target.import_state(document)

    warning = caught[0].message
    assert warning.code == "MOLSYSVIEWER-STATE-STRUCTURE-DIFFERS"
    assert "1441" in str(warning) and "22" in str(warning)
    assert issubclass(caught[0].category, UserWarning)


def test_an_identity_that_matches_two_atoms_breaks_rather_than_picking_one():
    """Identity is only usable while it identifies.

    Merging dialanine with itself gives a system where every atom's
    ``(chain_id, group_id, group_name, atom_name)`` names two atoms. Resolving to the
    first one would be a guess wearing the clothes of a resolution, and the caller could
    not tell the difference -- so the anchor is refused and the object is marked broken.
    """
    source = _mute(demo["dialanine"])
    source.annotations.add("site", atom_indices=[0], tag="ambiguous")
    document = source.export_state()

    doubled = msm.merge([source._molsys, source._molsys])  # noqa: SLF001
    target = _mute(msv.new_view(doubled))

    with pytest.warns(StateStructureDiffersWarning):
        target.import_state(document)

    assert target.annotations.info("ambiguous")["broken"] is True
