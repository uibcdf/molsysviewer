"""Owned cleanup survives errors from actual provider and transport hooks."""

import pytest
from ipywidgets.widgets.widget import _instances
from molsysviewer.widget import MolSysViewerWidget

import molsysviewer as msv
from molsysviewer import AddonPanelSpec, AddonPanelWidget, AddonSpec, addons


class ClosePanel(AddonPanelWidget):
    _esm = "export function render() {}"
    fail = False
    closes = 0
    needs_owner = False

    def close(self):
        self.closes += 1
        if self.fail:
            raise OSError("controlled provider close failure")
        if self.needs_owner and self._view is None:
            raise RuntimeError("provider retry lost its cleanup context")
        return super().close()


class DetachWidget(MolSysViewerWidget):
    fail = False

    def on_msg(self, callback, remove=False):
        if remove and self.fail:
            raise OSError("controlled transport detach failure")
        return super().on_msg(callback, remove=remove)


@pytest.fixture
def views():
    addons.register(
        AddonSpec(
            name="close-receiving",
            panels=(AddonPanelSpec(id="panel", title="Cleanup receiving", widget_class=f"{__name__}.ClosePanel"),),
        )
    )
    widget = DetachWidget()
    with msv.demo["dialanine"] as seed:
        view = msv.new_view(seed.molsys, view=msv.MolSysView(transport=widget))
        witness = msv.new_view(seed.molsys)
    view.addons.enable("close-receiving")
    view._endpoint_transfers.register("receiving-popup", "canvas")
    for endpoint in (None, "receiving-popup"):
        view._handle_frontend_event(
            {"event": "panel_navigate", "addon": "close-receiving", "panel": "panel", "_panel_endpoint_id": endpoint}
        )
    panels = [entry[2] for entry in view._active_panel_widgets.values()]
    owned = [widget, widget.layout, *(item for panel in panels for item in (panel, panel.layout))]
    yield view, witness, panels, {id(item): item.model_id for item in owned}
    widget.fail = False
    for panel in panels:
        panel.fail = False
        panel.needs_owner = False
        panel.close()
        panel.layout.close()
        panel._view = None
    view._close_callbacks.clear()
    # Failed pre-fix closes intentionally remain registered before this cleanup.
    view.widget.close()
    view.widget.layout.close()
    view.close()
    witness.close()
    addons.unregister("close-receiving")


def test_provider_error_releases_other_resources_and_retry_only_retries_failure(views):
    view, witness, panels, ids = views
    witness_state = witness.export_state()
    transfers = []
    for endpoint in (None, "receiving-popup"):
        manager = view._structure_transfer_manager(endpoint, create=endpoint is not None)
        transfers.append(
            manager.start(
                begin_message={"op": "structure_data_begin", "chunk_count": 1},
                chunks=[({"op": "structure_data_chunk", "chunk_id": 0}, [memoryview(b"coordinates")])],
                fallback_factory=lambda _generation: {"op": "load_molsys_payload"},
                payload=view.molsys,
                target_endpoint_id=endpoint,
            )
        )
    panels[0].fail = True
    panels[0].needs_owner = True
    with pytest.raises(OSError, match="controlled provider close failure"):
        view.close()
    assert view.closed
    assert not witness.closed
    assert witness.export_state() == witness_state
    assert not view._active_panel_widgets
    assert all(panel._view is None for panel in panels)
    assert ids[id(panels[0])] in _instances
    assert all(key not in _instances for obj, key in ids.items() if obj != id(panels[0]))
    assert [panel.closes for panel in panels] == [1, 1]
    assert all(transfer.release_count == 1 and transfer.payload is None for transfer in transfers)
    assert view._endpoint_transfers.popup_count == 0
    assert not view._endpoint_transfers.modes
    panels[0].fail = False
    view.close()
    assert [panel.closes for panel in panels] == [2, 1]
    assert all(key not in _instances for key in ids.values())
    view.close()
    assert [panel.closes for panel in panels] == [2, 1]


def test_transport_detach_failure_does_not_prevent_widget_layout_or_panel_close(views):
    view, witness, panels, ids = views
    view.widget.fail = True
    with pytest.raises(OSError, match="controlled transport detach failure"):
        view.close()
    assert all(key not in _instances for key in ids.values())
    assert all(panel._view is None for panel in panels)
    assert not witness.closed
    previous_click = view.get_last_click_event()
    view._widget_message_callback(
        view.widget, {"event": "interaction_click", "kind": "structure", "atom_indices": [1]}, []
    )
    assert view.get_last_click_event() == previous_click
    view.widget.fail = False
    view.close()
    assert view._widget_message_callback is None
    assert not view.widget._msg_callbacks.callbacks


def test_callback_failure_retries_without_repeating_successful_callbacks(views):
    view, _, _, ids = views
    events = []
    fail = True

    def callback():
        events.append("retry")
        if fail:
            raise OSError("controlled callback failure")

    view._close_callbacks.extend([callback, lambda: events.append("once")])
    with pytest.raises(OSError, match="controlled callback failure"):
        view.close()
    assert events == ["retry", "once"]
    assert all(key not in _instances for key in ids.values())
    fail = False
    view.close()
    assert events == ["retry", "once", "retry"]


def test_multiple_close_failures_remain_observable(views):
    view, _, panels, ids = views
    panels[0].fail = True
    view.widget.fail = True
    with pytest.raises(ExceptionGroup) as caught:
        view.close()
    assert {str(error) for error in caught.value.exceptions} == {
        "controlled provider close failure",
        "controlled transport detach failure",
    }
    assert all(key not in _instances for obj, key in ids.items() if obj != id(panels[0]))
    panels[0].fail = False
    view.widget.fail = False
    view.close()
    assert all(key not in _instances for key in ids.values())


def test_reentrant_close_does_not_repeat_cleanup(views):
    view, _, panels, ids = views
    view._close_callbacks.append(view.close)
    view.close()
    assert all(key not in _instances for key in ids.values())
    assert [panel.closes for panel in panels] == [1, 1]


def test_interruption_remains_observable_after_independent_cleanup(views):
    view, _, _, ids = views
    fail = True

    def interrupt():
        if fail:
            raise KeyboardInterrupt("controlled close interruption")

    view._close_callbacks.append(interrupt)
    with pytest.raises(KeyboardInterrupt, match="controlled close interruption"):
        view.close()
    assert view.closed
    assert all(key not in _instances for key in ids.values())
    fail = False
    view.close()


def test_source_close_attempts_other_unpresented_results_after_one_child_failure(views):
    source, _, _, _ = views
    service = source.addons.manager.presentations
    first = service.get(service.prepare(lambda child: msv.new_view(source.molsys, view=child)))
    second = service.get(service.prepare(lambda child: msv.new_view(source.molsys, view=child)))
    fail = True

    def failing_child_callback():
        if fail:
            raise OSError("controlled result close failure")

    first._close_callbacks.append(failing_child_callback)
    try:
        with pytest.raises(OSError, match="controlled result close failure"):
            source.close()
        assert first.closed and second.closed
        assert first.widget.comm is None
        assert second.widget.comm is None
    finally:
        fail = False
        source.close()
    assert not first._close_actions
    assert service.records() == []
