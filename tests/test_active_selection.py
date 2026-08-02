import molsysmt as msm
import pytest

from molsysviewer import demo
from molsysviewer.active_selection import _combine
from molsysviewer.loaders.load_molsysmt import load_from_molsysmt


def _seed_group_selection(view, group_index=1):
    atom_indices = list(view.select(selection=f"group_index=={group_index}"))
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": atom_indices,
        "group_indices": [group_index],
        "component_indices": [],
        "chain_indices": [0],
        "molecule_indices": [],
        "entity_indices": [0],
        "count_atoms": len(atom_indices),
        "count_groups": 1,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001
    return atom_indices


def test_active_selection_exposes_current_payload_and_helpers():
    view = demo["dialanine"]
    atom_indices = _seed_group_selection(view, 1)

    assert view.active_selection.source_kind == "element"
    assert view.active_selection.element_level == "group"
    assert view.active_selection.target_level == "none"
    assert view.active_selection.atom_indices == atom_indices
    assert view.active_selection.group_indices == [1]
    assert view.active_selection.chain_indices == [0]
    assert view.active_selection.entity_indices == [0]
    assert view.active_selection.is_empty() is False
    assert view.active_selection.info()["atom_indices"] == atom_indices


def test_active_selection_clear_resets_python_state_and_emits_frontend_message():
    view = demo["dialanine"]
    _seed_group_selection(view, 1)

    view.active_selection.clear()

    assert view.active_selection.is_empty() is True
    assert view.get_last_active_selection_event()["source_kind"] == "empty"
    assert view._test_message_log[-1]["op"] == "clear_active_selection"  # noqa: SLF001


def test_active_selection_focus_new_region_and_add_label_delegate_to_reproducible_apis():
    view = demo["dialanine"]
    atom_indices = _seed_group_selection(view, 1)

    view.active_selection.focus(duration_ms=50)
    assert view._test_message_log[-1]["op"] == "zoom"  # noqa: SLF001
    assert view._test_message_log[-1]["atom_indices"] == atom_indices  # noqa: SLF001

    region = view.active_selection.new_region(tag="picked", representation="ball_and_stick")
    assert region.tag == "picked"
    assert "picked" in view.regions

    layer = view.active_selection.add_label("Selected", tag="picked-label")
    assert layer.tag == "picked-label"
    assert view.annotations.contains("picked-label") is True


def test_active_selection_set_selects_atoms_and_emits_frontend_message():
    view = demo["dialanine"]

    expected = sorted(int(i) for i in view.select(selection="group_index==1"))
    result = view.active_selection.set("group_index==1")

    assert result is view.active_selection
    assert sorted(view.active_selection.atom_indices) == expected
    assert view.active_selection.is_empty() is False
    assert view._test_message_log[-1]["op"] == "set_active_selection"  # noqa: SLF001


def test_active_selection_set_with_empty_match_clears():
    view = demo["dialanine"]
    view.active_selection.set("group_index==1")

    view.active_selection.set('atom_name=="ZZZ"')

    assert view.active_selection.is_empty() is True


def test_combine_selection_indices_preserves_order_and_supports_shared_ops():
    assert _combine([3, 1, 3], [1, 2, 2], "replace") == [1, 2]
    assert _combine([3, 1, 3], [1, 2, 2], "add") == [3, 1, 2]
    assert _combine([3, 1, 2, 4], [1, 4], "subtract") == [3, 2]
    assert _combine([3, 1, 2, 4], [1, 4, 9], "intersect") == [1, 4]
    assert _combine([3, 1], [], "invert", universe=[0, 1, 2, 3, 4]) == [0, 2, 4]


def test_combine_selection_indices_rejects_unknown_ops():
    with pytest.raises(ValueError, match="Unsupported selection combine operation"):
        _combine([1], [2], "xor")  # type: ignore[arg-type]


