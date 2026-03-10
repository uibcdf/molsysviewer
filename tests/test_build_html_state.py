import json
import re

import pytest

from molsysviewer import MolSysView


def _extract_state_json(html: str) -> dict:
    match = re.search(
        r'application/vnd\.jupyter\.widget-state\+json">\n?(.+?)</script>',
        html,
        re.DOTALL,
    )
    assert match, "state JSON not found"
    return json.loads(match.group(1))


def test_build_html_filters_visibility(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    # Add redundant visibility message (full range) that should be stripped
    view._message_history = [
        {"op": "dummy"},
        {"op": "update_visibility", "options": {"visible_atom_indices": [0, 1, 2]}},
    ]

    # Avoid inlining huge bundle in this test
    monkeypatch.setattr(view, "_load_anywidget_bundle", lambda: "")

    html = view._build_standalone_html("Test", include_controls=True)
    state = _extract_state_json(html)
    widget_state = state["state"][view.widget.model_id]["state"]
    assert widget_state["initial_messages"] == [{"op": "dummy"}]


@pytest.mark.parametrize("include_bundle", [True, False])
def test_build_html_includes_anywidget(monkeypatch, include_bundle):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore
    monkeypatch.setattr(
        view,
        "_load_anywidget_bundle",
        lambda: "define('anywidget-inline', [], function(){return {};});" if include_bundle else "",
    )

    html = view._build_standalone_html("Test", include_controls=True)
    if include_bundle:
        assert "anywidget-inline" in html
        assert "requirejs.config" in html
    else:
        assert "anywidget-inline" not in html
        assert "requirejs.config" not in html


def test_build_html_includes_camera_snapshot(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore
    view._last_camera_snapshot = {"target": [0, 0, 0]}

    monkeypatch.setattr(view, "_load_anywidget_bundle", lambda: "")

    html = view._build_standalone_html("Test", include_controls=True)
    state = _extract_state_json(html)
    widget_state = state["state"][view.widget.model_id]["state"]

    assert widget_state["initial_messages"][-1] == {
        "op": "set_camera_snapshot",
        "snapshot": {"target": [0, 0, 0]},
        "duration_ms": 0,
    }


def test_build_export_messages_keeps_replay_order_and_appends_camera_snapshot():
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore
    view._message_history = [
        {"op": "load_molsys_payload", "payload": {"atoms": {"atom_id": [1, 2, 3]}, "structures": []}},
        {"op": "update_visibility", "options": {"visible_atom_indices": [0, 1, 2]}},
        {"op": "hide_global", "target": "global"},
    ]
    view._last_camera_snapshot = {"target": [1, 2, 3]}

    messages = view._build_export_messages()

    assert messages == [
        {"op": "load_molsys_payload", "payload": {"atoms": {"atom_id": [1, 2, 3]}, "structures": []}},
        {"op": "hide_global", "target": "global"},
        {
            "op": "set_camera_snapshot",
            "snapshot": {"target": [1, 2, 3]},
            "duration_ms": 0,
        },
    ]


def test_build_html_respects_popout_flag_in_export_state(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    monkeypatch.setattr(view, "_load_anywidget_bundle", lambda: "")

    html = view._build_standalone_html("Test", include_controls=True, include_popout=False)
    state = _extract_state_json(html)
    widget_state = state["state"][view.widget.model_id]["state"]

    assert widget_state["enable_popout"] is False
    if "popup_js_source" in widget_state:
        assert widget_state["popup_js_source"] == ""
