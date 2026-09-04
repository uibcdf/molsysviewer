"""What a self-contained export carries.

Since 2026-08-04 a self-contained export is the same page as a shared one with
the runtime embedded instead of addressed, so these assertions read the page
itself. Before, they read an ipywidgets state blob that also pulled require.js
and two `@jupyter-widgets` bundles from CDNs — which meant the "self-contained"
file did not render without a network.
"""

import json
import re

import pytest

from molsysviewer import MolSysView
from molsysviewer.widget import MolSysViewerWidget


def _block(html: str, element_id: str):
    match = re.search(
        rf'<script id="{element_id}" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match, f"{element_id} not found in the exported page"
    return json.loads(match.group(1))


def _export(view, **kwargs) -> str:
    """The page as `export.html` writes it, without touching the filesystem."""
    return view._build_lite_html(  # noqa: SLF001
        title="Test",
        include_controls=kwargs.pop("include_controls", True),
        include_popout=kwargs.pop("include_popout", True),
        messages=view._build_export_messages(),  # noqa: SLF001
        inline_messages=True,
        runtime_source=MolSysViewerWidget._viewer_js_source,
        **kwargs,
    )


def test_build_html_uses_canonical_state_instead_of_test_message_log(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    class HistoryMustNotBeRead:
        def __iter__(self):
            raise AssertionError("static export read _test_message_log")

    view._test_message_log = HistoryMustNotBeRead()  # type: ignore[assignment]  # noqa: SLF001

    ops = [m.get("op") for m in _block(_export(view), "molsysviewer-messages")]
    assert "show_whole" in ops
    assert "set_sections" in ops
    assert "set_addon_runtime_summary" in ops


@pytest.mark.parametrize(
    "machinery",
    ["requirejs", "anywidget-inline", "cdn.jsdelivr.net", "cdnjs.cloudflare.com",
     "vnd.jupyter.widget-state+json"],
)
def test_a_self_contained_export_needs_nobody(machinery):
    """The name has to be true: no host, no loader, no widget manager.

    This page used to be an ipywidgets document that fetched require.js and two
    `@jupyter-widgets` bundles at open time, so a reader without a network got
    nothing. If any of these reappears, that is the regression.
    """
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    assert machinery not in _export(view)


def test_build_html_includes_camera_snapshot(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore
    view._last_camera_snapshot = {"target": [0, 0, 0]}

    messages = _block(_export(view), "molsysviewer-messages")

    assert messages[-1] == {
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

    assert _block(_export(view), "molsysviewer-messages") == expected


def test_build_export_messages_project_current_scene_and_append_camera_snapshot():
    from molsysviewer.demo import demo

    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore
    view.whole.hide(skip_digestion=True)
    view._test_message_log.extend({"op": "noise", "n": i} for i in range(100))  # noqa: SLF001
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

    atom_indices = list(view.whole.select(selection="group_index==0"))
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

    ui = _block(_export(view, include_popout=False), "molsysviewer-ui")

    assert ui["enable_popout"] is False


def test_build_html_inlines_full_runtime_for_standalone(monkeypatch):
    view = MolSysView(debug_js=True)
    view.widget.send = lambda _msg: None  # type: ignore

    monkeypatch.setattr(MolSysViewerWidget, "_viewer_js_source", "export default { render() {} };")

    html = _export(view)

    assert _block(html, "molsysviewer-runtime-source") == "export default { render() {} };"
    assert _block(html, "molsysviewer-runtime-candidates") == [], (
        "a page that carries its runtime must not also address one"
    )