def test_context_action_apply_selection_query_combines_with_active_selection():
    view = demo["dialanine"]
    group_0 = list(view.select(selection="group_index==0"))
    group_1 = list(view.select(selection="group_index==1"))
    view.active_selection.set(group_0)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "apply_selection_query",
            "expression": "group_index==1",
            "syntax": "MolSysMT",
            "op": "add",
        }
    )

    assert sorted(view.active_selection.atom_indices) == sorted(group_0 + group_1)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "apply_selection_query",
            "expression": group_0,
            "syntax": "Indices",
            "op": "subtract",
        }
    )

    assert view.active_selection.atom_indices == group_1

    with pytest.raises(ValueError, match="Unsupported selection query operation"):
        view._apply_selection_query_action(  # noqa: SLF001
            {
                "expression": group_1,
                "syntax": "Indices",
                "op": "invert",
            }
        )
    assert view.active_selection.atom_indices == group_1


def test_active_selection_all_none_invert_operations_and_recipe():
    view = demo["dialanine"]
    group_0 = list(view.select(selection="group_index==0"))
    n_atoms = int(view._molsys.get_n_atoms())  # noqa: SLF001
    view.active_selection.set(group_0)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "set_active_selection_operation",
            "operation": "invert",
        }
    )

    assert view.active_selection.atom_indices == [
        atom_index for atom_index in range(n_atoms) if atom_index not in set(group_0)
    ]
    assert [step["op"] for step in view._active_selection_recipe] == ["replace", "invert"]  # noqa: SLF001

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "set_active_selection_operation",
            "operation": "none",
        }
    )
    assert view.active_selection.is_empty() is True
    assert view._active_selection_recipe == []  # noqa: SLF001

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "set_active_selection_operation",
            "operation": "invert",
        }
    )
    assert view.active_selection.atom_indices == list(range(n_atoms))
    assert view._active_selection_recipe[-1]["op"] == "invert"  # noqa: SLF001

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "set_active_selection_operation",
            "operation": "all",
        }
    )
    assert view.active_selection.atom_indices == list(range(n_atoms))
    assert [step["op"] for step in view._active_selection_recipe] == ["replace"]  # noqa: SLF001


def test_context_action_apply_selection_query_records_composable_recipe():
    view = demo["dialanine"]

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "apply_selection_query",
            "expression": "group_index==0",
            "syntax": "MolSysMT",
            "op": "replace",
        }
    )
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "apply_selection_query",
            "expression": "group_index==1",
            "syntax": "MolSysMT",
            "op": "add",
        }
    )

    recipe = view._active_selection_recipe  # noqa: SLF001
    assert [step["op"] for step in recipe] == ["replace", "add"]
    assert [step["expression"] for step in recipe] == ["group_index==0", "group_index==1"]
    view.active_selection.save("combined")
    record = view.selections.records()[0]
    assert record["recipe"] == recipe


def test_context_action_preview_selection_query_is_runtime_only():
    view = demo["dialanine"]
    before = len(view._test_message_log)  # noqa: SLF001
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = sent.append

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "selection_query_preview_request",
            "request_id": 7,
            "expression": "group_index==1",
            "syntax": "MolSysMT",
        }
    )

    assert len(view._test_message_log) == before  # noqa: SLF001
    assert sent[-1]["op"] == "selection_query_preview"
    assert sent[-1]["request_id"] == 7
    assert sent[-1]["ok"] is True
    assert sent[-1]["count"] == len(view.select(selection="group_index==1"))


def test_context_action_apply_selection_query_error_keeps_active_selection():
    view = demo["dialanine"]
    original = _seed_group_selection(view, 1)
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = sent.append

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "apply_selection_query",
            "expression": "not-an-index",
            "syntax": "Indices",
            "op": "replace",
        }
    )

    assert view.active_selection.atom_indices == original
    assert sent[-1]["op"] == "backend_error_occurred"
    assert sent[-1]["action"] == "apply_selection_query"
    assert sent[-1]["error_type"] == "ValueError"
    assert "integer atom indices" in sent[-1]["error_message"]


