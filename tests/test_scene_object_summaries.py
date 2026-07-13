from __future__ import annotations

from molsysviewer import pyunitwizard as puw
from molsysviewer.demo import demo


def _view():
    view = demo["dialanine"]
    view.widget.send = lambda _message: None  # type: ignore[method-assign]
    return view


def test_scene_object_summary_records_project_manager_info():
    view = _view()
    view.layers.add("analysis", skip_digestion=True)
    view.annotations.add(
        "site",
        atom_indices=[0, 1],
        tag="note",
        layer_tag="analysis",
    )
    view.measurements.add(
        "distance",
        [0],
        [1],
        tag="distance",
        layer_tag="analysis",
    )
    view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="site",
        layer_tag="analysis",
        atom_indices=[0],
        skip_digestion=True,
    )

    assert view._annotation_summary_records() == [{  # noqa: SLF001
        "kind": "label",
        "tag": "note",
        "layer_tag": "analysis",
        "text": "site",
        "atom_indices": [0, 1],
        "hidden": False,
        "broken": False,
        "broken_reason": None,
    }]
    measurement = view._measurement_summary_records()[0]  # noqa: SLF001
    assert measurement["tag"] == "distance"
    assert measurement["kind"] == "distance"
    assert measurement["atom_indices"] == [0, 1]
    assert measurement["value"] is not None
    assert measurement["unit"] == "nanometer"
    shape = view._shape_summary_records()[0]  # noqa: SLF001
    assert shape == {
        "kind": "sphere",
        "tag": "site",
        "layer_tag": "analysis",
        "title": "Sphere",
        "subtitle": "sphere",
        "atom_indices": [0],
        "hidden": False,
    }


def test_ready_resends_all_scene_object_summaries_runtime_only(monkeypatch):
    view = _view()
    sent_ops = []
    monkeypatch.setattr(
        view,
        "_send_runtime_only",
        lambda message: sent_ops.append(message["op"]),
    )

    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001

    assert "set_annotation_summaries" in sent_ops
    assert "set_measurement_summaries" in sent_ops
    assert "set_shape_summaries" in sent_ops


def test_hiding_a_layer_resyncs_member_summaries_with_final_visibility(monkeypatch):
    view = _view()
    layer = view.layers.add("analysis", skip_digestion=True)
    view.annotations.add("site", atom_indices=[0], tag="note", layer_tag="analysis")
    view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="site",
        layer_tag="analysis",
        skip_digestion=True,
    )
    sent = []
    monkeypatch.setattr(view, "_send_runtime_only", lambda message: sent.append(message))

    layer.hide(skip_digestion=True)

    latest = {message["op"]: message for message in sent}
    assert latest["set_annotation_summaries"]["annotations"][0]["hidden"] is True
    assert latest["set_shape_summaries"]["shapes"][0]["hidden"] is True


def test_panel_visibility_actions_mutate_the_authoritative_python_model():
    view = _view()
    view.annotations.add("site", atom_indices=[0], tag="note")
    view.measurements.add("distance", [0], [1], tag="distance")
    view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="site",
        skip_digestion=True,
    )

    for action, tag in (
        ("toggle_annotation_visibility", "note"),
        ("toggle_measurement_visibility", "distance"),
        ("toggle_shape_visibility", "site"),
    ):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "interaction_context_action",
            "action": action,
            "tag": tag,
        })

    assert view.annotations.info("note")["visible"] is False
    assert view.measurements.info("distance")[0]["visible"] is False
    assert view.shapes.info("site")[0]["visible"] is False


def test_frame_change_refreshes_measurements_without_republishing_static_domains():
    view = _view()
    sent = []
    view._send_runtime_only = lambda message: sent.append(message)  # type: ignore[method-assign]

    view._handle_frontend_event({  # noqa: SLF001
        "event": "trajectory_frame_changed",
        "frame": 0,
        "is_playing": False,
    })

    assert [message["op"] for message in sent] == ["set_measurement_summaries"]


def test_system_rebuild_republishes_all_scene_object_summaries():
    view = _view()
    view.annotations.add("site", atom_indices=[0], tag="note")
    view.measurements.add("distance", [0], [1], tag="distance")
    view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="site",
        skip_digestion=True,
    )
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]
    n_atoms = int(view.molsys.get_n_atoms())

    view.apply_system_edit(
        view.molsys.copy(),
        atom_index_map={index: index for index in range(n_atoms)},
        skip_digestion=True,
    )

    latest = {message["op"]: message for message in sent}
    assert latest["set_annotation_summaries"]["annotations"][0]["tag"] == "note"
    assert latest["set_measurement_summaries"]["measurements"][0]["tag"] == "distance"
    assert latest["set_shape_summaries"]["shapes"][0]["tag"] == "site"
