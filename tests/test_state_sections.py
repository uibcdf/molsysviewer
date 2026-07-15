import json

from molsysviewer import pyunitwizard as puw
from molsysviewer.demo import demo
from molsysviewer.viewer.panel_actions import dispatch_panel_action


def test_clipping_plane_survives_save_reload_as_usable_live_object():
    source = demo["dialanine"]
    source.scene.add_section(
        point=[0.1, 0.2, 0.3],
        normal=[2.0, 0.0, 0.0],
        invert=True,
        tag="cut",
    )

    document = source.export_state()
    json.dumps(document)
    assert document["sections"] == [{
        "tag": "cut",
        "point": [0.1, 0.2, 0.3],
        "normal": [1.0, 0.0, 0.0],
        "invert": True,
    }]

    restored = demo["dialanine"]
    restored.import_state(document)
    sections = restored.scene.sections()

    assert [section.tag for section in sections] == ["cut"]
    assert puw.get_value(sections[0].get_point(), to_unit="nm").tolist() == [0.1, 0.2, 0.3]
    assert sections[0].get_normal() == [1.0, 0.0, 0.0]
    assert sections[0].is_inverted() is True

    sections[0].set_point([0.4, 0.5, 0.6])
    sections[0].set_invert(False)
    assert restored.export_state()["sections"][0]["point"] == [0.4, 0.5, 0.6]
    assert restored.export_state()["sections"][0]["invert"] is False

    sections[0].delete()
    assert restored.scene.sections() == []


def test_old_v2_document_without_sections_imports_as_no_clipping_planes():
    view = demo["dialanine"]

    view.import_state({"version": 2, "regions": []})

    assert view.scene.sections() == []


def test_section_conflicts_follow_import_policy():
    source = demo["dialanine"]
    source.scene.add_section(point=[0.0, 0.0, 0.0], normal=[1, 0, 0], tag="cut")
    document = source.export_state()

    target = demo["dialanine"]
    target.scene.add_section(point=[1.0, 0.0, 0.0], normal=[0, 1, 0], tag="cut")
    target.import_state(document, clear_first=False, on_conflict="rename")

    assert [section.tag for section in target.scene.sections()] == ["cut", "cut_2"]


def test_section_creation_and_mutation_participate_in_scene_history():
    view = demo["dialanine"]
    view.history.clear()

    section = view.scene.add_section(
        point=[0.0, 0.0, 0.0], normal=[1, 0, 0], tag="cut"
    )
    section.set_invert(True)

    view.history.undo()
    assert view.scene.sections()[0].is_inverted() is False
    view.history.undo()
    assert view.scene.sections() == []
    view.history.redo()
    assert [item.tag for item in view.scene.sections()] == ["cut"]


def test_hidden_section_survives_state_round_trip_and_remains_removable():
    source = demo["dialanine"]
    source.scene.add_section([0.1, 0.2, 0.3], [1, 0, 0], tag="cut").hide()

    restored = demo["dialanine"]
    restored.import_state(source.export_state())
    section = restored.scene.sections()[0]

    assert section.visible is False
    assert restored.export_state()["sections"][0]["hidden"] is True
    section.delete()
    assert restored.scene.sections() == []


def test_a_restored_section_can_be_removed_from_the_panel():
    source = demo["dialanine"]
    source.scene.add_section([0.1, 0.2, 0.3], [1, 0, 0], tag="cut")
    fresh = demo["dialanine"]
    fresh.import_state(source.export_state())

    dispatch_panel_action(fresh, {"action": "remove_section", "tag": "cut"})

    assert "cut" not in [section.tag for section in fresh.scene.sections()]


def test_repeated_section_geometry_updates_coalesce_into_one_undo_step():
    view = demo["dialanine"]
    view.scene.add_section([0.0, 0.0, 0.0], [1, 0, 0], tag="cut")
    view.history.clear()

    view._handle_frontend_event({"event": "scene_history_coalescing_begin"})  # noqa: SLF001
    view._handle_frontend_event({  # noqa: SLF001
        "event": "section_moved", "tag": "cut", "point": [0.1, 0.0, 0.0], "normal": [0, 1, 0],
    })
    view._handle_frontend_event({  # noqa: SLF001
        "event": "section_moved", "tag": "cut", "point": [0.2, 0.0, 0.0], "normal": [0, 0, 1],
    })
    view._handle_frontend_event({"event": "scene_history_coalescing_end"})  # noqa: SLF001

    assert view.history.undo() is True
    restored = view.scene.sections()[0]
    assert puw.get_value(restored.get_point(), to_unit="nm").tolist() == [0.0, 0.0, 0.0]
    assert restored.get_normal() == [1.0, 0.0, 0.0]
    assert view.history.undo() is False
