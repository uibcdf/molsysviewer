from __future__ import annotations

from importlib.resources import files
import warnings

import pytest

import molsysmt as msm  # noqa: F401
import molsysviewer as viewer
import pyunitwizard as puw
from molsysviewer import demo
from molsysviewer.loaders.load_molsysmt import load_from_molsysmt


def test_demo_region_hide():
    """Smoke-test: create a region and hide it without errors."""

    demo_system = files("molsysviewer.data.h5msm").joinpath("1TCD.h5msm")
    view = viewer.new_view(demo_system, debug_js=True)
    # Avoid real frontend traffic; we only need the calls to not fail.
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.show()
    region = view.regions.add("chain_id == 'A'", representation="sticks")
    region.hide()

    assert region is not None
    assert region.tag in view.regions


def test_region_scoped_indices_bond():
    """Region._scoped_indices_for_element('bond') returns non-empty sorted int list."""
    view = demo["dialanine"]
    region = view.regions.add(selection="group_index == 0", tag="bond-scope-test")

    bond_indices = region._scoped_indices_for_element("bond")

    assert isinstance(bond_indices, list)
    assert len(bond_indices) > 0
    assert all(isinstance(i, int) for i in bond_indices)
    assert bond_indices == sorted(set(bond_indices))


def test_region_scoped_indices_bond_subset():
    """Bond scoping on a single-atom region returns only the bonds of that atom."""
    view = demo["dialanine"]
    region = view.regions.add(selection="atom_index == 1", tag="bond-scope-single")

    bond_indices = region._scoped_indices_for_element("bond")

    assert isinstance(bond_indices, list)
    assert len(bond_indices) > 0



def _empty_view():
    view = viewer.MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def test_region_boolean_composition_from_atom_indices():
    view = _empty_view()
    left = view.regions.add(atom_indices=[0, 1, 2], tag="left", skip_digestion=True)
    right = view.regions.add(atom_indices=[2, 3], tag="right", skip_digestion=True)

    difference = left.difference(right, tag="left-minus-right")
    intersection = left & right
    union = left.union(right, tag="left-or-right")

    assert difference.atom_indices == (0, 1)
    assert intersection.atom_indices == (2,)
    assert union.atom_indices == (0, 1, 2, 3)
    assert "left_and_right" in view.regions
    assert any(
        msg.get("op") == "create_region"
        and msg.get("tag") == "left-minus-right"
        and msg.get("atom_indices") == [0, 1]
        for msg in view._message_history  # noqa: SLF001
    )


def test_region_boolean_composition_rejects_empty_result():
    view = _empty_view()
    left = view.regions.add(atom_indices=[0, 1], tag="left", skip_digestion=True)
    right = view.regions.add(atom_indices=[2, 3], tag="right", skip_digestion=True)

    with pytest.raises(ValueError, match="empty region"):
        left.intersection(right)


def test_region_overlap_warning_when_visualizing_overlap():
    view = _empty_view()
    view.regions.add(atom_indices=[0, 1, 2], tag="first", representation="line", skip_digestion=True)
    second = view.regions.add(atom_indices=[2, 3], tag="second", skip_digestion=True)

    with pytest.warns(UserWarning, match="overlaps visible represented region"):
        second.set_representation("ball-and-stick", skip_digestion=True)


def test_region_overlap_warning_when_creating_visual_overlap():
    view = _empty_view()
    view.regions.add(atom_indices=[0, 1, 2], tag="first", representation="line", skip_digestion=True)

    with pytest.warns(UserWarning, match="overlaps visible represented region"):
        view.regions.add(atom_indices=[2, 3], tag="second", representation="ball-and-stick", skip_digestion=True)


def test_region_inherit_counts_as_visible_visual_overlap():
    view = _empty_view()
    view.regions.add(atom_indices=[0, 1, 2], tag="first", representation="inherit", skip_digestion=True)

    with pytest.warns(UserWarning, match="overlaps visible represented region"):
        view.regions.add(atom_indices=[2, 3], tag="second", representation="line", skip_digestion=True)


def test_region_overlap_warning_ignores_logical_and_hidden_regions():
    view = _empty_view()
    view.regions.add(atom_indices=[0, 1], tag="logical", skip_digestion=True)
    hidden = view.regions.add(atom_indices=[1, 2], tag="hidden", representation="line", skip_digestion=True)
    hidden.hide(skip_digestion=True)

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        view.regions.add(atom_indices=[1, 2, 3], tag="visible", representation="line", skip_digestion=True)

    assert record == []


