from __future__ import annotations

import pytest
import molsysmt as msm

from molsysviewer import pyunitwizard as puw
from molsysviewer import MolSysView
from molsysviewer.demo import demo
from molsysviewer.viewer.panel_actions.scene_objects import (
    create_measurement,
    reanchor_annotation,
    set_annotation_style,
)


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
        label_style={
            "color": "#123456",
            "size_em": 1.25,
            "background": True,
            "background_opacity": 0.6,
        },
    )
    view.measurements.add(
        "distance",
        [0],
        [1],
        tag="distance",
        layer_tag="analysis",
    )
    view.measurements.add_angle([0], [1], [2], tag="angle")
    view.measurements.add_dihedral([0], [1], [2], [3], tag="dihedral")
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
        "style": {
            "color": "#123456",
            "size_em": 1.25,
            "background": True,
            "background_opacity": 0.6,
        },
        "n_atoms": 2,
        "atom_indices": [0, 1],
        "anchor": {"type": "atoms", "indices": [0, 1]},
        "hidden": False,
        "broken": False,
        "broken_reason": None,
    }]
    measurements = {
        record["tag"]: record for record in view._measurement_summary_records()  # noqa: SLF001
    }
    assert measurements["distance"]["atom_indices"] == [0, 1]
    for tag, kind, unit in (
        ("distance", "distance", "angstrom"),
        ("angle", "angle", "degree"),
        ("dihedral", "dihedral", "degree"),
    ):
        measurement = measurements[tag]
        assert measurement["kind"] == kind
        assert measurement["value"] is not None
        assert measurement["unit"] == unit
        assert measurement["value"] == pytest.approx(
            puw.get_value(view.measurements.info(tag)[0]["value"], to_unit=unit)
        )
        assert measurement["endpoint_labels"]
        assert measurement["endpoint_policy"] == "centroid"
        assert "series" not in measurement
        assert "value_series" not in measurement
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


def test_measurement_summary_reports_the_current_frame_value_in_presentation_units():
    molsys = demo["dialanine"].molsys.copy()
    moved = msm.structure.translate(
        molsys,
        translation=puw.quantity([[[0.1, 0.0, 0.0]]], "nm"),
        selection=[1],
        structure_indices=0,
        skip_digestion=True,
    )
    msm.append_structures(
        molsys,
        moved,
        structure_indices=0,
        skip_digestion=True,
    )
    view = MolSysView()
    view.widget.send = lambda _message: None  # type: ignore[method-assign]
    view.load(molsys)
    view.measurements.add_distance([0], [1], tag="d1")
    expected = puw.get_value(view.measurements.series("d1"), to_unit="angstrom")[1]
    sent = []
    view._send_runtime_only = lambda message: sent.append(message)  # type: ignore[method-assign]

    view._handle_frontend_event({  # noqa: SLF001
        "event": "trajectory_frame_changed",
        "frame": 1,
        "is_playing": False,
    })

    summary = sent[-1]["measurements"][0]
    assert summary["value"] == pytest.approx(expected)
    assert summary["unit"] == "angstrom"
    assert "series" not in summary
    assert "value_series" not in summary


def test_measurement_series_is_runtime_only_and_minmax_downsampled(monkeypatch):
    view = _view()
    view.measurements.add_distance([0], [1], tag="d1")
    quantity = puw.quantity([float(index % 17) for index in range(6000)], "angstrom")
    monkeypatch.setattr(view.measurements, "series", lambda _tag: quantity)

    payload = view._measurement_series_payload("d1", request_id=7)  # noqa: SLF001

    assert payload["request_id"] == 7
    assert "series" not in payload
    assert payload["n_frames"] == 6000
    assert len(payload["sparkline"]) <= 240
    assert len(payload["sparkline"]) == len(payload["sparkline_indices"])
    assert max(payload["sparkline"]) == 16.0


def test_measurement_series_panel_request_uses_runtime_only_transport():
    view = _view()
    view.measurements.add_distance([0], [1], tag="d1")
    sent = []
    view._send_runtime_only = lambda message: sent.append(message)  # type: ignore[method-assign]
    history_size = len(view._message_history)  # noqa: SLF001

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "request_measurement_series",
        "tag": "d1",
        "request_id": 17,
    })

    assert sent[-1]["op"] == "measurement_series"
    assert sent[-1]["request_id"] == 17
    assert len(view._message_history) == history_size  # noqa: SLF001


def test_measurement_settings_round_trip_with_scene_state():
    source = _view()
    source.measurements.set_endpoint_policy("representative_atom")
    source.measurements.set_representative_atom("protein", "CB")

    restored = _view()
    restored.import_state(source.export_state())

    assert restored.measurements.settings() == {
        "endpoint_policy_default": "representative_atom",
        "representative_atoms": {
            "protein": "CB",
            "nucleic": "P",
            "lipid": "P",
            "other": "",
        },
    }


