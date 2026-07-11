from __future__ import annotations

import pytest

from molsysviewer.demo import demo

from _edit_helpers import apply_remove


def _quiet(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def test_region_provenance_is_populated_for_creation_routes():
    view = _quiet(demo["dialanine"])

    query = view.regions.add(selection="atom_index < 3", tag="query", skip_digestion=True)
    assert query.provenance["kind"] == "query"
    assert query.provenance["expression"] == "atom_index < 3"
    assert query.provenance["syntax"] == "MolSysMT"

    split = next(iter(view.make_regions_by("chain", representation=None, skip_digestion=True).values()))
    assert split.provenance["kind"] == "split"
    assert split.provenance["element"] == "chain"
    assert "value" in split.provenance

    duplicate = query.duplicate(tag="query-copy", skip_digestion=True)
    assert duplicate.provenance["kind"] == "duplicate"
    assert duplicate.provenance["of"] == query.uid

    complement = query.new_complementary_region(tag="query-complement", skip_digestion=True)
    assert complement.provenance["kind"] == "complement"
    assert complement.provenance["of"] == [query.uid]

    boolean = query.union(duplicate, tag="query-union", skip_digestion=True)
    assert boolean.provenance["kind"] == "boolean"
    assert boolean.provenance["op"] == "or"
    assert boolean.provenance["operands"] == [query.uid, duplicate.uid]


def test_active_and_saved_selection_regions_are_static_index_recipes():
    view = _quiet(demo["dialanine"])
    view.active_selection.set([0, 1], syntax="Indices", skip_digestion=True)

    active_region = view.new_region_from_active_selection(tag="active", skip_digestion=True)
    assert active_region.mode == "static"
    assert active_region.provenance["kind"] == "active_selection"
    assert active_region.provenance["atom_indices"] == [0, 1]

    with pytest.raises(ValueError, match="cannot be dynamic"):
        active_region.mode = "dynamic"

    saved = view.selections.add("saved", atom_indices=[2, 3], skip_digestion=True)
    saved_region = saved.new_region(tag="saved-region", skip_digestion=True)
    assert saved_region.mode == "static"
    assert saved_region.provenance["kind"] == "saved_selection"
    assert saved_region.provenance["atom_indices"] == [2, 3]


def test_region_atom_indices_are_read_only_public_state():
    view = _quiet(demo["dialanine"])
    region = view.regions.add(atom_indices=[0, 1], tag="readonly", skip_digestion=True)

    with pytest.raises(AttributeError):
        region.atom_indices = (2, 3)  # type: ignore[misc]

    region._set_atom_indices([2, 3])  # noqa: SLF001
    assert region.atom_indices == (2, 3)


def test_dynamic_mode_closes_over_reevaluable_compositions():
    view = _quiet(demo["dialanine"])
    left = view.regions.add(selection="atom_index < 3", tag="left", skip_digestion=True)
    right = view.regions.add(selection="atom_index < 4", tag="right", skip_digestion=True)
    static = view.regions.add(atom_indices=[4, 5], tag="static", skip_digestion=True)

    static_union = left.union(static, tag="static-union", skip_digestion=True)
    with pytest.raises(ValueError, match="cannot be dynamic"):
        static_union.mode = "dynamic"

    left.mode = "dynamic"
    right.mode = "dynamic"

    union = left.union(right, tag="union", skip_digestion=True)
    complement = left.new_complementary_region(tag="complement", skip_digestion=True)
    transitive = union.union(complement, tag="transitive", skip_digestion=True)

    assert union.mode == "dynamic"
    assert complement.mode == "dynamic"
    assert transitive.mode == "dynamic"

    left.delete(skip_digestion=True)
    assert union.mode == "static"
    assert transitive.mode == "static"


def test_renaming_operand_does_not_break_uid_based_recipe():
    view = _quiet(demo["dialanine"])
    left = view.regions.add(atom_indices=[0, 1], tag="left", skip_digestion=True)
    right = view.regions.add(atom_indices=[1, 2], tag="right", skip_digestion=True)
    combined = left.union(right, tag="combined", skip_digestion=True)

    left_uid = left.uid
    left.rename("renamed-left", skip_digestion=True)

    assert combined.provenance["operands"][0] == left_uid
    assert combined.dependencies == (left_uid, right.uid)
    assert view.regions.dependencies(skip_digestion=True)["combined"] == (left_uid, right.uid)
    assert combined.uid in view.regions.dependents(skip_digestion=True)["renamed-left"]
    assert view.regions.info("combined")["dependencies"] == (left_uid, right.uid)
    assert combined.atom_indices == (0, 1, 2)


def test_deleting_operand_freezes_dependents_without_cascade():
    view = _quiet(demo["dialanine"])
    left = view.regions.add(atom_indices=[0, 1], tag="left", skip_digestion=True)
    right = view.regions.add(atom_indices=[1, 2], tag="right", skip_digestion=True)
    combined = left.union(right, tag="combined", skip_digestion=True)
    cached = combined.atom_indices

    left.delete(skip_digestion=True)

    assert "left" not in view.regions
    assert "combined" in view.regions
    assert combined.atom_indices == cached
    assert combined.mode == "static"
    assert combined.provenance["broken"] is True
    assert combined.provenance["missing"] == [left.uid]


def test_apply_system_edit_reevaluates_query_region_instead_of_remapping():
    view = _quiet(demo["dialanine"])
    region = view.regions.add(selection="atom_index >= 2", tag="query", skip_digestion=True)
    old_indices = tuple(region.atom_indices or ())
    assert old_indices[:2] == (2, 3)

    apply_remove(view, selection=[0])

    n_atoms = int(view.molsys.get_n_atoms())
    assert region.atom_indices == tuple(range(2, n_atoms))
    assert region.atom_indices != tuple(index - 1 for index in old_indices)
