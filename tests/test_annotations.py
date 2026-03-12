from molsysviewer import demo


def test_group_label_registers_annotation_layer_and_export_message():
    view = demo["dialanine"]
    expected_atom_indices = list(view.select(selection="group_index==0"))

    layer = view.annotations.add_label(text="Group 0", group_index=0, tag="notes")

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
                "atom_indices": expected_atom_indices,
            },
        }
    ]

    ops = [msg["op"] for msg in view._build_export_messages()]  # noqa: SLF001
    assert "add_label" in ops


def test_clear_decorations_labels_clears_annotation_history_only():
    view = demo["dialanine"]
    view.annotations.add_label(text="Group 0", group_index=0, tag="notes")
    view.shapes.add_sphere(center=[0.0, 0.0, 0.0], radius=1.0, tag="shape-notes")

    assert len(view._annotation_history) == 1  # noqa: SLF001
    assert len(view._shape_history) == 1  # noqa: SLF001

    view.clear_decorations(shapes=False, styles=False, labels=True)

    assert view._annotation_history == []  # noqa: SLF001
    assert len(view._shape_history) == 1  # noqa: SLF001


def test_annotation_manager_supports_query_and_layer_operations():
    view = demo["dialanine"]
    view.annotations.add_label(text="Group 0", group_index=0, tag="notes")

    assert view.annotations.count() == 1
    assert view.annotations.tags() == ["notes"]
    assert view.annotations.contains("notes") is True
    layer = view.annotations.get("notes")
    assert layer is not None
    assert layer.tag == "notes"
    assert view.annotations.records()[0]["options"]["text"] == "Group 0"
    assert view.annotations.info("notes") == {
        "kind": "label",
        "tag": "notes",
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
    assert view.annotations.tags() == []
    assert view.annotations.count() == 0


def test_annotation_manager_clear_tag_and_global_clear():
    view = demo["dialanine"]
    view.annotations.add_label(text="Group 0", group_index=0, tag="notes")
    view.annotations.add_label(text="Group 1", group_index=1, tag="notes-2")

    summaries = view.annotations.info()
    assert [item["tag"] for item in summaries] == ["notes", "notes-2"]

    view.annotations.clear(tag="notes")
    assert view.annotations.contains("notes") is False
    assert view.annotations.contains("notes-2") is True
    assert [item["tag"] for item in view.annotations.records()] == ["notes-2"]

    view.annotations.clear()
    assert view.annotations.tags() == []
    assert view.annotations.records() == []
    assert view.annotations.count() == 0


def test_annotation_manager_can_update_label_text_replay_safely():
    view = demo["dialanine"]
    view.annotations.add_label(text="Before", group_index=0, tag="notes")

    view.annotations.set_text("notes", "After")

    assert view.annotations.info("notes")["text"] == "After"
    assert view.annotations.records()[0]["options"]["text"] == "After"
    exported = [msg for msg in view._build_export_messages() if msg.get("tag") == "notes"]  # noqa: SLF001
    assert [msg["op"] for msg in exported] == ["add_label", "update_label"]
    assert exported[-1]["options"]["text"] == "After"


def test_annotation_manager_can_reanchor_label_to_new_group_replay_safely():
    view = demo["dialanine"]
    view.annotations.add_label(text="Anchor", group_index=0, tag="notes")

    expected_atom_indices = list(view.select(selection="group_index==1"))
    view.annotations.set_group_index("notes", 1)

    assert view.annotations.info("notes")["atom_indices"] == expected_atom_indices
    assert view.annotations.records()[0]["options"]["atom_indices"] == expected_atom_indices
    exported = [msg for msg in view._build_export_messages() if msg.get("tag") == "notes"]  # noqa: SLF001
    assert [msg["op"] for msg in exported] == ["add_label", "update_label"]
    assert exported[-1]["options"]["atom_indices"] == expected_atom_indices
