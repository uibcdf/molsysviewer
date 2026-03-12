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
