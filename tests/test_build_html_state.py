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
    view = MolSysView()
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
    view = MolSysView()
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
