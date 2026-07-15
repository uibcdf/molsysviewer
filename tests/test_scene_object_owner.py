from __future__ import annotations

import pytest

from molsysviewer.demo import demo
from molsysviewer import pyunitwizard as puw


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


def test_attributed_to_covers_scene_domains_and_restores_nested_context():
    view = _mute(demo["dialanine"])

    with view.attributed_to("elastnetmt"):
        layer = view.layers.add("analysis", skip_digestion=True)
        shape = view.shapes.add_sphere(
            center=puw.quantity([0.0, 0.0, 0.0], "nm"),
            tag="mode1",
            layer_tag="analysis",
            skip_digestion=True,
        )
        annotation = view.annotations.add(
            "site",
            atom_indices=[0],
            tag="note1",
            layer_tag="analysis",
        )
        measurement = view.measurements.add(
            "distance",
            [0],
            [1],
            tag="distance1",
            layer_tag="analysis",
        )
        region = view.regions.add(atom_indices=[0, 1], tag="region1", skip_digestion=True)
        section = view.scene.add_section([0.0, 0.0, 0.0], [1.0, 0.0, 0.0], tag="section1")
        with view.attributed_to("topomt"):
            nested = view.shapes.add_sphere(tag="pocket1", skip_digestion=True)
        after_nested = view.shapes.add_sphere(tag="mode2", skip_digestion=True)

    user_shape = view.shapes.add_sphere(tag="mine", skip_digestion=True)

    assert {obj.owner for obj in (layer, shape, annotation, measurement, region, section, after_nested)} == {
        "elastnetmt"
    }
    assert nested.owner == "topomt"
    assert user_shape.owner is None
    with pytest.raises(AttributeError):
        shape.owner = "somebody-else"  # type: ignore[misc]


def test_attributed_to_restores_context_after_an_exception():
    view = _mute(demo["dialanine"])

    with pytest.raises(RuntimeError, match="stop"):
        with view.attributed_to("elastnetmt"):
            raise RuntimeError("stop")

    assert view.shapes.add_sphere(tag="mine", skip_digestion=True).owner is None


def test_owner_survives_state_v2_round_trip_for_every_scene_domain():
    source = _mute(demo["dialanine"])
    with source.attributed_to("elastnetmt"):
        source.layers.add("analysis", skip_digestion=True)
        source.shapes.add_sphere(tag="mode1", layer_tag="analysis", skip_digestion=True)
        source.annotations.add("site", atom_indices=[0], tag="note1", layer_tag="analysis")
        source.measurements.add("distance", [0], [1], tag="distance1", layer_tag="analysis")
        source.regions.add(atom_indices=[0, 1], tag="region1", skip_digestion=True)
        source.scene.add_section([0.0, 0.0, 0.0], [1.0, 0.0, 0.0], tag="section1")

    restored = _mute(demo["dialanine"])
    restored.import_state(source.export_state())

    assert restored.layers.info("analysis")["owner"] == "elastnetmt"
    assert restored.shapes.info("mode1")["owner"] == "elastnetmt"
    assert restored.annotations.info("note1")["owner"] == "elastnetmt"
    assert restored.measurements.info("distance1")["owner"] == "elastnetmt"
    assert restored.regions.info("region1")["owner"] == "elastnetmt"
    assert restored.scene.sections()[0].owner == "elastnetmt"


def test_v2_document_without_owner_imports_as_user_owned():
    view = _mute(demo["dialanine"])
    legacy_v2 = {
        "version": 2,
        "regions": [
            {
                "tag": "legacy",
                "atom_indices": [0, 1],
                "provenance": {
                    "kind": "imported",
                    "state_version": 2,
                    "frame_dependent": False,
                },
                "mode": "static",
                "order": 1,
            }
        ],
    }

    view.import_state(legacy_v2)

    assert view.regions.info("legacy")["owner"] is None


def test_owner_does_not_change_after_rename_or_layer_move():
    view = _mute(demo["dialanine"])
    view.layers.add("destination", skip_digestion=True)
    with view.attributed_to("elastnetmt"):
        shape = view.shapes.add_sphere(tag="mode1", skip_digestion=True)

    shape.set_tag("renamed", skip_digestion=True)
    shape.set_layer_tag("destination", skip_digestion=True)

    assert shape.owner == "elastnetmt"
    assert view.shapes.info("renamed")["owner"] == "elastnetmt"


def test_owned_shape_remains_deletable_from_panel_action():
    view = _mute(demo["dialanine"])
    with view.attributed_to("elastnetmt"):
        shape = view.shapes.add_sphere(tag="mode1", skip_digestion=True)

    view._handle_frontend_event(  # noqa: SLF001
        {
            "event": "interaction_context_action",
            "action": "delete_shape",
            "tag": "mode1",
            "context": {"kind": "shape", "tag": "mode1", "atom_indices": []},
        }
    )

    assert shape._active is False  # noqa: SLF001
    assert view.shapes.contains("mode1", skip_digestion=True) is False
