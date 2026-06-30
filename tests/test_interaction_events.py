from molsysviewer import MolSysView
from molsysviewer.regions import Region


def test_frontend_interaction_events_are_stored_on_view():
    view = MolSysView()

    hover = {"event": "interaction_hover", "kind": "structure", "atom_indices": [1, 2, 3]}
    click = {"event": "interaction_click", "kind": "empty"}
    context = {"event": "interaction_context_menu", "kind": "structure", "atom_indices": [4], "page_x": 10, "page_y": 20}
    action = {"event": "interaction_context_action", "action": "distance", "context": context}
    active_selection = {"event": "interaction_active_selection_changed", "source_kind": "element", "atom_indices": [4]}
    tool_state = {"event": "interaction_tool_state", "action": "distance", "status": "started", "picked_count": 1}
    measurement = {
        "event": "interaction_measurement_created",
        "action": "distance",
        "picked_count": 2,
        "picks_atom_indices": [[1], [2, 3]],
        "endpoint_kinds": ["atom", "centroid"],
        "endpoint_policy": "centroid",
        "endpoint_labels": ["atom", "centroid"],
        "endpoint_atom_indices": [[1], []],
    }

    view._handle_frontend_event(hover)  # noqa: SLF001
    view._handle_frontend_event(click)  # noqa: SLF001
    view._handle_frontend_event(context)  # noqa: SLF001
    view._handle_frontend_event(action)  # noqa: SLF001
    view._handle_frontend_event(active_selection)  # noqa: SLF001
    view._handle_frontend_event(tool_state)  # noqa: SLF001
    view._handle_frontend_event(measurement)  # noqa: SLF001

    # kind="structure" payloads are enriched with region_tags (empty when no regions defined)
    assert view.get_last_hover_event() == {**hover, "region_tags": []}
    assert view.get_last_click_event() == click
    assert view.get_last_context_event() == {**context, "region_tags": []}
    assert view.get_last_context_action_event() == action
    assert view.get_last_active_selection_event() == active_selection
    assert view.get_last_tool_state_event() == tool_state
    assert view.get_last_measurement_created_event() == {**measurement, "tag": "measurement1"}


def test_hover_and_context_targets_expose_lightweight_public_wrappers():
    view = MolSysView()

    assert view.hover_target.is_empty() is True
    assert view.context_target.is_empty() is True

    hover = {"event": "interaction_hover", "kind": "structure", "atom_indices": [1, 2, 3]}
    context = {
        "event": "interaction_context_menu",
        "kind": "annotation",
        "atom_indices": [4],
        "tag": "note-1",
        "text": "Catalytic",
        "page_x": 10,
        "page_y": 20,
    }

    view._handle_frontend_event(hover)  # noqa: SLF001
    view._handle_frontend_event(context)  # noqa: SLF001

    assert view.hover_target.kind == "structure"
    assert view.hover_target.atom_indices == [1, 2, 3]
    assert view.hover_target.info() == {**hover, "region_tags": []}

    assert view.context_target.kind == "annotation"
    assert view.context_target.atom_indices == [4]
    assert view.context_target.tag == "note-1"
    assert view.context_target.text == "Catalytic"
    assert view.context_target.page_x == 10
    assert view.context_target.page_y == 20
    assert view.context_target.info() == context


def test_shape_targets_and_shape_active_selection_are_exposed_in_python():
    view = MolSysView()

    hover = {"event": "interaction_hover", "kind": "shape", "atom_indices": [8, 9], "tag": "shape-1", "shape_name": "Sphere"}
    context = {
        "event": "interaction_context_menu",
        "kind": "shape",
        "atom_indices": [8, 9],
        "tag": "shape-1",
        "shape_name": "Sphere",
        "page_x": 12,
        "page_y": 24,
    }
    active_selection = {
        "event": "interaction_active_selection_changed",
        "source_kind": "shape",
        "target_level": "shape",
        "element_level": "none",
        "items": [{
            "source_kind": "shape",
            "shape_kind": "sphere",
            "shape_name": "Sphere",
            "tag": "shape-1",
            "atom_indices": [8, 9],
            "group_indices": [],
            "component_indices": [],
            "chain_indices": [],
            "molecule_indices": [],
            "entity_indices": [],
        }],
        "atom_indices": [8, 9],
        "group_indices": [],
        "component_indices": [],
        "chain_indices": [],
        "molecule_indices": [],
        "entity_indices": [],
        "count_atoms": 2,
        "count_groups": 0,
        "count_shapes": 1,
        "count_annotations": 0,
    }

    view._handle_frontend_event(hover)  # noqa: SLF001
    view._handle_frontend_event(context)  # noqa: SLF001
    view._handle_frontend_event(active_selection)  # noqa: SLF001

    assert view.hover_target.kind == "shape"
    assert view.hover_target.tag == "shape-1"
    assert view.hover_target.atom_indices == [8, 9]
    assert view.context_target.kind == "shape"
    assert view.context_target.tag == "shape-1"
    assert view.context_target.page_x == 12
    assert view.context_target.page_y == 24
    assert view.active_selection.source_kind == "shape"
    assert view.active_selection.target_level == "shape"
    assert view.active_selection.is_empty() is False
    assert view.active_selection.info() == active_selection


