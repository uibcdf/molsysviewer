"""Declared scientific readers retain endpoint ownership and scene guards."""

import molsysmt as msm
import pytest
from molsysviewer._private.argdigest import digest
from molsysviewer.system_edits import SystemEditPendingError

import molsysviewer as msv
from molsysviewer import AddonPanelSpec, AddonPanelWidget, AddonSpec, addons
from tests.test_addon_panel_pending_state import defer_box


class ReaderPanel(AddonPanelWidget):
    read_only_actions = ("inspect",)

    def __init__(self, view=None, **kwargs):
        super().__init__(view=view, **kwargs)
        self.reads = []

    @digest()
    def handle_action(self, view, action_id, payload, *, skip_digestion=False):
        if payload.get("scene"):
            view.shapes.add_sphere(center="[0,0,0] nm", skip_digestion=True)
        elif payload.get("recursive"):
            self.handle_action(view, "write", {}, skip_digestion=True)
        else:
            count = view.addons.manager.system_edits.read(
                lambda target: msm.get(target, element="system", n_atoms=True)
            )
            self.reads.append(count)
            self.push_state({"atoms": count})


@pytest.fixture
def case():
    name = "readonly-receiving"
    addons.register(
        AddonSpec(
            name=name, panels=(AddonPanelSpec(id="report", title="Report", widget_class=f"{__name__}.ReaderPanel"),)
        )
    )
    with msv.demo["dialanine"] as view:
        view.addons.enable(name)
        view._endpoint_transfers.register("peer", "panel")
        for endpoint in (None, "peer"):
            view._handle_frontend_event(
                {"event": "panel_navigate", "addon": name, "panel": "report", "_panel_endpoint_id": endpoint}
            )
        yield view
    addons.unregister(name)


def send(view, endpoint=None, **changes):
    event = {
        "event": "addon_panel_action",
        "addon": "readonly-receiving",
        "panel": "report",
        "_panel_endpoint_id": endpoint,
        "content": {"type": "action", "id": "inspect", "payload": {}},
    }
    event.update(changes)
    view._handle_frontend_event(event)


@pytest.mark.parametrize("endpoint", [None, "peer"])
@pytest.mark.parametrize("state", ["pending", "sync_failed"])
def test_declared_reader_uses_current_primary_without_projecting_or_changing_pending(case, endpoint, state):
    defer_box(case)
    case.addons.manager.system_edits._state = state
    before = case.addons.manager.system_edits.get_status()
    send(case, endpoint)
    assert case._active_panel_widgets[endpoint][2].reads == [22]
    assert case.addons.manager.system_edits.get_status() == before


@pytest.mark.parametrize(
    "changes",
    [
        {"addon": "foreign"},
        {"panel": "foreign"},
        {"_panel_endpoint_id": "closed-peer"},
        {"_panel_endpoint_id": []},
        {"content": {"type": "query", "id": "viewer.context"}},
        {"content": {"type": "action", "id": "write", "payload": {}}},
        {"content": {"type": "action", "id": "inspect", "payload": []}},
        {"content": {"type": "present_view", "id": "inspect"}},
    ],
)
def test_pending_requests_require_exact_declared_type_and_mounted_endpoint_owner(case, changes):
    defer_box(case)
    send(case, **changes)
    assert all(not entry[2].reads for entry in case._active_panel_widgets.values())


@pytest.mark.parametrize("payload", [{"scene": True}, {"recursive": True}])
def test_reader_admission_does_not_grant_nested_scene_or_other_handler_privilege(case, payload):
    defer_box(case)
    with pytest.raises(SystemEditPendingError):
        send(case, content={"type": "action", "id": "inspect", "payload": payload})
    assert not case._active_panel_widgets[None][2].reads
    panel = case._active_panel_widgets[None][2]
    with pytest.raises(SystemEditPendingError):
        panel.handle_action(case, "inspect", {}, skip_digestion=True)
    send(case)
    assert panel.reads == [22]


def test_direct_widget_transport_has_the_same_read_only_classification(case):
    panel = case._active_panel_widgets[None][2]
    defer_box(case)
    panel._route_frontend_message(panel, {"type": "action", "id": "write"}, [])
    assert not panel.reads
    panel._route_frontend_message(panel, {"type": "action", "id": "inspect"}, [])
    assert panel.reads == [22]


def test_unmounted_and_closed_endpoint_requests_cannot_recreate_a_reader(case):
    old = case._active_panel_widgets["peer"][2]
    case._handle_frontend_event({"event": "popup_endpoint_closed", "popup_endpoint_id": "peer"})
    defer_box(case)
    send(case, "peer")
    old._route_frontend_message(old, {"type": "action", "id": "inspect"}, [])
    assert not old.reads and "peer" not in case._active_panel_widgets


@pytest.mark.parametrize("state", ["editing", "syncing", "uncertain"])
def test_transient_or_uncertain_states_do_not_admit_declared_readers(case, state):
    # Exercise the host state classifier; no scientific result is manufactured.
    manager = case.addons.manager.system_edits
    manager._state = state
    try:
        send(case)
        assert not case._active_panel_widgets[None][2].reads
    finally:
        manager._state = "synchronized"


def test_default_admission_is_empty_and_invalid_declarations_fail_before_use():
    assert AddonPanelWidget.read_only_actions == ()

    class InvalidPanel(AddonPanelWidget):
        read_only_actions = "inspect"

    with pytest.raises(ValueError, match="tuple/list"):
        InvalidPanel()


@pytest.mark.parametrize("endpoint", [None, "peer"])
def test_mount_delivers_server_owned_reader_declaration_to_its_exact_endpoint(case, endpoint):
    sent = []
    case.widget.send = lambda message, buffers=None: sent.append(message)
    case._ready = True
    case._mount_addon_panel("readonly-receiving", "report", endpoint_id=endpoint)
    mount = next(message for message in sent if message.get("op") == "mount_addon_panel")
    assert mount["read_only_actions"] == ["inspect"]
    assert mount.get("target_endpoint_id") == endpoint
    assert case._active_panel_widgets[endpoint][2].read_only_actions == ("inspect",)
