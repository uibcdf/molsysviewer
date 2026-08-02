from __future__ import annotations

import pytest
import molsysmt as msm

from molsysviewer import pyunitwizard as puw
from molsysviewer import MolSysView
from molsysviewer.demo import demo
from molsysviewer.layers import Shape
from molsysviewer.shapes import SHAPE_STYLE_CAPABILITIES
from molsysviewer.viewer.panel_actions.scene_objects import (
    create_measurement,
    reanchor_annotation,
    set_annotation_style,
    set_shape_color,
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
    for tag, kind in (
        ("distance", "distance"),
        ("angle", "angle"),
        ("dihedral", "dihedral"),
    ):
        measurement = measurements[tag]
        expected = puw.standardize(view.measurements.info(tag)["value"])
        assert measurement["kind"] == kind
        assert measurement["value"] is not None
        assert measurement["unit"] == str(puw.get_unit(expected))
        assert measurement["value"] == pytest.approx(puw.get_value(expected))
        assert measurement["endpoint_labels"]
        assert measurement["endpoint_policy"] == "centroid"
        assert "series" not in measurement
        assert "value_series" not in measurement
    shape = view._shape_summary_records()[0]  # noqa: SLF001
    radius = shape.pop("radius")
    assert radius["unit"] == "nanometer"
    assert radius["magnitude"] == pytest.approx(1.0)
    assert shape == {
        "op": "add_sphere",
        "kind": "sphere",
        "tag": "site",
        "layer_tag": "analysis",
        "title": "Sphere",
        "subtitle": "sphere",
        "atom_indices": [0],
        "hidden": False,
        "color": "#00ff00",
        "n_colors": None,
        "n_radii": None,
        "alpha": 0.4,
        "radius_scale": None,
        "length_scale": None,
        "broken": False,
        "broken_reason": None,
    }


def test_shape_summary_carries_real_style_values_and_standard_length_unit():
    view = _view()
    view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "angstrom"),
        radius=puw.quantity(3.0, "angstrom"),
        color="#aBcDeF",
        alpha=0.65,
        tag="site",
        skip_digestion=True,
    )

    info = view.shapes.info("site", skip_digestion=True)
    summary = view._shape_summary_records()[0]  # noqa: SLF001

    assert info["op"] == "add_sphere"
    assert info["color"] == "#abcdef"
    assert summary["color"] == "#abcdef"
    assert summary["alpha"] == pytest.approx(0.65)
    assert summary["radius"]["magnitude"] == pytest.approx(0.3)
    assert summary["radius"]["unit"] == "nanometer"


def test_shape_panel_actions_route_plural_style_without_not_implemented():
    view = _view()
    view.shapes.add_links(
        coordinate_pairs=puw.quantity([[[0, 0, 0], [1, 0, 0]]], "angstrom"),
        radius=puw.quantity(1.0, "angstrom"),
        color="#112233",
        alpha=0.4,
        tag="links",
        skip_digestion=True,
    )

    for action in (
        {"action": "set_shape_color", "tag": "links", "color": "#445566"},
        {"action": "set_shape_radius", "tag": "links", "radius": {"magnitude": 2.5, "unit": "angstrom"}},
        {"action": "set_shape_alpha", "tag": "links", "alpha": 0.75},
    ):
        view._handle_frontend_event({"event": "interaction_context_action", **action})  # noqa: SLF001

    options = view.shapes.records()[0]["options"]
    assert options["colors"] == [0x445566]
    assert options["radii"] == [2.5]
    assert options["alpha"] == pytest.approx(0.75)


def test_shape_panel_action_refuses_unsupported_control_before_mutator():
    view = _view()
    view.shapes.add_pocket_surface(atom_indices=[0, 1], tag="surface", skip_digestion=True)

    with pytest.raises(ValueError, match="not supported for shape op 'add_pocket_surface'"):
        set_shape_color(view, {"tag": "surface", "color": "#ffffff"})


