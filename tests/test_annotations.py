import pytest
import pyunitwizard as puw
import molsysviewer._pyunitwizard  # noqa: F401

from molsysviewer import demo


def test_group_label_registers_annotation_layer_and_export_message():
    view = demo["dialanine"]
    expected_atom_indices = list(view.select(selection="group_index==0"))

    layer = view.annotations.add_annotation(text="Group 0", selection="group_index==0", tag="notes")

    assert layer.tag == "notes"
    assert layer.kind == "annotation"
    assert "notes" in view.layers
    assert view.layers["notes"].kind == "annotation"
    assert view._annotation_history == [  # noqa: SLF001
        {
            "op": "add_label",
            "tag": "notes",
            "options": {
                "text": "Group 0",
                "tag": "notes",
                "layer_tag": "notes",
                "atom_indices": expected_atom_indices,
            },
        }
    ]

    ops = [msg["op"] for msg in view._build_export_messages()]  # noqa: SLF001
    assert "add_label" in ops


def test_group_label_uses_annotation_prefix_by_default():
    view = demo["dialanine"]

    layer = view.annotations.add_annotation(text="Group 0", selection="group_index==0")

    assert layer.tag == "annotation1"
    assert layer.layer_tag == "annotation1"
    assert view.annotations.tags == ["annotation1"]
    assert view.annotations.records()[0]["tag"] == "annotation1"
    assert view.annotations.records()[0]["options"]["tag"] == "annotation1"
    assert view.annotations.records()[0]["options"]["layer_tag"] == "annotation1"


def test_clear_decorations_labels_clears_annotation_history_only():
    view = demo["dialanine"]
    view.annotations.add_annotation(text="Group 0", selection="group_index==0", tag="notes")
    view.shapes.add_sphere(center=puw.quantity([0.0, 0.0, 0.0], "nm"), radius=puw.quantity(1.0, "nm"), tag="shape-notes")

    assert len(view._annotation_history) == 1  # noqa: SLF001
    assert len(view._shape_history) == 1  # noqa: SLF001

    view.clear_decorations(shapes=False, styles=False, labels=True)

    assert view._annotation_history == []  # noqa: SLF001
    assert len(view._shape_history) == 1  # noqa: SLF001


def test_annotation_manager_supports_query_and_layer_operations():
    view = demo["dialanine"]
    view.annotations.add_annotation(text="Group 0", selection="group_index==0", tag="notes")

    assert view.annotations.count() == 1
    assert view.annotations.tags == ["notes"]
    assert view.annotations.contains("notes") is True
    layer = view.annotations.get("notes")
    assert layer is not None
    assert view.annotations["notes"] is layer
    assert view.layers["notes"].annotations == {"notes": layer}
    assert view.layers["notes"].members == {("annotation", "notes"): layer}
    assert layer.tag == "notes"
    assert view.annotations.records()[0]["options"]["text"] == "Group 0"
    assert view.annotations.info("notes") == {
        "kind": "label",
        "tag": "notes",
        "layer_tag": "notes",
        "text": "Group 0",
        "n_atoms": len(view.select(selection="group_index==0")),
        "atom_indices": list(view.select(selection="group_index==0")),
        "visible": True,
        "active": True,
    }

    view.annotations.hide("notes")
    assert view.layers["notes"]._hidden is True  # noqa: SLF001
    assert view.annotations.info("notes")["visible"] is False

    view.annotations.show("notes")
    assert view.layers["notes"]._hidden is False  # noqa: SLF001

    renamed = view.annotations.set_tag("notes", "analysis-label")
    assert renamed.tag == "analysis-label"
    assert view.annotations.contains("notes") is False
    assert view.annotations.contains("analysis-label") is True
    assert view.annotations.records()[0]["tag"] == "analysis-label"
    assert view.annotations.records()[0]["options"]["tag"] == "analysis-label"

    view.annotations.delete("analysis-label")
    assert view.annotations.tags == []
    assert view.annotations.count() == 0


def test_annotation_manager_rejects_duplicate_tags():
    view = demo["dialanine"]
    view.annotations.add_annotation(text="Group 0", selection="group_index==0", tag="notes")

    with pytest.raises(ValueError, match="already exists"):
        view.annotations.add_annotation(text="Group 1", selection="group_index==1", tag="notes")

    with pytest.raises(KeyError):
        _ = view.annotations["missing"]


def test_annotation_manager_supports_explicit_shared_layer_tag():
    view = demo["dialanine"]
    first = view.annotations.add_annotation(text="Group 0", selection="group_index==0", tag="notes-a", layer_tag="analysis")
    second = view.annotations.add_annotation(text="Group 1", selection="group_index==1", tag="notes-b", layer_tag="analysis")

    assert first.layer_tag == "analysis"
    assert second.layer_tag == "analysis"
    assert "analysis" in view.layers
    assert set(view.layers["analysis"].annotations.keys()) == {"notes-a", "notes-b"}
    assert set(view.layers["analysis"].members.keys()) == {("annotation", "notes-a"), ("annotation", "notes-b")}