def test_context_action_preview_selection_query_error_is_inline_runtime_only():
    view = demo["dialanine"]
    before = len(view._test_message_log)  # noqa: SLF001
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = sent.append

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "selection_query_preview_request",
            "request_id": 8,
            "expression": "not-an-index",
            "syntax": "Indices",
        }
    )

    assert len(view._test_message_log) == before  # noqa: SLF001
    assert sent[-1]["op"] == "selection_query_preview"
    assert sent[-1]["request_id"] == 8
    assert sent[-1]["ok"] is False
    assert sent[-1]["error_type"] == "ValueError"
    assert "integer atom indices" in sent[-1]["error_message"]


def test_context_action_expand_selection_to_hierarchical_levels():
    view = demo["dialanine"]
    group_1 = list(view.select(selection="group_index==1"))
    view.active_selection.set(group_1[:2])

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "expand_selection",
            "level": "group",
        }
    )

    assert view.active_selection.atom_indices == group_1

    view.active_selection.set(group_1[:2])
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "expand_selection",
            "level": "chain",
        }
    )

    assert view.active_selection.atom_indices == list(range(int(view._molsys.get_n_atoms())))  # noqa: SLF001


def test_context_action_expand_selection_rejects_empty_or_unknown_level():
    view = demo["dialanine"]
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = sent.append

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "expand_selection",
            "level": "group",
        }
    )

    assert sent[-1]["op"] == "backend_error_occurred"
    assert "non-empty active selection" in sent[-1]["error_message"]

    view.active_selection.set([0])
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "expand_selection",
            "level": "residue",
        }
    )

    assert sent[-1]["op"] == "backend_error_occurred"
    assert "Unsupported selection expansion level" in sent[-1]["error_message"]


def test_context_action_spatial_expand_selection_matches_native_within():
    view = demo["dialanine"]
    view.active_selection.set([0, 1])
    expected = list(
        view.select(
            selection="all within 4 angstroms of atom_index in [0, 1]",
            syntax="MolSysMT",
            element="atom",
            skip_digestion=True,
        )
    )

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "expand_selection",
            "level": "spatial",
            "distance_angstroms": 4.0,
        }
    )

    assert view.active_selection.atom_indices == expected


def test_active_selection_set_fetches_correct_hierarchy_metadata():
    view = demo["dialanine"]
    view.active_selection.set([0, 1])

    expected = msm.get(
        view._molsys,  # noqa: SLF001
        element="atom",
        selection=[0, 1],
        output_type="dictionary",
        group_index=True,
        component_index=True,
        chain_index=True,
        molecule_index=True,
        entity_index=True,
        skip_digestion=True,
    )
    assert view.active_selection.group_indices == sorted(set(expected["group_index"]))
    assert view.active_selection.component_indices == sorted(set(expected["component_index"]))
    assert view.active_selection.chain_indices == sorted(set(expected["chain_index"]))
    assert view.active_selection.molecule_indices == sorted(set(expected["molecule_index"]))
    assert view.active_selection.entity_indices == sorted(set(expected["entity_index"]))


def test_context_action_expand_selection_uses_loaded_index_space_for_subset():
    original_view = demo["dialanine"]
    view = load_from_molsysmt(original_view.molecular_system, selection="group_index==1")
    assert view._atom_index_mapper is not None  # noqa: SLF001
    assert view._structure_index_mapper is None  # noqa: SLF001

    view.active_selection.set([0])
    assert view._test_message_log[-1]["op"] == "set_active_selection"  # noqa: SLF001
    assert view._test_message_log[-1]["atom_indices"] == [0]  # noqa: SLF001

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "expand_selection",
            "level": "group",
        }
    )

    assert view.active_selection.atom_indices == list(range(10))
    assert view._test_message_log[-1]["op"] == "set_active_selection"  # noqa: SLF001
    assert view._test_message_log[-1]["atom_indices"] == list(range(10))  # noqa: SLF001
