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


def test_extract_returns_a_view_of_the_subset():
    view = demo["dialanine"]

    subset = view.extract(selection=[0, 1, 2], debug_js=True)
    assert isinstance(subset, MolSysView)
    assert msm.get(subset._molsys, element="system", n_atoms=True, skip_digestion=True) == 3  # noqa: SLF001


def test_get_answers_what_contains_and_is_composed_of_used_to_wrap():
    """The two questions survive; the two methods that wrapped them do not.

    `contains` and `is_composed_of` were removed from the view, the whole and regions in
    `uibcdf/molsysviewer#71` — `get` already carries the information, and `msm.contains`
    and `msm.is_composed_of` are still there for anyone who wants the direct form. This
    pins the translation rather than leaving it to a changelog.
    """
    view = demo["dialanine"]

    # was: view.contains(n_peptides=True) is True
    assert view.whole.get(n_peptides=True) > 0
    # was: view.is_composed_of(n_molecules=1) is True
    assert view.whole.get(n_molecules=True) == 1


def test_a_region_scopes_element_level_attributes_to_its_own_atoms():
    view = demo["dialanine"]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", skip_digestion=True)

    assert list(region.get(element="atom", index=True)) == [0, 1, 2]


def test_a_callers_mask_narrows_a_region_and_cannot_widen_it():
    """`mask` composes with the region's scope rather than replacing it.

    A region is a subset; asking it a question with a mask of your own can only narrow it
    further. Replacing instead of composing was measured to answer for the whole system —
    497 atoms instead of the region's 248 — which is the wrong answer to a question asked
    of a region.
    """
    view = demo["1TCD"]
    view.make_regions_by("chain")
    regions = view.regions
    region = list(regions.values())[0] if hasattr(regions, "values") else regions[0]

    scoped = region.select(selection="all", element="atom", mask='atom_name=="CA"')
    everywhere = view.whole.select(selection='atom_name=="CA"', element="atom")

    assert len(scoped) < len(everywhere), (len(scoped), len(everywhere))
    assert set(scoped) <= set(region.atom_indices)


def test_a_regions_system_level_attributes_are_the_whole_systems():
    """Surprising, pre-existing, and worth pinning so it is a decision rather than a bug.

    `Region.get` scopes by element. A *system*-level attribute has no element to scope by,
    so it answers for the system the region lives in — `n_atoms` on a three-atom region is
    the system's 22, not 3.
    """
    view = demo["dialanine"]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag2", skip_digestion=True)

    assert region.get(n_atoms=True) == view.whole.get(n_atoms=True)
    assert len(region.get(element="atom", index=True)) == 3


def test_focus_selection_focus_region_and_region_focus_emit_zoom_messages():
    view = demo["dialanine"]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", skip_digestion=True)

    view.focus_selection(selection=[0, 1], duration_ms=0, extra_radius="2 angstroms", min_radius="1 angstrom")
    first_zoom = next(msg for msg in reversed(view._test_message_log) if msg.get("op") == "zoom")  # noqa: SLF001
    assert first_zoom["atom_indices"] == [0, 1]
    assert first_zoom["options"]["duration_ms"] == 0

    view.focus_region("frag", duration_ms=0)
    second_zoom = next(msg for msg in reversed(view._test_message_log) if msg.get("op") == "zoom")  # noqa: SLF001
    assert second_zoom["atom_indices"] == [0, 1, 2]

    region.focus(duration_ms=0)
    third_zoom = next(msg for msg in reversed(view._test_message_log) if msg.get("op") == "zoom")  # noqa: SLF001
    assert third_zoom["atom_indices"] == [0, 1, 2]

    view.whole.focus(selection=[3, 4], duration_ms=0)
    fourth_zoom = next(msg for msg in reversed(view._test_message_log) if msg.get("op") == "zoom")  # noqa: SLF001
    assert fourth_zoom["atom_indices"] == [3, 4]


def test_make_regions_by_creates_regions_with_deduplicated_tags():
    view = demo["dialanine"]

    chains = view.make_regions_by("chain", representation="line")
    molecules = view.make_regions_by("molecule")
    entities = view.make_regions_by("entity")
    chains_second = view.make_regions_by("chain")

    assert set(chains) == {"A"}
    assert chains["A"].representation == "line"
    assert chains["A"].atom_indices == tuple(range(22))

    assert set(molecules) == {"molecule_peptide_0"}
    assert molecules["molecule_peptide_0"].atom_indices == tuple(range(22))

    assert set(entities) == {"entity_peptide_0"}
    assert entities["entity_peptide_0"].atom_indices == tuple(range(22))

    assert set(chains_second) == {"A__2"}
    assert chains_second["A__2"].atom_indices == tuple(range(22))


def test_region_show_only_uses_ownership_without_mutating_user_visibility():
    view = demo["dialanine"]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", representation="line", skip_digestion=True)
    other = view.regions.add(atom_indices=[3, 4], tag="other", representation="line", skip_digestion=True)

    region.show_only()

    assert view.visible_atom_indices == list(range(22))
    assert region._hidden is False  # noqa: SLF001
    assert other._hidden is True  # noqa: SLF001
    assert view._test_message_log[-1] == {"op": "show_only_region", "tag": "frag"}  # noqa: SLF001


def test_tools_basic_extract_returns_subset_view():
    view = demo["dialanine"]

    result = tools.extract(view, selection=[0, 1, 2], debug_js=True)

    assert isinstance(result, MolSysView)
    assert result is not view
    assert msm.get(result._molsys, element="system", n_atoms=True, skip_digestion=True) == 3  # noqa: SLF001


def test_tools_basic_copy_returns_independent_view_with_scene_state():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.set_representation("cartoon", skip_digestion=True)
    view.whole.hide(skip_digestion=True)
    region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True)
    region.hide(skip_digestion=True)
    pocket = view.shapes.add_pocket_surface(atom_indices=[0, 1, 2], tag="pocket", skip_digestion=True)
    pocket.hide(skip_digestion=True)
    view.hide(selection=[2], skip_digestion=True)

    result = tools.copy(view, debug_js=True)

    assert isinstance(result, MolSysView)
    assert result is not view
    assert result._molsys is not view._molsys  # noqa: SLF001
    assert set(result.regions) == {"frag"}
    assert set(result.layers) == {"pocket"}
    assert result.regions["frag"].atom_indices == (0, 1, 2)
    assert result.regions["frag"]._hidden is True  # noqa: SLF001
    assert result.layers["pocket"]._hidden is True  # noqa: SLF001
    assert result._global_hidden is True  # noqa: SLF001


def test_tools_basic_merge_returns_new_view_from_multiple_views():
    view_a = demo["dialanine"]
    view_b = demo["dialanine"]

    result = tools.merge([view_a, view_b], debug_js=True)

    assert isinstance(result, MolSysView)
    assert result is not view_a
    assert result is not view_b
    assert msm.get(result._molsys, element="system", n_atoms=True, skip_digestion=True) == 44  # noqa: SLF001


def test_object_api_convert_delegates_to_current_molecular_system():
    view = demo["dialanine"]

    converted = view.whole.convert(to_form="molsysmt.MolSys")

    assert msm.get(converted, element="system", n_atoms=True, skip_digestion=True) == 22
    assert msm.get(converted, element="system", n_structures=True, skip_digestion=True) == 1