def test_region_reset_representation_removes_own_visual_state():
    view = _empty_view()
    region = view.regions.add(
        atom_indices=[0, 1, 2],
        tag="styled",
        representation="line",
        alpha=0.4,
        skip_digestion=True,
    )

    region.reset_representation(skip_digestion=True)

    assert region.representation is None
    assert region.preset is None
    assert region.repr_params == {}
    assert view._message_history[-1] == {  # noqa: SLF001
        "op": "set_region_representation",
        "tag": "styled",
        "order": region.order,
        "representation": None,
        "preset": None,
        "user_preset": None,
        "params": {},
    }


def test_none_region_hide_and_show_warn_without_frontend_visibility_message():
    view = _empty_view()
    region = view.regions.add(atom_indices=[0, 1, 2], tag="logical", skip_digestion=True)
    before = len(view._message_history)  # noqa: SLF001

    with pytest.warns(UserWarning, match="no own representation to hide"):
        region.hide(skip_digestion=True)
    with pytest.warns(UserWarning, match="no own representation to show"):
        region.show(skip_digestion=True)

    assert len(view._message_history) == before  # noqa: SLF001
    assert region._hidden is False  # noqa: SLF001


def test_new_region_with_visual_spec_preserves_representation_semantics():
    view = _empty_view()
    view.regions.add(
        atom_indices=[0, 1, 2],
        tag="one-build",
        representation="line",
        color="red",
        alpha=0.4,
        skip_digestion=True,
    )

    operations = [
        message
        for message in view._message_history  # noqa: SLF001
        if message.get("tag") == "one-build"
        and message.get("op") in {"create_region", "set_region_representation"}
    ]
    assert operations[0] == {
        "op": "create_region",
        "tag": "one-build",
        "selection": "all",
        "atom_indices": [0, 1, 2],
        "order": 1,
    }
    assert operations[1]["op"] == "set_region_representation"
    assert operations[1]["tag"] == "one-build"
    assert operations[1]["order"] == 2
    assert operations[1]["representation"] == "line"
    assert operations[1]["preset"] is None
    assert operations[1]["user_preset"] is None
    assert operations[1]["params"] == {
        "alpha": 0.4,
        "molstar_color_theme": {
            "name": "uniform",
            "params": {"value": 16711680},
        },
    }


def test_new_region_with_visual_params_preserves_none_representation():
    view = _empty_view()
    region = view.regions.add(
        atom_indices=[0, 1, 2],
        tag="styled-default",
        alpha=0.4,
        skip_digestion=True,
    )

    assert region.representation is None
    assert region.repr_params == {}
    operations = [
        message
        for message in view._message_history  # noqa: SLF001
        if message.get("tag") == "styled-default"
        and message.get("op") in {"create_region", "set_region_representation"}
    ]
    assert operations == [
        {
            "op": "create_region",
            "tag": "styled-default",
            "selection": "all",
            "atom_indices": [0, 1, 2],
            "order": region.order,
        }
    ]


def test_rebuild_replays_visual_region_as_bare_create_then_style():
    view = _empty_view()
    view.regions.add(
        atom_indices=[0, 1, 2],
        tag="rebuild-region",
        representation="line",
        alpha=0.4,
        skip_digestion=True,
    )
    view._message_history.clear()  # noqa: SLF001

    for region in list(view._regions.values()):  # noqa: SLF001
        if not getattr(region, "_active", True):
            continue
        if getattr(region, "preset", None) is not None or region.representation is not None or region.repr_params:
            region._send_create(include_visual=False)  # noqa: SLF001
            region.set_representation(
                region.representation,
                preset=getattr(region, "preset", None),
                skip_digestion=True,
                **(region.repr_params or {}),
            )
        else:
            region._send_create()  # noqa: SLF001

    operations = [
        message
        for message in view._message_history  # noqa: SLF001
        if message.get("tag") == "rebuild-region"
        and message.get("op") in {"create_region", "set_region_representation"}
    ]
    assert operations[0] == {
        "op": "create_region",
        "tag": "rebuild-region",
        "selection": "all",
        "atom_indices": [0, 1, 2],
        "order": 2,
    }
    assert operations[1]["op"] == "set_region_representation"
    assert operations[1]["order"] == 3
    assert operations[1]["representation"] == "line"


