from __future__ import annotations

import numpy as np

from molsysviewer.demo import demo
from molsysviewer._pyunitwizard import puw


def test_whole_representation_properties_and_visibility_are_orthogonal():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.hide(skip_digestion=True)
    view.whole.set_representation("cartoon", color="red", skip_digestion=True)

    assert view.whole.visible is False
    assert view.whole.representation == "cartoon"
    assert view.whole.preset is None
    assert view.whole.params == {
        "molstar_color_theme": {"name": "uniform", "params": {"value": 0xFF0000}}
    }


def test_whole_reset_representation_returns_to_load_time_explicit_style():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.set_color_scheme("chain_default", skip_digestion=True)
    view.whole.set_representation("spacefill", skip_digestion=True)
    view.whole.reset_representation(skip_digestion=True)

    assert view.whole.representation is None
    assert view.whole.preset is None
    assert view.whole.params == {}
    assert view.whole.color_scheme is None
    message = view._test_message_log[-1]  # noqa: SLF001
    assert message["op"] == "set_whole_representation"
    assert message["representation"] is None
    assert message["preset"] is None
    assert message["params"] == {}


def test_whole_set_color_by_values_can_merge_with_existing_map():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    n_atoms = int(view.molsys.get_n_atoms())

    view.whole.set_color_by_values(
        list(range(n_atoms)),
        element="atom",
        palette=[0x111111, 0xEEEEEE],
        replace=True,
        skip_digestion=True,
    )
    view.whole.set_color_by_values(
        list(range(n_atoms)),
        element="atom",
        palette=[0x222222, 0xDDDDDD],
        replace=False,
        skip_digestion=True,
    )

    assert set(view._atom_color_map) == set(range(n_atoms))  # noqa: SLF001
    assert set(view._atom_color_layers["whole"]) == set(range(n_atoms))  # noqa: SLF001
    assert view._test_message_log[-1]["replace"] is False  # noqa: SLF001


def test_whole_set_color_by_attribute_uses_real_molsysmt_attributes():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view.whole.set_color_by_attribute(
        "atom_index",
        element="atom",
        palette=[0x111111, 0xEEEEEE],
        structure_indices=[view.current_structure_index],
        skip_digestion=True,
    )

    n_atoms = int(view.molsys.get_n_atoms())
    assert set(view._atom_color_map) == set(range(n_atoms))  # noqa: SLF001
    assert view._test_message_log[-1]["op"] == "set_atom_colors"  # noqa: SLF001
    assert view._test_message_log[-1]["replace"] is False  # noqa: SLF001


def test_whole_get_center_returns_centroid_quantity():
    view = demo["dialanine"]

    center = view.whole.get_center(structure_indices=[view.current_structure_index], skip_digestion=True)

    values = puw.get_value(center, to_unit="nm")
    assert np.asarray(values).shape == (3,)


def test_reset_all_colors_clears_canvas_color_map():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    n_atoms = int(view.molsys.get_n_atoms())

    view.whole.set_color_by_values(
        list(range(n_atoms)),
        element="atom",
        palette=[0x111111, 0xEEEEEE],
        skip_digestion=True,
    )
    assert view._atom_color_map  # noqa: SLF001

    view.reset_all_colors(skip_digestion=True)

    assert view._atom_color_map == {}  # noqa: SLF001
    assert view._test_message_log[-1] == {"op": "clear_atom_colors"}  # noqa: SLF001


def test_scene_style_name_is_public_read_only_state():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    applied = view.styles.apply(tag="polymer-cartoon", skip_digestion=True)

    assert applied.name == "Polymer Cartoon"
    assert view.scene_style_name == "Polymer Cartoon"
    assert view.whole.scene_style_name == "Polymer Cartoon"


def test_whole_context_actions_route_through_public_api():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "set_whole_representation",
            "representation": "cartoon",
            "params": {"alpha": 0.7},
        }
    )
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "set_whole_visibility",
            "visible": False,
        }
    )
    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "reset_all_colors",
        }
    )

    assert view.whole.representation == "cartoon"
    assert view.whole.params == {"alpha": 0.7}
    assert view.whole.visible is False
    assert [msg["op"] for msg in view._test_message_log[-3:]] == [  # noqa: SLF001
        "set_whole_representation",
        "hide_whole",
        "clear_atom_colors",
    ]
