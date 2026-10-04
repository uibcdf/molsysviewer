from __future__ import annotations

import json
from copy import deepcopy

from molsysviewer.demo import demo

from molsysviewer import FigureSpec, MolSysView


def _normalized(messages: list[dict]) -> list[dict]:
    result = deepcopy(messages)
    for message in result:
        message.get("options", {}).pop("version", None)
    return result


def test_static_export_content_and_size_ignore_one_hundred_thousand_trace_entries():
    view = demo["dialanine"]
    view.regions.add("group_index==0", tag="current")
    before = view._build_export_messages()  # noqa: SLF001

    view._test_message_log.extend(  # noqa: SLF001
        {"op": "irrelevant_interaction", "index": index} for index in range(100_000)
    )
    after = view._build_export_messages()  # noqa: SLF001

    assert _normalized(after) == _normalized(before)
    assert len(json.dumps(after, separators=(",", ":"))) == len(json.dumps(before, separators=(",", ":")))


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


def test_static_export_does_not_consult_the_test_protocol_trace():
    view = MolSysView()

    class TraceMustNotBeRead:
        def __iter__(self):
            raise AssertionError("static export read the test protocol trace")

    view._test_message_log = TraceMustNotBeRead()  # type: ignore[assignment]  # noqa: SLF001
    messages = view._build_export_messages()  # noqa: SLF001

    assert any(message.get("op") == "set_sections" for message in messages)


def test_static_export_preserves_complete_panel_summaries_without_duplicate_scene_operations():
    from molsysviewer._pyunitwizard import puw

    with demo["pentalanine"] as view:
        view.regions.add(atom_indices=[0, 1], tag="saved-region", representation="spacefill").hide()
        view.annotations.add("Saved label", atom_indices=[0], tag="saved-label")
        view.measurements.add_distance([0], [1], tag="saved-distance")
        view.shapes.add_sphere(center=puw.quantity([0, 0, 0], "nm"), radius="0.2 nm", tag="saved-sphere")
        view.selections.add("saved-selection", atom_indices=[0, 1])
        state = deepcopy(view.export_state())
        static = view._build_export_messages()
        panel = view.build_popup_scene_snapshot("panel")
        canvas = view.build_popup_scene_snapshot("canvas")
        summaries = [
            message for message in panel if message["op"].endswith("_summary") or message["op"].endswith("_summaries")
        ]
        assert len(summaries) >= 8
        for expected in summaries:
            matching = [message for message in static if message["op"] == expected["op"]]
            assert matching == [expected]
        region = next(message for message in static if message["op"] == "set_region_summaries")["regions"][0]
        assert region["tag"] == "saved-region" and region["hidden"] is True
        assert region["representation"] == "spacefill"
        for operation in ("save_selection", "set_active_selection", "set_measurement_settings"):
            assert [msg for msg in static if msg["op"] == operation] == [
                msg for msg in canvas if msg["op"] == operation
            ]
        assert "set_region_summaries" not in [message["op"] for message in canvas]
        assert view.export_state() == state
