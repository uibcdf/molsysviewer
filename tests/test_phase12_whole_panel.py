from __future__ import annotations

import molsysmt as msm

from molsysviewer import MolSysView
from molsysviewer.demo import demo
from molsysviewer.styles import STRUCTURAL_COLOR_SCHEMES


def _fresh_view():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.load(demo["dialanine"]._molsys.copy(), skip_digestion=True)  # noqa: SLF001
    view._ready = True  # noqa: SLF001
    return view


def _capture(view):
    sent: list[dict] = []
    view.widget.send = sent.append  # type: ignore[assignment]
    return sent


def test_whole_summary_carries_contract_fields_and_color_schemes():
    view = _fresh_view()
    record = view._whole_summary_record()  # noqa: SLF001

    assert record["representation"] is None
    assert record["preset"] is None
    assert isinstance(record["params"], dict)
    assert record["visible"] is True
    assert record["color_scheme"] is None
    assert isinstance(record["available_attributes"], list)
    assert record["color_schemes"] == sorted(STRUCTURAL_COLOR_SCHEMES)
    assert record["inheriting_region_count"] == 0
    assert record["none_state_region_count"] == 0
    assert record["covering_layer_count"] == 0


def test_whole_summary_counters_move_when_regions_change():
    view = _fresh_view()
    sent = _capture(view)

    view.regions.add(atom_indices=[0, 1], tag="base", skip_digestion=True)
    summary = [msg for msg in sent if msg.get("op") == "set_whole_summary"][-1]
    assert summary["none_state_region_count"] == 1
    assert summary["inheriting_region_count"] == 0

    view.regions["base"].set_representation("inherit", skip_digestion=True)
    summary = [msg for msg in sent if msg.get("op") == "set_whole_summary"][-1]
    assert summary["none_state_region_count"] == 0
    assert summary["inheriting_region_count"] == 1


def test_whole_details_payload_includes_composition_contains_and_frame_centroid():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.load(demo["pentalanine"]._molsys.copy(), skip_digestion=True)  # noqa: SLF001
    view._ready = True  # noqa: SLF001
    sent = _capture(view)

    view._handle_frontend_event(  # noqa: SLF001
        {"event": "interaction_context_action", "action": "get_whole_details", "request_id": 1}
    )
    view._current_structure_index = 1  # noqa: SLF001
    view._handle_frontend_event(  # noqa: SLF001
        {"event": "interaction_context_action", "action": "get_whole_details", "request_id": 2}
    )

    details = next(msg for msg in sent if msg.get("op") == "whole_details" and msg["request_id"] == 1)
    next_details = next(msg for msg in sent if msg.get("op") == "whole_details" and msg["request_id"] == 2)
    assert details["request_id"] == 1
    assert details["structure_index"] == 0
    assert next_details["structure_index"] == 1
    assert details["atom_count"] == int(view.molsys.get_n_atoms())

    # Every count is asserted against MolSysMT, not just `atoms`: a composition that
    # silently degrades to zeros must fail here.
    def _count(flag):
        return int(msm.get(view.molsys, element="system", output_type="values", **{flag: True}))

    assert details["composition"] == {
        "atoms": _count("n_atoms"),
        "groups": _count("n_groups"),
        "chains": _count("n_chains"),
        "molecules": _count("n_molecules"),
        "entities": _count("n_entities"),
    }
    assert details["composition"]["groups"] > 1

    # `contains` must carry real answers, not an empty dict: pentalanine is a peptide
    # and has no water. Asserting only `isinstance(..., dict)` lets a swallowed
    # exception ship as an empty panel.
    assert details["contains"]["peptide"] > 0
    assert details["contains"]["protein"] == 0
    assert details["contains"]["water"] == 0
    assert details["is_composed_of"]["peptide"] is True
    assert details["is_composed_of"]["water"] is False

    assert len(details["center_nm"]) == 3
    assert next_details["center_nm"] != details["center_nm"]


def test_whole_details_contains_detects_every_component_of_a_solvated_system():
    view = MolSysView()
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.load(demo["181L"]._molsys.copy(), skip_digestion=True)  # noqa: SLF001
    view._ready = True  # noqa: SLF001
    sent = _capture(view)

    view._handle_frontend_event(  # noqa: SLF001
        {"event": "interaction_context_action", "action": "get_whole_details", "request_id": 1}
    )

    contains = next(msg for msg in sent if msg.get("op") == "whole_details")["contains"]
    assert contains["protein"] > 0
    assert contains["water"] > 0
    assert contains["ion"] > 0
    assert contains["small_molecule"] > 0
    assert contains["lipid"] == 0


def test_reset_all_colors_is_undoable_for_whole_and_region_layers():
    view = _fresh_view()
    view.whole.set_color_by_values([1.0] * int(view.molsys.get_n_atoms()), skip_digestion=True)
    region = view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    region.set_color_by_values([1.0, 2.0], skip_digestion=True)
    assert view._atom_color_layers["whole"]  # noqa: SLF001
    assert view._atom_color_layers["A"]  # noqa: SLF001

    view.reset_all_colors(skip_digestion=True)
    assert view._atom_color_layers == {"whole": {}}  # noqa: SLF001

    assert view.history.undo()
    assert view._atom_color_layers["whole"]  # noqa: SLF001
    assert view._atom_color_layers["A"]  # noqa: SLF001


def test_one_synchronization_asks_the_system_for_its_attributes_once():
    """Both summaries need the same inventory, and traversing for it twice was 43%.

    `_sync_region_summaries_runtime` builds the region summaries and then the whole
    summary, and each used to call `_available_region_attributes()` for itself. The cost
    is not argument digestion -- every form-level predicate underneath already passes
    `skip_digestion=True` -- it is the traversal. Measured on `demo['dialanine']`:
    `regions.add` took 46.6 ms with two traversals and 26.8 ms with one
    (uibcdf/molsysviewer#32).

    The value is passed, not stored. A cache on the view or on the molecular system would
    have to know when the system changes underneath it, and a live edit that adds atoms
    changes exactly this answer; one synchronization is the longest it is provably still
    true. This guard therefore pins the reuse *within* a sync and says nothing about
    across syncs, which must keep re-asking.
    """
    view = _fresh_view()
    calls = {"n": 0}
    original = type(view)._available_region_attributes  # noqa: SLF001

    def counting(self):
        calls["n"] += 1
        return original(self)

    type(view)._available_region_attributes = counting  # noqa: SLF001
    try:
        view.regions.add(atom_indices=[0, 1], tag="one")
        during_first = calls["n"]
        calls["n"] = 0
        view._sync_region_summaries_runtime()  # noqa: SLF001
        during_sync = calls["n"]
    finally:
        type(view)._available_region_attributes = original  # noqa: SLF001

    assert during_sync == 1, (
        f"one synchronization asked the molecular system {during_sync} times for the same "
        "attribute inventory; both summaries must share one"
    )
    assert during_first >= 1, "the inventory was never built at all"