def test_region_duplicate_preserves_atoms_and_visual_specification():
    view = _empty_view()
    region = view.regions.add(
        atom_indices=[0, 1, 2],
        tag="source",
        representation="line",
        alpha=0.6,
        quality="medium",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    duplicate = region.duplicate(tag="source-copy", skip_digestion=True)

    assert duplicate.atom_indices == region.atom_indices
    assert duplicate.selection == region.selection
    assert duplicate.representation == "line"
    assert duplicate.preset is None
    assert duplicate.repr_params == {"alpha": 0.6, "quality": "medium"}
    assert view.regions["source-copy"] is duplicate


def test_region_and_manager_overlap_queries_use_visible_visual_regions():
    view = _empty_view()
    first = view.regions.add(
        atom_indices=[0, 1, 2],
        tag="first",
        representation="line",
        skip_digestion=True,
    )
    second = view.regions.add(
        atom_indices=[2, 3],
        tag="second",
        skip_digestion=True,
    )
    with pytest.warns(UserWarning, match="overlaps visible represented region"):
        second.set_representation("ball-and-stick", skip_digestion=True)

    assert first.overlaps(skip_digestion=True) == ["second"]
    assert second.overlaps(skip_digestion=True) == ["first"]
    assert view.regions.overlaps(skip_digestion=True) == {
        "first": ["second"],
        "second": ["first"],
    }

    second.hide(skip_digestion=True)
    assert first.overlaps(skip_digestion=True) == []


def test_regions_manager_show_all_and_hide_all_update_every_region():
    view = _empty_view()
    first = view.regions.add(atom_indices=[0], tag="first", skip_digestion=True)
    second = view.regions.add(atom_indices=[1], tag="second", skip_digestion=True)

    view.regions.hide_all(skip_digestion=True)
    assert first._hidden is True  # noqa: SLF001
    assert second._hidden is True  # noqa: SLF001
    assert view._message_history[-1] == {  # noqa: SLF001
        "op": "set_regions_visibility",
        "tags": ["first", "second"],
        "hidden": True,
    }

    view.regions.show_all(skip_digestion=True)
    assert first._hidden is False  # noqa: SLF001
    assert second._hidden is False  # noqa: SLF001
    assert view._message_history[-1] == {  # noqa: SLF001
        "op": "set_regions_visibility",
        "tags": ["first", "second"],
        "hidden": False,
    }


def test_region_set_color_by_real_b_factor_attribute():
    view = demo["dialanine"]
    n_atoms = int(view._molsys.get_n_atoms())  # noqa: SLF001
    b_factors = puw.quantity([float(index) for index in range(n_atoms)], "nm**2")
    msm.set(
        view._molsys,  # noqa: SLF001
        element="atom",
        b_factor=b_factors,
        skip_digestion=True,
    )
    region = view.regions.add(atom_indices=[0, 1, 2], tag="bfactor", skip_digestion=True)

    region.set_color_by_attribute("bfactor", palette="viridis", skip_digestion=True)

    message = view._message_history[-1]  # noqa: SLF001
    assert message["op"] == "set_atom_colors"
    assert message["atom_indices"] == [0, 1, 2]
    assert len(message["colors"]) == 3


def test_region_set_color_by_attribute_rejects_missing_attribute():
    view = demo["dialanine"]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="missing", skip_digestion=True)

    with pytest.raises(ValueError, match="not available"):
        region.set_color_by_attribute("b_factor", skip_digestion=True)


def test_region_frontend_actions_route_through_public_api():
    view = demo["dialanine"]
    group_0 = list(view.select(selection="group_index==0"))
    group_1 = list(view.select(selection="group_index==1"))
    view.regions.add(atom_indices=group_0, tag="left", skip_digestion=True)
    view.regions.add(atom_indices=group_1, tag="right", skip_digestion=True)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "compose_regions",
            "tag_a": "left",
            "tag_b": "right",
            "op": "union",
            "new_tag": "combined",
        }
    )
    assert view.regions["combined"].atom_indices == tuple(group_0 + group_1)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "create_complementary_region",
            "tag": "left",
        }
    )
    assert "Global-left" in view.regions

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "duplicate_region",
            "tag": "right",
            "new_tag": "right-copy",
        }
    )
    assert view.regions["right-copy"].atom_indices == tuple(group_1)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "hide_all_regions",
        }
    )
    assert view._message_history[-1]["op"] == "set_regions_visibility"  # noqa: SLF001
    assert all(region._hidden for region in view.regions.values())  # noqa: SLF001


