from molsysviewer import MolSysView


def test_shape_render_status_is_runtime_only_and_queryable():
    view = MolSysView()
    history_len = len(view._message_history)  # noqa: SLF001
    shape_history_len = len(view._shape_history)  # noqa: SLF001

    event = {
        "event": "shape_render_status",
        "tag": "site",
        "op": "add_sphere_from_atoms",
        "frame": 3,
        "status": "invalid-indices",
        "requested_atoms": 4,
        "used_atoms": 0,
    }
    view._handle_frontend_event(event)  # noqa: SLF001

    assert view.shapes.render_status("site") == event
    assert view.shapes.render_status() == {"site": event}
    assert "shape_render_status" not in view.export_state()
    assert all("render_status" not in record for record in view._shape_summary_records())  # noqa: SLF001
    assert len(view._message_history) == history_len  # noqa: SLF001
    assert len(view._shape_history) == shape_history_len  # noqa: SLF001


def test_shape_render_status_is_cleared_when_shape_is_unregistered():
    view = MolSysView()
    view._shape_render_status["site"] = {"event": "shape_render_status", "tag": "site"}  # noqa: SLF001
    view._scene_objects[("shape", "site")] = object()  # noqa: SLF001

    view._unregister_scene_object("shape", "site")  # noqa: SLF001

    assert view.shapes.render_status("site") is None