def test_annotation_manager_can_move_annotation_between_layers():
    view = demo["dialanine"]
    layer = view.annotations.add_annotation(text="Group 0", selection="group_index==0", tag="notes")

    moved = view.annotations.set_layer_tag("notes", "analysis")

    assert moved is layer
    assert view.annotations["notes"].layer_tag == "analysis"
    assert "notes" not in view.layers
    assert "analysis" in view.layers
    assert view.layers["analysis"].annotations == {"notes": layer}
    assert view.annotations.info("notes")["layer_tag"] == "analysis"
    assert view.annotations.records()[0]["options"]["layer_tag"] == "analysis"
    exported = [msg for msg in view._build_export_messages() if msg.get("tag") == "notes"]  # noqa: SLF001
    assert exported[0]["options"]["layer_tag"] == "analysis"


def test_annotation_manager_clear_tag_and_global_clear():
    view = demo["dialanine"]
    view.annotations.add_annotation(text="Group 0", selection="group_index==0", tag="notes")
    view.annotations.add_annotation(text="Group 1", selection="group_index==1", tag="notes-2")

    summaries = view.annotations.info()
    assert [item["tag"] for item in summaries] == ["notes", "notes-2"]

    view.annotations.clear(tag="notes")
    assert view.annotations.contains("notes") is False
    assert view.annotations.contains("notes-2") is True
    assert [item["tag"] for item in view.annotations.records()] == ["notes-2"]

    view.annotations.clear()
    assert view.annotations.tags == []
    assert view.annotations.records() == []
    assert view.annotations.count() == 0


def test_annotation_manager_can_update_label_text_replay_safely():
    view = demo["dialanine"]
    view.annotations.add_annotation(text="Before", selection="group_index==0", tag="notes")

    view.annotations.set_text("notes", "After")

    assert view.annotations.info("notes")["text"] == "After"
    assert view.annotations.records()[0]["options"]["text"] == "After"
    exported = [msg for msg in view._build_export_messages() if msg.get("tag") == "notes"]  # noqa: SLF001
    assert [msg["op"] for msg in exported] == ["add_label", "update_label"]
    assert exported[-1]["options"]["text"] == "After"


def test_annotation_manager_set_anchor_reanchors_by_selection_replay_safely():
    view = demo["dialanine"]
    view.annotations.add_annotation(text="Anchor", selection="group_index==0", tag="notes")

    expected_atom_indices = list(view.select(selection="group_index==1"))
    view.annotations.set_anchor("notes", selection="group_index==1")

    assert view.annotations.info("notes")["atom_indices"] == expected_atom_indices
    assert view.annotations.records()[0]["options"]["atom_indices"] == expected_atom_indices
    exported = [msg for msg in view._build_export_messages() if msg.get("tag") == "notes"]  # noqa: SLF001
    assert [msg["op"] for msg in exported] == ["add_label", "update_label"]
    assert exported[-1]["options"]["atom_indices"] == expected_atom_indices


def test_annotation_manager_set_anchor_accepts_explicit_atom_indices():
    view = demo["dialanine"]
    view.annotations.add_annotation(text="Anchor", selection="group_index==0", tag="notes")

    explicit = list(view.select(selection="group_index==1"))
    view.annotations.set_anchor("notes", atom_indices=explicit)

    assert view.annotations.info("notes")["atom_indices"] == explicit


def test_annotation_manager_set_group_index_is_deprecated_wrapper():
    view = demo["dialanine"]
    view.annotations.add_annotation(text="Anchor", selection="group_index==0", tag="notes")

    expected_atom_indices = list(view.select(selection="group_index==1"))
    with pytest.warns(DeprecationWarning, match="set_group_index"):
        view.annotations.set_group_index("notes", 1)

    assert view.annotations.info("notes")["atom_indices"] == expected_atom_indices


def test_add_annotation_with_style_stores_style_in_message():
    view = demo["dialanine"]
    expected_atom_indices = list(view.select(selection="group_index==0"))

    view.annotations.add_annotation(
        text="Styled",
        selection="group_index==0",
        tag="styled",
        label_style={"color": "#FF0000", "size_em": 1.5, "background": True, "background_opacity": 0.7},
    )

    record = view._annotation_history[0]  # noqa: SLF001
    assert record["options"]["style"] == {
        "color": "#FF0000",
        "size_em": 1.5,
        "background": True,
        "background_opacity": 0.7,
    }
    assert record["options"]["atom_indices"] == expected_atom_indices


def test_add_annotation_without_style_omits_style_from_message():
    view = demo["dialanine"]

    view.annotations.add_annotation(text="Plain", selection="group_index==0", tag="plain")

    record = view._annotation_history[0]  # noqa: SLF001
    assert "style" not in record["options"]


def test_add_annotation_partial_style_only_includes_provided_keys():
    view = demo["dialanine"]

    view.annotations.add_annotation(
        text="Half",
        selection="group_index==0",
        tag="half",
        label_style={"color": "#00FF00"},
    )

    record = view._annotation_history[0]  # noqa: SLF001
    assert record["options"]["style"] == {"color": "#00FF00"}
    assert "size_em" not in record["options"]["style"]
    assert "background" not in record["options"]["style"]
