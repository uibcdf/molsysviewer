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


def test_object_api_contains_extract_and_is_composed_of():
    view = demo["dialanine"]

    assert view.contains(n_peptides=True) is True
    assert view.is_composed_of(n_molecules=1) is True

    subset = view.extract(selection=[0, 1, 2], debug_js=True)
    assert isinstance(subset, MolSysView)
    assert msm.get(subset._molsys, element="system", n_atoms=True, skip_digestion=True) == 3  # noqa: SLF001


def test_region_and_whole_contains_and_is_composed_of_use_scoped_semantics():
    view = demo["dialanine"]
    region = view.new_region(atom_indices=[0, 1, 2], tag="frag", skip_digestion=True)

    assert view.whole.contains(n_peptides=True) is True
    assert view.whole.is_composed_of(n_molecules=1) is True
    assert region.contains(selection=[0], n_atoms=True) is True
    assert region.is_composed_of(n_atoms=3) is True


def test_focus_selection_focus_region_and_region_focus_emit_zoom_messages():
    view = demo["dialanine"]
    region = view.new_region(atom_indices=[0, 1, 2], tag="frag", skip_digestion=True)

    view.focus_selection(selection=[0, 1], duration_ms=0, extra_radius="2 angstroms", min_radius="1 angstrom")
    first_zoom = next(msg for msg in reversed(view._message_history) if msg.get("op") == "zoom")  # noqa: SLF001
    assert first_zoom["atom_indices"] == [0, 1]
    assert first_zoom["options"]["duration_ms"] == 0

    view.focus_region("frag", duration_ms=0)
    second_zoom = next(msg for msg in reversed(view._message_history) if msg.get("op") == "zoom")  # noqa: SLF001
    assert second_zoom["atom_indices"] == [0, 1, 2]

    region.focus(duration_ms=0)
    third_zoom = next(msg for msg in reversed(view._message_history) if msg.get("op") == "zoom")  # noqa: SLF001
    assert third_zoom["atom_indices"] == [0, 1, 2]

    view.whole.focus(selection=[3, 4], duration_ms=0)
    fourth_zoom = next(msg for msg in reversed(view._message_history) if msg.get("op") == "zoom")  # noqa: SLF001
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
    region = view.new_region(atom_indices=[0, 1, 2], tag="frag", representation="line", skip_digestion=True)
    other = view.new_region(atom_indices=[3, 4], tag="other", representation="line", skip_digestion=True)

    region.show_only()

    assert view.visible_atom_indices == list(range(22))
    assert region._hidden is False  # noqa: SLF001
    assert other._hidden is True  # noqa: SLF001
    assert view._message_history[-1] == {"op": "show_only_region", "tag": "frag"}  # noqa: SLF001


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
    region = view.new_region(atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True)
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

    converted = view.convert(to_form="molsysmt.MolSys")

    assert msm.get(converted, element="system", n_atoms=True, skip_digestion=True) == 22
    assert msm.get(converted, element="system", n_structures=True, skip_digestion=True) == 1
