from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from molsysviewer import pyunitwizard as puw
from molsysviewer.demo import demo
from molsysviewer.viewer.panel_actions import (
    CONTEXT_ONLY_ACTIONS,
    FRONTEND_LOCAL_PANEL_ACTIONS,
    HANDLERS,
    dispatch_panel_action,
)


def _typescript_panel_actions() -> set[str]:
    source = Path("molsysviewer/js/src/ui/panels/types.ts").read_text()
    declaration = source.split("export type PanelAction =", 1)[1].split(
        "export interface PanelContext", 1
    )[0]
    return set(re.findall(r'"([^"]+)"', declaration))


def test_python_handlers_cover_the_closed_panel_action_vocabulary_exactly():
    panel_actions = _typescript_panel_actions()

    assert FRONTEND_LOCAL_PANEL_ACTIONS <= panel_actions
    assert (panel_actions - FRONTEND_LOCAL_PANEL_ACTIONS) == (
        set(HANDLERS) - CONTEXT_ONLY_ACTIONS
    )


def test_every_declared_context_only_action_has_a_handler():
    assert CONTEXT_ONLY_ACTIONS <= set(HANDLERS)


def test_remote_reset_view_routes_through_the_python_authority():
    view = demo["pentalanine"]
    sent = []
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    view._ready = True  # noqa: SLF001

    dispatch_panel_action(view, {"action": "reset_view"})

    assert sent[-1] == {"op": "reset_view", "options": {}}


def test_trajectory_context_actions_mutate_python_authority_and_project_summary():
    view = demo["pentalanine"]
    sent = []
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    view._ready = True  # noqa: SLF001

    dispatch_panel_action(view, {"action": "set_trajectory_frame", "index": 4})
    assert view.player.index == 4
    assert sent[-2:] == [
        {"op": "set_trajectory_frame", "index": 4},
        {
            "op": "set_trajectory_summary",
            "frame": 4,
            "frame_count": view.player.n_structures,
            "is_playing": False,
            "fps": 30,
            "step": 1,
            "mode": "loop",
            "direction": "forward",
        },
    ]

    dispatch_panel_action(view, {"action": "step_trajectory", "by": -2})
    assert view.player.index == 2
    dispatch_panel_action(view, {
        "action": "set_trajectory_playback",
        "playback_action": "play",
        "fps": 12,
        "step": 2,
        "mode": "once",
        "direction": "backward",
    })
    assert view.player.is_playing is True
    assert sent[-1] == {
        "op": "set_trajectory_summary",
        "frame": 2,
        "frame_count": view.player.n_structures,
        "is_playing": True,
        "fps": 12,
        "step": 2,
        "mode": "once",
        "direction": "backward",
    }

    dispatch_panel_action(view, {
        "action": "set_trajectory_playback",
        "playback_action": "stop",
    })
    assert view.player.is_playing is False
    assert sent[-1]["op"] == "set_trajectory_summary"
    assert sent[-1]["is_playing"] is False


@pytest.mark.parametrize(
    "content",
    [
        {"action": "set_trajectory_frame", "index": -1},
        {"action": "set_trajectory_frame", "index": 10**9},
        {"action": "step_trajectory", "by": 0},
        {"action": "set_trajectory_playback", "playback_action": "play", "fps": 0},
        {"action": "set_trajectory_playback", "playback_action": "rewind"},
    ],
)
def test_trajectory_context_actions_reject_invalid_remote_intent(content):
    with pytest.raises(ValueError):
        dispatch_panel_action(demo["pentalanine"], content)


def test_unknown_panel_action_reports_a_backend_error_instead_of_failing_silently():
    view = demo["dialanine"]
    sent = []
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    view._ready = True  # noqa: SLF001

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "action_without_handler",
    })

    error = sent[-1]
    assert error["op"] == "backend_error_occurred"
    assert error["action"] == "action_without_handler"
    assert "Unsupported panel action" in error["error_message"]