def test_compose_regions_handler_supports_all_ordered_operations():
    view = demo["dialanine"]
    view.regions.add(atom_indices=[0, 1, 2], tag="left", skip_digestion=True)
    view.regions.add(atom_indices=[2, 3], tag="right", skip_digestion=True)
    expected = {
        "union": (0, 1, 2, 3),
        "intersection": (2,),
        "difference": (0, 1),
    }

    for operation, atom_indices in expected.items():
        output_tag = f"result-{operation}"
        view._handle_frontend_event(  # noqa: SLF001
            {
                "event": "interaction_context_action",
                "action": "compose_regions",
                "tag_a": "left",
                "tag_b": "right",
                "op": operation,
                "new_tag": output_tag,
            }
        )
        assert view.regions[output_tag].atom_indices == atom_indices

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "compose_regions",
            "tag_a": "left",
            "tag_b": "right",
            "op": "difference",
            "new_tag": "right",
            "overwrite": True,
        }
    )
    assert view.regions["right"].atom_indices == (0, 1)
    assert not any(tag.startswith("right__compose") for tag in view.regions)


def test_create_region_from_query_split_and_lazy_details_actions():
    view = demo["dialanine"]
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = sent.append

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "create_region_from_query",
            "expression": "group_index==0",
            "syntax": "MolSysMT",
            "tag": "query-region",
            "representation": "line",
        }
    )
    assert view.regions["query-region"].selection == "group_index==0"

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "make_regions_by",
            "element": "chain",
        }
    )
    assert len(view.regions) > 1

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "get_region_details",
            "tag": "query-region",
            "request_id": 7,
        }
    )
    details = sent[-1]
    assert details["op"] == "region_details"
    assert details["request_id"] == 7
    assert details["tag"] == "query-region"
    assert details["atom_count"] > 0
    assert details["group_count"] == 1
    assert details["chain_count"] == 1
    assert len(details["center_nm"]) == 3
    assert details["structure_index"] == view.current_structure_index


def test_create_region_from_active_selection_action_applies_initial_representation():
    view = demo["dialanine"]
    view._last_active_selection_event = {"atom_indices": [0, 1]}  # noqa: SLF001

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "create_region_from_selection",
            "tag": "active-region",
            "representation": "line",
        }
    )

    region = view.regions["active-region"]
    assert region.atom_indices == (0, 1)
    assert region.representation == "line"


def test_region_details_center_uses_current_trajectory_frame():
    view = demo["pentalanine"]
    region = view.regions.add(atom_indices=[0, 1, 2], tag="moving", skip_digestion=True)
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = sent.append
    view.set_structure(1, skip_digestion=True)
    expected = puw.get_value(
        region.get_center(structure_indices=[1], skip_digestion=True),
        to_unit="nm",
    ).tolist()

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "get_region_details",
            "tag": "moving",
            "request_id": 11,
        }
    )

    details = sent[-1]
    assert details["structure_index"] == 1
    assert details["center_nm"] == pytest.approx(expected)


def test_new_region_rejects_duplicate_tag():
    view = _empty_view()
    view.regions.add(atom_indices=[0], tag="same", skip_digestion=True)

    with pytest.raises(ValueError, match="already exists"):
        view.regions.add(atom_indices=[1], tag="same", skip_digestion=True)


