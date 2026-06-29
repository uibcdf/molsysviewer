from __future__ import annotations

import pytest

pytest.importorskip("molsysmt")

from molsysviewer.demo import demo


def test_whole_hide_stays_sticky_across_show_all():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.hide(skip_digestion=True)
    view.show(skip_digestion=True)

    assert view._global_hidden is True  # noqa: SLF001
    assert view.visible_atom_indices == list(range(22))
    assert [msg.get("op") for msg in view._message_history[-3:]] == [
        "update_visibility",
        "show_global",
        "hide_global",
    ]
    assert view._message_history[-1] == {"op": "hide_global", "target": "global"}  # noqa: SLF001


def test_hidden_region_and_layer_survive_global_hide_show_cycle():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    pocket_layer = view.shapes.add_pocket_surface(
        atom_indices=[0, 1, 2],
        tag="pocket",
        skip_digestion=True,
    )
    pocket_layer.hide(skip_digestion=True)

    view.hide(skip_digestion=True)
    view.show(skip_digestion=True)

    assert view.regions["frag"]._hidden is True  # noqa: SLF001
    assert view.layers["pocket"]._hidden is True  # noqa: SLF001
    assert view.visible_atom_indices == list(range(22))
    assert not any(msg.get("op") == "show_region" and msg.get("tag") == "frag" for msg in view._message_history)
    assert not any(msg.get("op") == "show_layer" and msg.get("tag") == "pocket" for msg in view._message_history)
    assert [msg.get("op") for msg in view._message_history[-3:]] == [
        "update_visibility",
        "show_global",
        "show_global",
    ]
    assert view._message_history[-1] == {"op": "show_global", "target": "global"}  # noqa: SLF001


def test_show_all_resets_partial_atom_visibility_without_clearing_hidden_region_state():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.new_region(
        atom_indices=[0, 1, 2],
        tag="frag",
        representation="sticks",
        skip_digestion=True,
    )
    region.hide(skip_digestion=True)

    view.hide(selection=[5], skip_digestion=True)
    assert bool(view.atom_mask[5]) is False

    view.show(skip_digestion=True)

    assert bool(view.atom_mask[5]) is True
    assert view.regions["frag"]._hidden is True  # noqa: SLF001
    assert not any(msg.get("op") == "show_region" and msg.get("tag") == "frag" for msg in view._message_history)
    visibility_msg = next(msg for msg in reversed(view._message_history) if msg.get("op") == "update_visibility")
    assert visibility_msg["options"]["visible_atom_indices"] == list(range(22))

@pytest.mark.parametrize(
    "operation",
    [
        lambda view: view.hide(selection="all", structure_indices=[0], skip_digestion=True),
        lambda view: view.show(selection="all", structure_indices=[0], skip_digestion=True),
        lambda view: view.isolate(selection="all", structure_indices=[0], skip_digestion=True),
        lambda view: view.focus_with_fade(selection="all", structure_indices=[0], skip_digestion=True),
    ],
)
def test_visibility_rejects_per_structure_visibility_until_supported(operation):
    view = demo["chicken_villin_HP35"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    mask_before = None if view.atom_mask is None else view.atom_mask.copy()
    history_len = len(view._message_history)  # noqa: SLF001

    with pytest.raises(NotImplementedError, match="Per-structure visibility is not supported"):
        operation(view)

    assert len(view._message_history) == history_len  # noqa: SLF001
    if mask_before is not None:
        assert view.atom_mask is not None
        assert view.atom_mask.tolist() == mask_before.tolist()