def test_viewport_panel_actions_use_the_public_python_scene_api():
    view = demo["dialanine"]
    sent = []
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    view._ready = True  # noqa: SLF001

    for action, details in (
        ("toggle_background", {"mode": "light"}),
        ("toggle_spin", {"enabled": False}),
        ("toggle_swing", {"enabled": True}),
        ("set_camera_mode", {"mode": "orthographic"}),
        ("set_fog", {"enable": True, "intensity": 0.4}),
        ("set_figure_spec", {"figure_preset": "publication-dark", "figure_scale": 3.0}),
    ):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "interaction_context_action",
            "action": action,
            **details,
        })

    messages = [message["op"] for message in sent]
    assert messages == [
        "toggle_background",
        "toggle_spin",
        "toggle_swing",
        "set_camera_mode",
        "set_fog",
        "set_figure_spec",
    ]


def test_focus_measurement_panel_action_uses_the_measurement_public_api():
    view = demo["dialanine"]
    sent = []
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    view._ready = True  # noqa: SLF001
    view.measurements.add_distance(
        [0],
        [1],
        tag="backbone-distance",
        skip_digestion=True,
    )
    sent.clear()

    dispatch_panel_action(
        view,
        {"action": "focus_measurement", "tag": "backbone-distance"},
    )

    assert sent[-1]["op"] in {"zoom_to_position", "zoom"}


def test_viewport_section_actions_mutate_live_sections_and_use_molsysmt_center():
    view = demo["dialanine"]
    view.active_selection.set([0, 1], syntax="Indices", skip_digestion=True)

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "create_section_from_selection",
        "camera_forward": [0.0, 1.0, 0.0],
    })
    section = view.scene.sections()[0]
    expected = view.regions.add(
        [0, 1], syntax="Indices", tag="selected", skip_digestion=True,
    ).get_center(
        structure_indices=[view.current_structure_index],
        skip_digestion=True,
    )
    assert np.allclose(
        puw.get_value(section.get_point(), to_unit="nm"),
        puw.get_value(expected, to_unit="nm"),
    )

    for action, details in (
        ("set_section_point", {"point": {"magnitude": [4.0, 5.0, 6.0], "unit": "angstroms"}}),
        ("set_section_normal", {"normal": [0.0, 0.0, 2.0]}),
        ("set_section_invert", {"invert": True}),
        ("set_section_visibility", {"visible": False}),
    ):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "interaction_context_action", "action": action, "tag": section.tag, **details,
        })

    assert np.allclose(puw.get_value(section.get_point(), to_unit="nm"), [0.4, 0.5, 0.6])
    assert section.get_normal() == [0.0, 0.0, 1.0]
    assert section.is_inverted() is True
    assert section.visible is False

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action", "action": "remove_section", "tag": section.tag,
    })
    assert view.scene.sections() == []


def test_creating_a_section_from_the_active_selection_places_it_at_the_centroid():
    view = demo["dialanine"]
    view.active_selection.set([0, 1], syntax="Indices", skip_digestion=True)
    expected = view.regions.add(
        [0, 1], syntax="Indices", tag="selected", skip_digestion=True,
    ).get_center(
        structure_indices=[view.current_structure_index],
        skip_digestion=True,
    )

    dispatch_panel_action(view, {
        "action": "create_section_from_selection",
        "camera_forward": [0.0, 0.0, -1.0],
    })
    section = view.scene.sections()[-1]

    assert np.allclose(
        puw.get_value(section.get_point(), to_unit="nm"),
        puw.get_value(expected, to_unit="nm"),
    )
    assert section.get_normal() == [0.0, 0.0, -1.0]

    empty = demo["dialanine"]
    with pytest.raises(ValueError, match="non-empty active selection"):
        dispatch_panel_action(empty, {
            "action": "create_section_from_selection",
            "camera_forward": [0.0, 0.0, -1.0],
        })

    with pytest.raises(ValueError, match="non-zero vector"):
        dispatch_panel_action(view, {
            "action": "create_section_from_selection",
            "camera_forward": [0.0, 0.0, 0.0],
        })