def test_create_measurement_panel_action_uses_active_selection_groups_as_endpoints():
    view = _view()
    view.active_selection.set(selection="group_index in [0, 1]")

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "create_measurement",
        "kind": "distance",
    })

    record = view.measurements.info()[0]
    assert record["kind"] == "distance"
    assert record["n_picks"] == 2
    assert all(record["picks_atom_indices"])


@pytest.mark.parametrize(
    ("kind", "selection", "match"),
    [
        ("rmsd", "group_index in [0, 1]", "requires kind"),
        ("distance", "group_index==0", "requires 2 selected endpoints"),
    ],
)
def test_create_measurement_panel_action_rejects_invalid_kind_or_endpoint_count(
    kind, selection, match
):
    view = _view()
    view.active_selection.set(selection=selection)

    with pytest.raises(ValueError, match=match):
        create_measurement(view, {"kind": kind})

    assert view.measurements.count() == 0


def test_measurement_panel_lifecycle_actions_mutate_the_python_model():
    view = _view()
    view.measurements.add_distance([0], [1], tag="d1")

    def dispatch(action, **details):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "interaction_context_action",
            "action": action,
            **details,
        })

    dispatch("toggle_measurement_visibility", tag="d1")
    assert view.measurements.info("d1")[0]["visible"] is False
    dispatch("rename_measurement", tag="d1", new_tag="distance")
    dispatch("set_measurement_layer", tag="distance", layer="analysis")
    assert view.measurements.info("distance")[0]["layer_tag"] == "analysis"
    dispatch("show_all_measurements")
    assert view.measurements.info("distance")[0]["visible"] is True
    dispatch("hide_all_measurements")
    assert view.measurements.info("distance")[0]["visible"] is False
    dispatch("clear_measurements")
    assert view.measurements.count() == 0


def test_annotation_panel_actions_mutate_authoritative_state_and_summary():
    view = _view()
    view.active_selection.set(selection="group_index==0")

    def dispatch(action, **details):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "interaction_context_action",
            "action": action,
            **details,
        })

    dispatch(
        "create_annotation",
        text="Catalytic site",
        label_style={"color": "#112233", "size_em": 1.2},
    )
    tag = view.annotations.tags()[0]
    dispatch("set_annotation_text", tag=tag, text="Gate closed")
    dispatch(
        "set_annotation_style",
        tag=tag,
        style={
            "color": "#abcdef",
            "size_em": 1.5,
            "background": False,
            "background_opacity": 0.4,
        },
    )
    dispatch("rename_annotation", tag=tag, new_tag="gate")
    dispatch("set_annotation_layer", tag="gate", layer="analysis")

    info = view.annotations.info("gate")
    assert info["text"] == "Gate closed"
    assert info["layer_tag"] == "analysis"
    assert info["style"] == {
        "color": "#abcdef",
        "size_em": 1.5,
        "background": False,
        "background_opacity": 0.4,
    }
    summary = view._annotation_summary_records()[0]  # noqa: SLF001
    assert summary["tag"] == "gate"
    assert summary["style"] == info["style"]
    assert summary["anchor"] == {
        "type": "atoms",
        "indices": info["atom_indices"],
    }

    dispatch("toggle_annotation_visibility", tag="gate")
    assert view.annotations.info("gate")["visible"] is False
    dispatch("show_all_annotations")
    assert view.annotations.info("gate")["visible"] is True
    dispatch("hide_all_annotations")
    assert view.annotations.info("gate")["visible"] is False
    dispatch("clear_annotations")
    assert view.annotations.count() == 0


def test_annotation_panel_reanchors_to_the_active_selection():
    view = _view()
    view.annotations.add("Anchor", selection="group_index==0", tag="note")
    view.active_selection.set(selection="group_index==1")
    expected = list(view.active_selection.atom_indices)

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "reanchor_annotation",
        "tag": "note",
    })

    assert view.annotations.info("note")["atom_indices"] == expected


@pytest.mark.parametrize(
    ("action", "details", "match"),
    [
        ("set_annotation_style", {"tag": "note", "style": []}, "style mapping"),
        ("reanchor_annotation", {"tag": "note"}, "non-empty active selection"),
    ],
)
def test_annotation_panel_actions_reject_invalid_style_or_empty_reanchor(
    action, details, match
):
    view = _view()
    view.annotations.add("Anchor", atom_indices=[0], tag="note")

    with pytest.raises(ValueError, match=match):
        if action == "set_annotation_style":
            set_annotation_style(view, details)
        else:
            reanchor_annotation(view, details)


def test_endpoint_policy_panel_action_affects_only_future_measurements_and_is_undoable():
    view = _view()
    view.active_selection.set(selection="group_index in [0, 1]")
    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "create_measurement",
        "kind": "distance",
    })
    first_tag = view.measurements.tags()[0]

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "set_measurement_endpoint_policy",
        "policy": "representative_atom",
    })
    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "create_measurement",
        "kind": "distance",
    })
    second_tag = view.measurements.tags()[-1]

    assert view.measurements.info(first_tag)[0]["endpoint_policy"] == "centroid"
    assert view.measurements.info(second_tag)[0]["endpoint_policy"] == "representative_atom"
    assert view.history.can_undo() is True


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