def test_on_hover_callback_is_called_with_event_dict():
    view = MolSysView()
    received = []

    def handler(ev):
        received.append(ev)

    view.on_hover(handler)

    hover1 = {"event": "interaction_hover", "kind": "structure", "atom_indices": [1]}
    hover2 = {"event": "interaction_hover", "kind": "annotation", "atom_indices": [2], "tag": "ann-1", "text": "X"}
    view._handle_frontend_event(hover1)  # noqa: SLF001
    view._handle_frontend_event(hover2)  # noqa: SLF001

    # hover1 is kind="structure" so region_tags=[] is injected; hover2 is annotation, unchanged
    assert received == [{**hover1, "region_tags": []}, hover2]


def test_on_click_callback_is_called_with_event_dict():
    view = MolSysView()
    received = []

    view.on_click(received.append)

    click = {"event": "interaction_click", "kind": "measurement", "atom_indices": [3, 7], "tag": "m1", "measurement_name": "distance"}
    view._handle_frontend_event(click)  # noqa: SLF001

    assert received == [click]


def test_on_context_callback_is_called_with_event_dict():
    view = MolSysView()
    received = []

    view.on_context(received.append)

    ctx = {"event": "interaction_context_menu", "kind": "annotation", "atom_indices": [5], "tag": "ann-2", "page_x": 10, "page_y": 20}
    view._handle_frontend_event(ctx)  # noqa: SLF001

    assert received == [ctx]


def test_off_hover_removes_callback():
    view = MolSysView()
    received = []

    def handler(ev):
        received.append(ev)

    view.on_hover(handler)
    view.off_hover(handler)

    view._handle_frontend_event({"event": "interaction_hover", "kind": "empty"})  # noqa: SLF001

    assert received == []


def test_on_hover_ignores_duplicate_registration():
    view = MolSysView()
    count = [0]

    def handler(_ev):
        count[0] += 1

    view.on_hover(handler)
    view.on_hover(handler)

    view._handle_frontend_event({"event": "interaction_hover", "kind": "empty"})  # noqa: SLF001

    assert count[0] == 1


def test_region_tags_added_to_structure_payload():
    view = MolSysView()

    # Inject two regions directly into the internal registry
    view._regions["active-site"] = Region(view, "active-site", "all", atom_indices=[10, 11, 12])  # noqa: SLF001
    view._regions["loop-1"] = Region(view, "loop-1", "all", atom_indices=[20, 21])  # noqa: SLF001

    # Pick that overlaps active-site only
    hover = {"event": "interaction_hover", "kind": "structure", "atom_indices": [11, 12]}
    view._handle_frontend_event(hover)  # noqa: SLF001
    assert view.get_last_hover_event()["region_tags"] == ["active-site"]

    # Pick that overlaps both regions
    click = {"event": "interaction_click", "kind": "structure", "atom_indices": [12, 20]}
    view._handle_frontend_event(click)  # noqa: SLF001
    assert set(view.get_last_click_event()["region_tags"]) == {"active-site", "loop-1"}

    # Pick with no region overlap
    ctx = {"event": "interaction_context_menu", "kind": "structure", "atom_indices": [99]}
    view._handle_frontend_event(ctx)  # noqa: SLF001
    assert view.get_last_context_event()["region_tags"] == []

    # Non-structure events are not enriched
    hover_empty = {"event": "interaction_hover", "kind": "empty"}
    view._handle_frontend_event(hover_empty)  # noqa: SLF001
    assert "region_tags" not in view.get_last_hover_event()


def test_region_tags_empty_when_no_regions_defined():
    view = MolSysView()
    hover = {"event": "interaction_hover", "kind": "structure", "atom_indices": [5, 6]}
    view._handle_frontend_event(hover)  # noqa: SLF001
    assert view.get_last_hover_event()["region_tags"] == []


def test_trajectory_frame_rendered_transaction_ack():
    view = MolSysView()
    
    # Send trajectory_frame_rendered event
    event = {"event": "trajectory_frame_rendered", "transaction_id": "tx-999"}
    view._handle_frontend_event(event)  # noqa: SLF001
    
    assert "tx-999" in view._rendered_transactions_acks  # noqa: SLF001
    assert view._last_rendered_transaction == "tx-999"  # noqa: SLF001
    
    # wait_for_transaction returns True immediately if transaction was acknowledged
    success = view.wait_for_transaction("tx-999", timeout_s=0.1)
    assert success is True
    
    # Transaction is cleared from the acks set once consumed
    assert "tx-999" not in view._rendered_transactions_acks  # noqa: SLF001
    
    # wait_for_transaction returns False if transaction was not acknowledged within timeout
    fail = view.wait_for_transaction("tx-nonexistent", timeout_s=0.01)
    assert fail is False

def test_webgl_context_lost_and_restored_toggle_queryable_state():
    view = MolSysView()
    assert view._webgl_context_lost is False  # noqa: SLF001

    view._handle_frontend_event({"event": "webgl_context_lost"})  # noqa: SLF001
    assert view._webgl_context_lost is True  # noqa: SLF001

    view._handle_frontend_event({"event": "webgl_context_restored"})  # noqa: SLF001
    assert view._webgl_context_lost is False  # noqa: SLF001


def test_trajectory_frame_changed_syncs_player_index_and_play_state():
    view = MolSysView()

    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 4, "is_playing": True})  # noqa: SLF001
    assert view.player.index == 4
    assert view.player.is_playing is True
    assert view._player_state["is_playing"] is True  # noqa: SLF001

    view._handle_frontend_event({"event": "trajectory_frame_changed", "frame": 7})  # noqa: SLF001
    assert view.player.index == 7
    assert view.player.is_playing is False
    assert view._player_state["is_playing"] is False  # noqa: SLF001

