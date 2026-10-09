"""Context operations preserve working selection unless selection is explicit."""

import pytest
from molsysviewer.demo import demo
from molsysviewer.viewer.panel_actions import dispatch_panel_action


def _target(view):
    atoms = list(view.whole.select("group_index==1"))
    return {"kind": "structure", "atom_indices": atoms, "atom_index": atoms[0]}


@pytest.mark.parametrize("operation", ["replace", "add", "subtract"])
@pytest.mark.parametrize("scope", ["atom", "group", "chain"])
def test_explicit_target_selection_uses_canonical_scope(operation, scope):
    view = demo["dialanine"]
    try:
        target = _target(view)
        current = [0, target["atom_index"]]
        view.active_selection.set(current)
        incoming = (
            [target["atom_index"]]
            if scope == "atom"
            else target["atom_indices"]
            if scope == "group"
            else list(view.whole.select("chain_index==0"))
        )
        expected = (
            incoming
            if operation == "replace"
            else sorted(set(current) | set(incoming))
            if operation == "add"
            else [atom for atom in current if atom not in incoming]
        )
        dispatch_panel_action(
            view,
            {
                "action": "select_context_target",
                "context": target,
                "op": operation,
                "scope": scope,
                "structure_index": 0,
            },
        )
        assert set(view.active_selection.atom_indices) == set(expected)
    finally:
        view.close()


def test_target_creation_preserves_selection_and_is_replayable():
    view = demo["dialanine"]
    try:
        target = _target(view)
        view.active_selection.set([0, 1])
        dispatch_panel_action(
            view, {"action": "create_region_from_target", "context": target, "scope": "group", "tag": "pointed-residue"}
        )
        assert view.active_selection.atom_indices == [0, 1]
        assert list(view.regions.get("pointed-residue").atom_indices) == target["atom_indices"]
        dispatch_panel_action(
            view,
            {"action": "create_annotation_from_target", "context": target, "scope": "atom", "text": "Pointed atom"},
        )
        assert view.active_selection.atom_indices == [0, 1]
        annotation = view.annotations.info()[-1]
        assert annotation["atom_indices"] == [target["atom_index"]]
        assert annotation["text"] == "Pointed atom"
        assert view.annotations.records()[-1]["options"]["atom_indices"] == [target["atom_index"]]
    finally:
        view.close()


@pytest.mark.parametrize(
    "action", ["select_context_target", "create_region_from_target", "create_annotation_from_target"]
)
def test_missing_group_membership_refuses_without_mutating_scene(action):
    view = demo["dialanine"]
    try:
        target = _target(view)
        view.active_selection.set([0, 1])
        # A real native topology can declare atoms without group membership,
        # as happens with partially specified molecular sources.
        view.molsys.topology.atoms["group_index"] = None
        regions_before = view.regions.records()
        annotations_before = view.annotations.records()
        with pytest.raises(ValueError, match="no declared group membership"):
            dispatch_panel_action(
                view,
                {
                    "action": action,
                    "context": target,
                    "scope": "group",
                    "op": "replace",
                    "tag": "missing-group",
                    "text": "Missing group",
                },
            )
        assert view.active_selection.atom_indices == [0, 1]
        assert view.regions.records() == regions_before
        assert view.annotations.records() == annotations_before
    finally:
        view.close()


@pytest.mark.parametrize(
    "change",
    [
        {"scope": "nonsense"},
        {"structure_index": 1},
        {"context": {"kind": "structure", "atom_indices": [-1]}},
        {"context": {"kind": "structure", "atom_indices": [True]}},
        {"context": {"kind": "structure", "atom_indices": [999999]}},
        {"context": {"kind": "interaction", "atom_indices": [0, 1]}},
        {"scope": "atom", "context": {"kind": "structure", "atom_indices": [0, 1]}},
        {"op": "nonsense"},
    ],
)
def test_invalid_or_stale_target_refuses_before_mutation(change):
    view = demo["dialanine"]
    try:
        view.active_selection.set([0])
        content = {"action": "select_context_target", "context": _target(view), "scope": "target", **change}
        with pytest.raises(ValueError):
            dispatch_panel_action(view, content)
        assert view.active_selection.atom_indices == [0]
    finally:
        view.close()
