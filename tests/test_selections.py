from molsysviewer import demo


def _seed_group_selection(view, group_index=1):
    atom_indices = list(view.select(selection=f"group_index=={group_index}"))
    event = {
        "event": "interaction_active_selection_changed",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "items": [],
        "atom_indices": atom_indices,
        "group_indices": [group_index],
        "component_indices": [],
        "chain_indices": [0],
        "molecule_indices": [],
        "entity_indices": [0],
        "count_atoms": len(atom_indices),
        "count_groups": 1,
        "count_shapes": 0,
        "count_annotations": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001
    return atom_indices


def test_active_selection_save_creates_persistent_selection():
    view = demo["dialanine"]
    atom_indices = _seed_group_selection(view, 1)

    selection = view.active_selection.save("picked")

    assert selection.tag == "picked"
    assert view.selections.tags == ["picked"]
    assert view.selections.count() == 1
    assert view.selections.info("picked") == {
        "kind": "selection",
        "tag": "picked",
        "source_kind": "element",
        "element_level": "group",
        "target_level": "none",
        "n_atoms": len(atom_indices),
        "atom_indices": atom_indices,
        "group_indices": [1],
        "component_indices": [0],
        "chain_indices": [0],
        "molecule_indices": [0],
        "entity_indices": [0],
        "count_items": 0,
    }


def test_persistent_selection_supports_focus_region_and_label():
    view = demo["dialanine"]
    atom_indices = _seed_group_selection(view, 1)
    selection = view.active_selection.save("picked")

    selection.focus(duration_ms=50)
    assert view._message_history[-1]["op"] == "zoom"  # noqa: SLF001
    assert view._message_history[-1]["atom_indices"] == atom_indices  # noqa: SLF001

    region = selection.new_region(tag="picked-region", representation="ball_and_stick")
    assert region.tag == "picked-region"
    assert "picked-region" in view.regions

    label = selection.add_label("Picked", tag="picked-label")
    assert label.tag == "picked-label"
    assert view.annotations.contains("picked-label") is True


def test_persistent_selection_can_restore_itself_as_active_selection():
    view = demo["dialanine"]
    _seed_group_selection(view, 1)
    selection = view.active_selection.save("picked")
    view.active_selection.clear()

    restored = selection.activate()

    assert restored is view.active_selection
    assert view.active_selection.info()["source_kind"] == "element"
    assert view.active_selection.group_indices == [1]
    assert view._message_history[-1]["op"] == "set_active_selection"  # noqa: SLF001


def test_selections_manager_can_activate_by_tag():
    view = demo["dialanine"]
    _seed_group_selection(view, 2)
    view.active_selection.save("picked")
    view.active_selection.clear()

    restored = view.selections.activate("picked")

    assert restored is view.active_selection
    assert view.active_selection.group_indices == [2]


def test_persistent_selection_rename_delete_and_clear_update_records():
    view = demo["dialanine"]
    _seed_group_selection(view, 1)
    selection = view.active_selection.save("picked")

    renamed = selection.set_tag("saved")
    assert renamed.tag == "saved"
    assert view.selections.tags == ["saved"]
    assert view.selections.contains("picked") is False
    assert view.selections.contains("saved") is True

    view.selections.delete("saved")
    assert view.selections.count() == 0
    assert view.selections.tags == []

    _seed_group_selection(view, 2)
    view.active_selection.save("picked-2")
    assert view.selections.count() == 1
    view.selections.clear()
    assert view.selections.count() == 0


def test_persistent_selection_records_are_exported_and_remapped_on_remove():
    view = demo["dialanine"]
    atom_indices = _seed_group_selection(view, 1)
    view.active_selection.save("picked")

    messages = view._build_export_messages()  # noqa: SLF001
    selection_msg = next(msg for msg in messages if msg.get("op") == "save_selection")
    assert selection_msg["tag"] == "picked"
    assert selection_msg["atom_indices"] == atom_indices

    view.remove(selection="group_index==0")
    selection_info = view.selections.info("picked")
    assert selection_info["group_indices"] == [0]
    assert selection_info["atom_indices"] == list(range(0, 10))
