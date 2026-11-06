"""Addon metadata remains deliverable while molecular scene actions are paused."""

from threading import Event, Thread

import molsysmt as msm
import numpy as np
import pytest
from molsysviewer._private.argdigest import digest
from molsysviewer.system_edits import SystemEditPendingError

import molsysviewer as msv
from molsysviewer import AddonPanelWidget


class StatusPanel(AddonPanelWidget):
    pass


class OverriddenPanel(AddonPanelWidget):
    @digest()
    def push_state(self, state, *, skip_digestion=False):
        raise AssertionError("An override must not acquire the host metadata exemption")


@pytest.fixture
def panel():
    with msv.demo["dialanine"] as view:
        widget = StatusPanel(view=view)
        widget._addon_name = "status-probe"
        messages = []
        widget.send = lambda message, buffers=None: messages.append(message)
        yield view, widget, messages
        widget.close()
        widget.layout.close()


def defer_box(view):
    box = msm.pyunitwizard.quantity((2 * np.eye(3))[None], "nm")
    view.addons.manager.system_edits.execute(
        lambda target: {"run": lambda: msm.set(target, box=box), "changed": True},
        name="metadata-receiving.box",
        update_view=False,
    )


def test_inherited_metadata_transport_survives_pending_state(panel):
    view, widget, messages = panel
    defer_box(view)
    status = view.addons.manager.system_edits.get_status()
    widget.set_state({"draft": "kept"})
    widget.push_state({"stage": "sync_required"})
    assert widget.state == {"draft": "kept"}
    assert messages == [{"type": "state", "state": {"stage": "sync_required"}}]
    assert view.addons.manager.system_edits.get_status() == status
    with pytest.raises(SystemEditPendingError):
        view.shapes.add_sphere(center="[0, 0, 0] nm")


def test_metadata_does_not_need_a_foreign_molecular_read_lock(panel):
    view, widget, messages = panel
    entered, release = Event(), Event()
    errors = []

    def hold():
        try:

            def read(target):
                entered.set()
                assert release.wait(10)

            view.addons.manager.system_edits.read(read)
        except BaseException as exc:
            errors.append(exc)

    worker = Thread(target=hold)
    worker.start()
    assert entered.wait(10)
    try:
        widget.set_state({"draft": "independent metadata"})
        widget.push_state({"stage": "busy"})
        assert messages[-1]["state"]["stage"] == "busy"
    finally:
        release.set()
        worker.join(10)
    assert not worker.is_alive() and not errors


def test_same_named_override_does_not_bypass_scene_pause(panel):
    view, _, _ = panel
    defer_box(view)
    overridden = OverriddenPanel(view=view)
    try:
        with pytest.raises(SystemEditPendingError):
            overridden.push_state({"anything": True})
    finally:
        overridden.close()
        overridden.layout.close()
