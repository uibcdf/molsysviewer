"""Independent windows own addon widgets while sharing the scientific scene."""

import pytest
from molsysviewer.addons import AddonPanelSpec, AddonPanelWidget, AddonSpec
from molsysviewer.remote import RemoteViewChannel

from molsysviewer import MolSysView, addons


class EndpointPanel(AddonPanelWidget):
    _esm = "export function render() {}"

    def on_mount(self, view, *, skip_digestion=False):
        self.push_state({"initial": True})

    def handle_action(self, view, action_id, payload, *, skip_digestion=False):
        if action_id == "render":
            view.shapes.add_sphere(center="[0,0,0] nm", radius="0.3 nm", tag=payload["tag"])


@pytest.fixture
def panel_view():
    addons.register(
        AddonSpec(
            name="endpoint-review",
            panels=tuple(
                AddonPanelSpec(id=key, title=key, widget_class=f"{__name__}.EndpointPanel") for key in ("one", "two")
            ),
        )
    )
    view = MolSysView()
    view.addons.enable("endpoint-review")
    view._endpoint_transfers.register("canvas-peer", "canvas")
    view._endpoint_transfers.register("panel-peer", "panel")
    yield view
    view.close()
    addons.unregister("endpoint-review")


def event(view, kind, endpoint=None, panel="one", **extra):
    view._handle_frontend_event(
        {"event": kind, "addon": "endpoint-review", "panel": panel, "_panel_endpoint_id": endpoint, **extra}
    )


def test_navigation_and_close_preserve_other_windows(panel_view):
    from ipywidgets.widgets.widget import _instances

    view = panel_view
    for endpoint in (None, "canvas-peer", "panel-peer"):
        event(view, "panel_navigate", endpoint)
    owned = dict(view._active_panel_widgets)
    assert len({id(entry[2]) for entry in owned.values()}) == 3

    event(view, "panel_navigate", panel="two")
    assert owned[None][2]._view is None
    assert view._active_panel_widgets["canvas-peer"] == owned["canvas-peer"]
    event(view, "panel_unmount", panel="one")  # delayed unmount of old host panel
    assert view._active_panel_widget[:2] == ("endpoint-review", "two")

    view._handle_frontend_event({"event": "popup_endpoint_closed", "popup_endpoint_id": "panel-peer"})
    assert owned["panel-peer"][2]._view is None
    event(
        view,
        "addon_panel_action",
        "canvas-peer",
        content={"type": "action", "id": "render", "payload": {"tag": "peer-shape"}},
    )
    assert view.shapes.contains("peer-shape")
    event(view, "panel_navigate", "panel-peer")  # late event cannot recreate a closed popup
    assert "panel-peer" not in view._active_panel_widgets

    remaining = [entry[2] for entry in view._active_panel_widgets.values()]
    registered = [identifier for widget in remaining for identifier in (widget.model_id, widget.layout.model_id)]
    view.close()
    assert not view._active_panel_widgets
    assert all(widget._view is None for widget in remaining)
    assert all(identifier not in _instances for identifier in registered)


def test_actions_require_the_endpoint_and_panel_owner(panel_view):
    view = panel_view
    event(view, "panel_navigate", "canvas-peer")
    action = {"type": "action", "id": "render", "payload": {"tag": "wrong-owner"}}
    event(view, "addon_panel_action", content=action)
    event(view, "addon_panel_action", "canvas-peer", panel="two", content=action)
    assert not view.shapes.contains("wrong-owner")
    event(view, "addon_panel_action", "canvas-peer", content=action)
    assert view.shapes.contains("wrong-owner")


@pytest.mark.parametrize("endpoint", [None, "canvas-peer", "panel-peer"])
def test_initial_state_follows_mount_and_is_addressed_to_its_owner(panel_view, endpoint):
    view = panel_view
    sent = []
    view.widget.send = lambda message, buffers=None: sent.append(message)
    view._ready = True
    event(view, "panel_navigate", endpoint)
    # Runtime-only deliveries use the widget transport, without persistence.
    messages = [message for message in sent if message.get("op") in {"mount_addon_panel", "addon_panel_message"}]
    assert [message["op"] for message in messages] == [
        "mount_addon_panel",
        "addon_panel_message",
        "addon_panel_message",
    ]
    owner = f"widget-host:{view._binary_session_id}" if endpoint is None else endpoint
    assert all(message["target_endpoint_id"] == owner for message in messages)
    assert messages[1]["content"] == {"type": "state", "state": {"initial": True}}


def test_primary_widget_emissions_remain_local_with_other_mounted_windows(panel_view):
    view = panel_view
    sent = []
    view.widget.send = lambda message, buffers=None: sent.append(message)
    view._ready = True
    event(view, "panel_navigate")
    primary = view._active_panel_widgets[None][2]
    event(view, "panel_navigate", "canvas-peer")
    peer = view._active_panel_widgets["canvas-peer"][2]
    assert primary is not peer

    sent.clear()
    primary.push_state({"primary": True})
    assert sent == [
        {
            "op": "addon_panel_message",
            "addon": "endpoint-review",
            "panel": "one",
            "target_endpoint_id": f"widget-host:{view._binary_session_id}",
            "content": {"type": "state", "state": {"primary": True}},
        }
    ]
    sent.clear()
    peer.push_state({"peer": True})
    assert len(sent) == 1
    assert sent[0]["target_endpoint_id"] == "canvas-peer"
    assert sent[0]["content"] == {"type": "state", "state": {"peer": True}}


def test_primary_addon_uses_the_remote_connectors_default_route(panel_view):
    # The real connector/router owns its recipient identity and has no widget-host
    # endpoint. A payload must not invent one inside its valid remote envelope.
    del panel_view  # The fixture owns registration of the real test panel type.
    sent = []
    channel = RemoteViewChannel(sent.append, render_on="client")
    with MolSysView(transport=channel) as view:
        endpoint = "browser-client:owner"
        channel.router.register_endpoint(
            endpoint,
            "browser-client",
            {"command-origin", "input-send", "workbench", "render", "structure-receive"},
            actor_id=endpoint,
            actor_kind="human",
        )
        view.addons.enable("endpoint-review")
        view._ready = True
        event(view, "panel_navigate")
        messages = [item for item in sent if item["action"] in {"mount_addon_panel", "addon_panel_message"}]
        assert [item["action"] for item in messages] == [
            "mount_addon_panel",
            "addon_panel_message",
            "addon_panel_message",
        ]
        assert channel.router.projection_endpoint_ids() == (endpoint,)
        assert all("targetEndpointId" not in item for item in messages)
        assert all("target_endpoint_id" not in item["payload"] for item in messages)
        assert messages[1]["payload"]["content"] == {"type": "state", "state": {"initial": True}}


def test_late_retired_widget_messages_do_not_reach_its_replacement(panel_view):
    view = panel_view
    sent = []
    view.widget.send = lambda message, buffers=None: sent.append(message)
    view._ready = True
    event(view, "panel_navigate", "canvas-peer")
    retired = view._active_panel_widgets["canvas-peer"][2]
    event(view, "panel_navigate", "canvas-peer", panel="two")
    sent.clear()
    retired.push_state({"late": True})
    assert sent == []
    current = view._active_panel_widgets["canvas-peer"][2]
    current.push_state({"current": True})
    assert sent[-1]["content"] == {"type": "state", "state": {"current": True}}
