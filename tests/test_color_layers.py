from __future__ import annotations

from molsysviewer.demo import demo


def _constant_values(view):
    return [0.0] * int(view.molsys.get_n_atoms())


def test_region_color_layer_overrides_whole_only_on_region_atoms():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    n_atoms = int(view.molsys.get_n_atoms())

    view.whole.set_color_by_values(
        _constant_values(view),
        element="atom",
        palette=[0x111111, 0x111111],
        skip_digestion=True,
    )
    region = view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    region.set_color_by_values(
        [0.0, 0.0],
        element="atom",
        palette=[0x222222, 0x222222],
        replace=True,
        skip_digestion=True,
    )

    assert view._atom_color_layers["whole"][2] == 0x111111  # noqa: SLF001
    assert view._atom_color_layers["A"] == {0: 0x222222, 1: 0x222222}  # noqa: SLF001
    assert view._atom_color_map[0] == 0x222222  # noqa: SLF001
    assert view._atom_color_map[1] == 0x222222  # noqa: SLF001
    assert view._atom_color_map[2] == 0x111111  # noqa: SLF001
    assert set(view._atom_color_map) == set(range(n_atoms))  # noqa: SLF001


def test_region_reset_colors_reveals_whole_layer_underneath():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.set_color_by_values(
        _constant_values(view),
        element="atom",
        palette=[0x111111, 0x111111],
        skip_digestion=True,
    )
    region = view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    region.set_color_by_values([0.0, 0.0], element="atom", palette=[0x222222, 0x222222], skip_digestion=True)

    region.reset_colors(skip_digestion=True)

    assert view._atom_color_layers["A"] == {}  # noqa: SLF001
    assert view._atom_color_map[0] == 0x111111  # noqa: SLF001
    assert view._atom_color_map[1] == 0x111111  # noqa: SLF001
    assert view._message_history[-1] == {  # noqa: SLF001
        "op": "set_atom_colors",
        "atom_indices": [0, 1],
        "colors": [0x111111, 0x111111],
        "replace": False,
    }


def test_whole_reset_colors_preserves_region_layer_and_delete_reveals_beneath():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.set_color_by_values(
        _constant_values(view),
        element="atom",
        palette=[0x111111, 0x111111],
        skip_digestion=True,
    )
    region = view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    region.set_color_by_values([0.0, 0.0], element="atom", palette=[0x222222, 0x222222], skip_digestion=True)

    view.whole.reset_colors(skip_digestion=True)

    assert view._atom_color_layers["whole"] == {}  # noqa: SLF001
    assert view._atom_color_map == {0: 0x222222, 1: 0x222222}  # noqa: SLF001

    region.delete(skip_digestion=True)

    assert "A" not in view._atom_color_layers  # noqa: SLF001
    assert view._atom_color_map == {}  # noqa: SLF001
    assert view._message_history[-1] == {  # noqa: SLF001
        "op": "clear_atom_colors",
        "atom_indices": [0, 1],
    }


def test_overlapping_region_color_layers_follow_latest_order():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    a = view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    b = view.regions.add(atom_indices=[1, 2], tag="B", skip_digestion=True)

    a.set_color_by_values([0.0, 0.0], element="atom", palette=[0x111111, 0x111111], skip_digestion=True)
    b.set_color_by_values([0.0, 0.0], element="atom", palette=[0x222222, 0x222222], skip_digestion=True)
    assert view._atom_color_map[1] == 0x222222  # noqa: SLF001

    a.set_color_by_values([0.0, 0.0], element="atom", palette=[0x333333, 0x333333], replace=True, skip_digestion=True)
    assert a.order > b.order
    assert view._atom_color_map[1] == 0x333333  # noqa: SLF001


def test_region_raise_to_front_reorders_color_and_notifies_frontend():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    a = view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    b = view.regions.add(atom_indices=[1, 2], tag="B", skip_digestion=True)
    a.set_color_by_values([0.0, 0.0], element="atom", palette=[0x111111, 0x111111], skip_digestion=True)
    b.set_color_by_values([0.0, 0.0], element="atom", palette=[0x222222, 0x222222], skip_digestion=True)
    assert view._atom_color_map[1] == 0x222222  # noqa: SLF001

    a.raise_to_front(skip_digestion=True)

    assert a.order > b.order
    assert view._atom_color_map[1] == 0x111111  # noqa: SLF001
    assert view._message_history[-1] == {"op": "set_region_order", "tag": "A", "order": a.order}  # noqa: SLF001


def test_regions_manager_send_to_back_reorders_color_and_notifies_frontend():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    a = view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    b = view.regions.add(atom_indices=[1, 2], tag="B", skip_digestion=True)
    a.set_color_by_values([0.0, 0.0], element="atom", palette=[0x111111, 0x111111], skip_digestion=True)
    b.set_color_by_values([0.0, 0.0], element="atom", palette=[0x222222, 0x222222], skip_digestion=True)

    view.regions.send_to_back("B", skip_digestion=True)

    assert b.order < a.order
    assert view._atom_color_map[1] == 0x111111  # noqa: SLF001
    assert view._message_history[-1] == {"op": "set_region_order", "tag": "B", "order": b.order}  # noqa: SLF001


def test_region_rename_and_duplicate_preserve_color_layer_lifecycle():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    region = view.regions.add(atom_indices=[0, 1], tag="A", skip_digestion=True)
    region.set_color_by_values([0.0, 0.0], element="atom", palette=[0x111111, 0x111111], skip_digestion=True)

    region.rename("renamed", skip_digestion=True)
    duplicate = region.duplicate(tag="copy", skip_digestion=True)

    assert "A" not in view._atom_color_layers  # noqa: SLF001
    assert view._atom_color_layers["renamed"] == {0: 0x111111, 1: 0x111111}  # noqa: SLF001
    assert view._atom_color_layers["copy"] == {0: 0x111111, 1: 0x111111}  # noqa: SLF001
    assert duplicate.order > region.order