def test_region_summary_fields_filter_transients_and_gate_attributes():
    view = demo["dialanine"]
    n_atoms = int(view._molsys.get_n_atoms())  # noqa: SLF001
    msm.set(
        view._molsys,  # noqa: SLF001
        element="atom",
        b_factor=puw.quantity([float(index) for index in range(n_atoms)], "nm**2"),
        skip_digestion=True,
    )
    first = view.regions.add(
        atom_indices=[0, 1, 2],
        tag="first",
        representation="line",
        skip_digestion=True,
    )
    with pytest.warns(UserWarning, match="overlaps visible represented region"):
        view.regions.add(
            atom_indices=[2, 3],
            tag="second",
            representation="ball-and-stick",
            skip_digestion=True,
        )
    with pytest.warns(UserWarning, match="overlaps visible represented region"):
        view.styles.focus(
            representation="line",
            atom_indices=[0],
            skip_digestion=True,
        )
    view.show_orientation_axes(atom_indices=[0, 1], skip_digestion=True)
    view.show_best_fit_plane(atom_indices=[0, 1, 2], skip_digestion=True)

    records = view._region_summary_records()  # noqa: SLF001
    by_tag = {record["tag"]: record for record in records}

    assert sorted(by_tag) == ["first", "second"]
    assert by_tag["first"]["representation"] == "line"
    assert by_tag["first"]["preset"] is None
    assert by_tag["first"]["representation_params"] == {}
    assert by_tag["first"]["overlap_tags"] == ["second"]
    assert by_tag["first"]["available_attributes"] == ["b_factor"]
    assert by_tag["first"]["atom_indices"] == list(first.atom_indices)


def test_set_region_representation_action_supports_preset_and_params():
    view = demo["dialanine"]
    view.regions.add(atom_indices=[0, 1], tag="styled", skip_digestion=True)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "set_region_representation",
            "tag": "styled",
            "preset": "polymer-cartoon",
            "params": {"alpha": 0.6, "quality": "high"},
        }
    )

    region = view.regions["styled"]
    assert region.representation is None
    assert region.preset == "polymer-cartoon"
    assert region.repr_params == {"alpha": 0.6, "quality": "high"}


def test_make_regions_by_batches_operations_and_supports_api_only_levels():
    view = demo["dialanine"]
    before = len(view._message_history)  # noqa: SLF001

    groups = view.make_regions_by("group", representation="line", skip_digestion=True)

    assert len(groups) >= 2
    messages = view._message_history[before:]  # noqa: SLF001
    assert len(messages) == 1
    assert messages[0]["op"] == "batch_region_operations"
    operations = messages[0]["operations"]
    assert [operation["op"] for operation in operations].count("create_region") == len(groups)
    assert [operation["op"] for operation in operations].count("set_region_representation") == len(groups)

    components = view.make_regions_by("component", skip_digestion=True)
    assert len(components) >= 1
    assert view._message_history[-1]["op"] == "batch_region_operations"  # noqa: SLF001


def test_region_operations_stay_in_loaded_subset_index_space():
    source = demo["dialanine"]
    view = load_from_molsysmt(source.molecular_system, selection="group_index==1")
    n_atoms = int(view._molsys.get_n_atoms())  # noqa: SLF001
    assert view._atom_index_mapper is not None  # noqa: SLF001

    region = view.regions.add(
        atom_indices=[0, 1],
        tag="local",
        representation="line",
        skip_digestion=True,
    )
    complement = region.new_complementary_region(skip_digestion=True)
    split = view.make_regions_by("group", skip_digestion=True)

    assert region.atom_indices == (0, 1)
    assert complement.atom_indices == tuple(range(2, n_atoms))
    assert sorted(index for item in split.values() for index in item.atom_indices or ()) == list(range(n_atoms))
    create_operations = [
        operation
        for operation in view._message_history[-1]["operations"]  # noqa: SLF001
        if operation["op"] == "create_region"
    ]
    assert sorted(index for operation in create_operations for index in operation["atom_indices"]) == list(range(n_atoms))


def test_state_none_drops_representation_params(): 
    """Contract A: state None owns no visual, so params have nothing to apply to.

    Retaining them would make `repr_params` advertise styling the region does not
    have, and would serialise a phantom parameter into the state file.
    """
    view = viewer.MolSysView()
    view.widget.send = lambda _msg: None
    view.load(demo["dialanine"]._molsys.copy(), skip_digestion=True)
    view._ready = True

    region = view.regions.add(atom_indices=[0, 1], tag="r", representation="line", alpha=0.3, skip_digestion=True)
    assert region.repr_params == {"alpha": 0.3}

    # Dropping to state None must drop the params with the visual they styled.
    region.set_representation(None, alpha=0.3, skip_digestion=True)
    assert region.representation is None
    assert region.preset is None
    assert region.repr_params == {}

    # A region that owns a visual keeps them, including via the "inherit" sentinel.
    region.set_representation("inherit", alpha=0.6, skip_digestion=True)
    assert region.repr_params == {"alpha": 0.6}
