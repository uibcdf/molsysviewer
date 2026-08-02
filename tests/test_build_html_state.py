import json
import re

import pytest

from molsysviewer import MolSysView
from molsysviewer.widget import MolSysViewerWidget


def _extract_state_json(html: str) -> dict:
    match = re.search(
        r'application/vnd\.jupyter\.widget-state\+json">\n?(.+?)</script>',
        html,
        re.DOTALL,
    )
    assert match, "state JSON not found"
    return json.loads(match.group(1))


def test_build_html_uses_canonical_state_instead_of_message_history(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    class HistoryMustNotBeRead:
        def __iter__(self):
            raise AssertionError("static export read _message_history")

    view._message_history = HistoryMustNotBeRead()  # type: ignore[assignment]  # noqa: SLF001

    # Avoid inlining huge bundle in this test
    monkeypatch.setattr(view, "_load_anywidget_bundle", lambda: "")

    html = view._build_standalone_html("Test", include_controls=True)
    state = _extract_state_json(html)
    widget_state = state["state"][view.widget.model_id]["state"]
    ops = [m.get("op") for m in widget_state["initial_messages"]]
    assert "show_whole" in ops
    assert "set_sections" in ops
    assert "set_addon_runtime_summary" in ops


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


def test_standalone_html_embeds_the_exact_canonical_static_snapshot(monkeypatch):
    from molsysviewer.demo import demo

    view = demo["dialanine"]
    view.regions.add("group_index==0", tag="exported")
    view._last_camera_snapshot = {"target": [1, 2, 3]}  # noqa: SLF001
    expected = view._build_export_messages()  # noqa: SLF001
    monkeypatch.setattr(view, "_load_anywidget_bundle", lambda: "")

    html = view._build_standalone_html("Test", include_controls=True)
    state = _extract_state_json(html)
    widget_state = state["state"][view.widget.model_id]["state"]

    assert widget_state["initial_messages"] == expected


def test_build_export_messages_project_current_scene_and_append_camera_snapshot():
    from molsysviewer.demo import demo

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore
    view.whole.hide(skip_digestion=True)
    view._message_history.extend({"op": "noise", "n": i} for i in range(100))  # noqa: SLF001
    view._last_camera_snapshot = {"target": [1, 2, 3]}

    messages = view._build_export_messages()

    ops = [message.get("op") for message in messages]
    assert ops[0] == "load_molsys_payload"
    assert "hide_whole" in ops
    assert "noise" not in ops
    assert messages[-1] == {
        "op": "set_camera_snapshot",
        "snapshot": {"target": [1, 2, 3]},
        "duration_ms": 0,
    }


def test_export_messages_include_hide_region_for_hidden_region():
    """A region hidden before export must have hide_region in export messages (item 5)."""
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    view.regions.add(
        atom_indices=[0, 1, 2],
        tag="pocket",
        representation="cartoon",
        skip_digestion=True,
    )
    view.regions["pocket"].hide(skip_digestion=True)

    messages = view._build_export_messages()  # noqa: SLF001
    ops = [m["op"] for m in messages if m.get("op") != "set_addon_runtime_summary"]

    assert "hide_region" in ops
    assert ops.index("create_region") < ops.index("hide_region"), \
        "create_region must precede hide_region in export"


def test_export_messages_include_hide_whole_when_view_is_hidden():
    """hide_whole in history must survive into export messages (item 5)."""
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    view.whole.hide(skip_digestion=True)

    messages = view._build_export_messages()  # noqa: SLF001
    ops = [m["op"] for m in messages if m.get("op") != "set_addon_runtime_summary"]

    assert "hide_whole" in ops
    assert "show_whole" not in ops


def test_export_messages_after_post_load_region_and_label():
    """Popup live-sync: region + label added after load appear in export in correct order (item 7)."""
    import pytest
    pytest.importorskip("molsysmt")
    from molsysviewer.demo import demo

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]

    atom_indices = list(view.select(selection="group_index==0"))
    view.regions.add(atom_indices=atom_indices, tag="r0", skip_digestion=True)
    view.annotations.add_annotation(
        text="Anchor",
        selection="group_index==0",
        tag="anchor",
        skip_digestion=True,
    )

    messages = view._build_export_messages()  # noqa: SLF001
    ops = [m["op"] for m in messages if m.get("op") != "set_addon_runtime_summary"]

    assert "load_molsys_payload" in ops
    assert "create_region" in ops
    assert "add_label" in ops
    assert ops.index("load_molsys_payload") < ops.index("create_region")
    assert ops.index("create_region") < ops.index("add_label")


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


def test_build_html_inlines_full_runtime_for_standalone(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    monkeypatch.setattr(view, "_load_anywidget_bundle", lambda: "")
    monkeypatch.setattr(MolSysViewerWidget, "_viewer_js_source", "export default { render() {} };")

    html = view._build_standalone_html("Test", include_controls=True)
    state = _extract_state_json(html)
    widget_state = state["state"][view.widget.model_id]["state"]

    assert widget_state["_esm"] == "export default { render() {} };"
