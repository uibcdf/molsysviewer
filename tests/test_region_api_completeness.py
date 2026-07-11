from __future__ import annotations

import pytest

from molsysviewer.demo import demo


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def _regions(view):
    a = view.new_region(atom_indices=[0, 1, 2, 3, 4], tag="A", skip_digestion=True)
    b = view.new_region(atom_indices=[1, 2], tag="B", skip_digestion=True)
    c = view.new_region(atom_indices=[3], tag="C", skip_digestion=True)
    return a, b, c


def test_variadic_difference_subtracts_every_operand():
    a, b, c = _regions(_mute(demo["dialanine"]))
    d = a.difference(b, c, tag="D", skip_digestion=True)
    # A - (B | C) = {0,1,2,3,4} - {1,2,3} = {0,4}
    assert sorted(d.atom_indices) == [0, 4]


def test_variadic_union_tracks_all_operands():
    a, b, c = _regions(_mute(demo["dialanine"]))
    u = a.union(b, c, tag="U", skip_digestion=True)
    assert sorted(u.atom_indices) == [0, 1, 2, 3, 4]
    assert u.provenance["operands"] == [a.uid, b.uid, c.uid]


def test_variadic_intersection_across_operands():
    view = _mute(demo["dialanine"])
    a = view.new_region(atom_indices=[0, 1, 2, 3], tag="A", skip_digestion=True)
    b = view.new_region(atom_indices=[1, 2, 3], tag="B", skip_digestion=True)
    c = view.new_region(atom_indices=[2, 3, 9], tag="C", skip_digestion=True)
    i = a.intersection(b, c, tag="I", skip_digestion=True)
    # A & B & C = {2, 3}
    assert sorted(i.atom_indices) == [2, 3]
    # A ∩ B ∩ C where C is disjoint on the tail → empty → raises
    empty_c = view.new_region(atom_indices=[7, 8], tag="Z", skip_digestion=True)
    with pytest.raises(ValueError):
        a.intersection(b, empty_c, tag="EMPTY", skip_digestion=True)


def test_single_operand_boolean_still_works():
    a, b, _ = _regions(_mute(demo["dialanine"]))
    d = a.difference(b, tag="D1", skip_digestion=True)
    assert sorted(d.atom_indices) == [0, 3, 4]


def test_boolean_requires_at_least_one_operand():
    a, _, _ = _regions(_mute(demo["dialanine"]))
    with pytest.raises(TypeError):
        a.union(tag="x", skip_digestion=True)


def test_count_regions_by_matches_make_regions_by():
    view = _mute(demo["dialanine"])
    n = view.count_regions_by("group")
    made = view.make_regions_by("group")
    assert n == len(made)
    assert n > 0


def test_count_regions_by_rejects_unknown_element():
    view = _mute(demo["dialanine"])
    with pytest.raises(Exception, match="element"):
        view.count_regions_by("nonsense")


def test_complement_of_several_regions():
    view = _mute(demo["dialanine"])
    view.new_region(atom_indices=[0, 1], tag="A", skip_digestion=True)
    view.new_region(atom_indices=[2, 3], tag="B", skip_digestion=True)
    comp = view.new_region(complement_of_regions=["A", "B"], tag="COMP", skip_digestion=True)
    assert comp.provenance["kind"] == "complement"
    assert len(comp.provenance["of"]) == 2
    assert all(i not in comp.atom_indices for i in [0, 1, 2, 3])
