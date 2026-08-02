from __future__ import annotations

from copy import deepcopy
import json

from molsysviewer import FigureSpec, MolSysView
from molsysviewer.demo import demo


def _normalized(messages: list[dict]) -> list[dict]:
    result = deepcopy(messages)
    for message in result:
        if message.get("op") == "update_visibility":
            message.get("options", {}).pop("version", None)
    return result


def test_static_export_content_and_size_ignore_one_hundred_thousand_history_entries():
    view = demo["dialanine"]
    view.regions.add("group_index==0", tag="current")
    before = view._build_export_messages()  # noqa: SLF001

    view._message_history.extend(  # noqa: SLF001
        {"op": "irrelevant_interaction", "index": index}
        for index in range(100_000)
    )
    after = view._build_export_messages()  # noqa: SLF001

    assert _normalized(after) == _normalized(before)
    assert len(json.dumps(after, separators=(",", ":"))) == len(
        json.dumps(before, separators=(",", ":"))
    )


def test_static_export_embeds_hostless_state_that_live_popup_excludes():
    view = demo["dialanine"]
    view._last_camera_snapshot = {  # noqa: SLF001
        "target": [1.0, 2.0, 3.0],
        "position": [4.0, 5.0, 6.0],
    }
    view.set_figure_spec(FigureSpec(preset="publication-light"))

    static = view._build_export_messages()  # noqa: SLF001
    popup = view.build_popup_scene_snapshot("canvas")
    static_ops = [message.get("op") for message in static]
    popup_ops = [message.get("op") for message in popup]

    assert "set_figure_spec" in static_ops
    assert "set_addon_runtime_summary" in static_ops
    assert static_ops[-1] == "set_camera_snapshot"
    assert "set_camera_snapshot" not in popup_ops


def test_static_export_does_not_consult_the_append_only_journal():
    view = MolSysView()

    class HistoryMustNotBeRead:
        def __iter__(self):
            raise AssertionError("static export read _message_history")

    view._message_history = HistoryMustNotBeRead()  # type: ignore[assignment]  # noqa: SLF001
    messages = view._build_export_messages()  # noqa: SLF001

    assert any(message.get("op") == "set_sections" for message in messages)
