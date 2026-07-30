"""R2 canonical popup snapshot projector — purity, invariance, isolation.

The projector must build the scene from live state only, so its output is
independent of interaction history. Mutation targets are called out per test.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from molsysviewer import MolSysView

MOLECULAR_OR_STRUCTURAL_OPS = {
    "load_molsys_payload",
    "load_molsys_array_payload",
    "set_atom_colors",
    "update_visibility",
    "create_region",
    "set_sections",
    "show_whole",
    "set_whole_representation",
    "set_trajectory_frame",
}


def _view_with_scene() -> MolSysView:
    v = MolSysView()
    # A minimal but non-trivial live scene.
    import molsysmt as msm

    v.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    v.regions.add("atom_index < 6", tag="a")
    v.active_selection.set([1, 2, 3])
    return v


def _normalize(messages: list[dict]) -> list[dict]:
    """Drop legitimately monotonic counters before comparing snapshots."""
    out = []
    for message in messages:
        message = deepcopy(message)
        if message.get("op") == "update_visibility":
            message.get("options", {}).pop("version", None)
        out.append(message)
    return out


# -- mode validation (mutation: accept an unknown mode) ----------------------

def test_mode_is_strictly_validated():
    v = _view_with_scene()
    assert isinstance(v.build_popup_scene_snapshot("canvas"), list)
    assert isinstance(v.build_popup_scene_snapshot("panel"), list)
    for bad in ("Canvas", "popup", "", None, "both"):
        with pytest.raises(ValueError):
            v.build_popup_scene_snapshot(bad)


# -- panel isolation (mutation: include molecular data in panel) -------------

def test_panel_snapshot_contains_no_molecular_or_structural_ops():
    v = _view_with_scene()
    ops = {m.get("op") for m in v.build_popup_scene_snapshot("panel")}
    assert not (ops & MOLECULAR_OR_STRUCTURAL_OPS)
    # It does carry UI summaries.
    assert "set_region_summaries" in ops


# -- purity: no history, no send, no state change ----------------------------

def test_projector_is_pure_with_respect_to_history_and_state():
    v = _view_with_scene()
    history_len = len(v._message_history)  # noqa: SLF001
    mol_before = deepcopy(v._current_molecular_projection)  # noqa: SLF001
    v.build_popup_scene_snapshot("canvas")
    v.build_popup_scene_snapshot("panel")
    assert len(v._message_history) == history_len  # noqa: SLF001  no checkpoints
    assert v._current_molecular_projection == mol_before  # noqa: SLF001  unchanged


# -- invariance (mutation: build from _message_history) ----------------------

def test_snapshot_is_byte_for_byte_identical_under_history_growth():
    v = _view_with_scene()
    before = v.build_popup_scene_snapshot("canvas")
    # Inflate the journal with thousands of unrelated ops.
    v._message_history.extend({"op": "noise", "n": i} for i in range(10_000))  # noqa: SLF001
    after = v.build_popup_scene_snapshot("canvas")
    assert before == after  # a history-derived projector would grow here


def test_size_depends_only_on_live_state_not_interaction_count():
    v = _view_with_scene()
    snap1 = v.build_popup_scene_snapshot("canvas")
    # Many redundant interactions that leave the same scene.
    for _ in range(40):
        v.active_selection.set([1, 2, 3])
        v.regions["a"].show(skip_digestion=True)
    snap2 = v.build_popup_scene_snapshot("canvas")
    assert len(snap1) == len(snap2)
    assert _normalize(snap1) == _normalize(snap2)


# -- defensive copies (mutation: return internal references) -----------------

def test_consumer_cannot_mutate_internal_state_through_the_result():
    v = _view_with_scene()
    snap = v.build_popup_scene_snapshot("canvas")

    molecular = next(m for m in snap if m["op"] == "load_molsys_payload")
    molecular["payload"] = "TAMPERED"
    region = next(m for m in snap if m["op"] == "create_region")
    assert region["atom_indices"]
    region["atom_indices"].append(999_999)

    # Internal state is untouched...
    assert v._current_molecular_projection["payload"] != "TAMPERED"  # noqa: SLF001
    # ...and the next snapshot is unaffected.
    snap2 = v.build_popup_scene_snapshot("canvas")
    molecular2 = next(m for m in snap2 if m["op"] == "load_molsys_payload")
    region2 = next(m for m in snap2 if m["op"] == "create_region")
    assert molecular2["payload"] != "TAMPERED"
    assert 999_999 not in (region2["atom_indices"] or [])


# -- dynamic/region fidelity (mutation: omit current indices) ----------------

def test_region_create_carries_current_materialized_indices():
    v = _view_with_scene()
    region = v.regions["a"]
    expected = list(region.atom_indices)
    assert expected  # non-empty
    snap = v.build_popup_scene_snapshot("canvas")
    create = next(m for m in snap if m["op"] == "create_region" and m.get("tag") == "a")
    # The current materialized indices (current frame for dynamic regions) must be
    # present; a projector that dropped them would fail here.
    assert create["atom_indices"] == expected
