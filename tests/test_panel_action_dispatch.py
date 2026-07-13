from __future__ import annotations

import re
from pathlib import Path

from molsysviewer.demo import demo
from molsysviewer.viewer.panel_actions import (
    CONTEXT_ONLY_ACTIONS,
    FRONTEND_LOCAL_PANEL_ACTIONS,
    HANDLERS,
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