def test_shape_panel_capability_matrix_only_exposes_working_mutators():
    argument = {
        "set_color": "#445566",
        "set_colors": "#445566",
        "set_alpha": 0.75,
        "set_radius": puw.quantity(2.5, "angstrom"),
        "set_radii": puw.quantity(2.5, "angstrom"),
        "set_radius_scale": 1.25,
        "set_length_scale": 1.5,
    }
    generic_options = {
        "center": [0.0, 0.0, 0.0],
        "centers": [[0.0, 0.0, 0.0]],
        "coordinate_pairs": [[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]],
        "tetra_coords": [[[0.0, 0.0, 0.0]] * 4],
        "vertices": [[[0.0, 0.0, 0.0]] * 3],
        "colors": [0x112233],
        "radii": [1.0],
        "tag": "shape",
        "layer_tag": "shape",
    }

    for op, capabilities in SHAPE_STYLE_CAPABILITIES.items():
        for capability in capabilities:
            view = MolSysView()
            view.widget.send = lambda _message: None  # type: ignore[method-assign]
            shape = Shape(view, "shape")
            view._scene_objects[("shape", "shape")] = shape  # noqa: SLF001
            message = {"op": op, "options": dict(generic_options)}
            view._shape_history = [message]  # noqa: SLF001
            view._test_message_log = [message]  # noqa: SLF001

            getattr(shape, capability)(argument[capability], skip_digestion=True)


def test_shape_style_mutation_republishes_the_authoritative_summary():
    view = _view()
    view.shapes.add_sphere(tag="site", skip_digestion=True)
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]

    view.shapes["site"].set_color("#445566", skip_digestion=True)

    summaries = [message for message in sent if message.get("op") == "set_shape_summaries"]
    assert summaries[-1]["shapes"][0]["color"] == "#445566"


def test_adding_rings_publishes_the_authoritative_summary():
    view = _view()
    sent = []
    view._ready = True  # noqa: SLF001
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]

    view.shapes.add_rings(
        centers=puw.quantity([[0.0, 0.0, 0.0]], "angstrom"),
        normals=[[0.0, 0.0, 1.0]],
        radii=puw.quantity([1.0], "angstrom"),
        tag="ring",
        skip_digestion=True,
    )

    summaries = [message for message in sent if message.get("op") == "set_shape_summaries"]
    assert summaries[-1]["shapes"][0]["op"] == "add_rings"


def test_ready_projects_all_scene_object_summaries():
    view = _view()
    sent = []
    view.widget.send = lambda message: sent.append(dict(message))  # type: ignore[method-assign]

    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001

    sent_ops = [message.get("op") for message in sent]
    assert "set_annotation_summaries" in sent_ops
    assert "set_measurement_summaries" in sent_ops
    assert "set_shape_summaries" in sent_ops
    assert "set_layer_summaries" in sent_ops


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
    assert view.measurements.info("distance")["visible"] is False
    assert view.shapes.info("site")["visible"] is False


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
    expected_quantity = puw.standardize(view.measurements.series("d1"))
    expected = puw.get_value(expected_quantity)[1]
    sent = []
    view._send_runtime_only = lambda message: sent.append(message)  # type: ignore[method-assign]

    view._handle_frontend_event({  # noqa: SLF001
        "event": "trajectory_frame_changed",
        "frame": 1,
        "is_playing": False,
    })

    summary = sent[-1]["measurements"][0]
    assert summary["value"] == pytest.approx(expected)
    assert summary["unit"] == str(puw.get_unit(expected_quantity))
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
    assert max(payload["sparkline"]) == pytest.approx(1.6)
    assert payload["unit"] == "nanometer"


def test_measurement_series_panel_request_uses_runtime_only_transport():
    view = _view()
    view.measurements.add_distance([0], [1], tag="d1")
    sent = []
    view._send_runtime_only = lambda message: sent.append(message)  # type: ignore[method-assign]
    history_size = len(view._test_message_log)  # noqa: SLF001

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "request_measurement_series",
        "tag": "d1",
        "request_id": 17,
    })

    assert sent[-1]["op"] == "measurement_series"
    assert sent[-1]["request_id"] == 17
    assert len(view._test_message_log) == history_size  # noqa: SLF001


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
    assert view.measurements.info("d1")["visible"] is False
    dispatch("rename_measurement", tag="d1", new_tag="distance")
    dispatch("set_measurement_layer", tag="distance", layer="analysis")
    assert view.measurements.info("distance")["layer_tag"] == "analysis"
    dispatch("show_all_measurements")
    assert view.measurements.info("distance")["visible"] is True
    dispatch("hide_all_measurements")
    assert view.measurements.info("distance")["visible"] is False
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

    assert view.measurements.info(first_tag)["endpoint_policy"] == "centroid"
    assert view.measurements.info(second_tag)["endpoint_policy"] == "representative_atom"
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
