"""Qt keeps control messages JSON and refuses AnyWidget-style buffers.

Qt is in scope for 1.0, but a green AnyWidget transport does not imply Qt: the
control bridge carries JSON while structural binary payloads use a separate Qt
payload-scheme path. What must hold is that passing AnyWidget-style ``buffers``
to the control channel fails loudly instead of dropping them.
"""

from pathlib import Path

import pytest
from molsysviewer.standalone_qt.view_channel import QtViewChannel


class _FakeBridge:
    def __init__(self):
        self.sent = []
        self.event_sink = None

    def send(self, msg):
        self.sent.append(msg)


def _channel():
    channel = QtViewChannel.__new__(QtViewChannel)
    channel._bridge = _FakeBridge()  # noqa: SLF001
    return channel


def test_the_anywidget_buffer_path_cannot_reach_qt_by_construction():
    # Negotiation follows an explicit transport capability; Qt's control
    # channel remains JSON-only even though remote WebSockets can carry buffers.
    assert QtViewChannel.supports_array_native_buffers is False


def test_qt_refuses_buffers_instead_of_dropping_them():
    channel = _channel()
    with pytest.raises(NotImplementedError, match="does not carry AnyWidget-style buffers"):
        channel.send({"op": "structure_data_chunk"}, buffers=[memoryview(b"xyz")])
    assert channel._bridge.sent == [], "nothing may reach the frontend"  # noqa: SLF001


def test_qt_still_carries_ordinary_control_messages():
    channel = _channel()
    channel.send({"op": "set_region_summaries", "regions": []})
    channel.send({"op": "load_molsys_payload"}, buffers=None)
    channel.send({"op": "clear_all"}, buffers=[])
    assert [m["op"] for m in channel._bridge.sent] == [  # noqa: SLF001
        "set_region_summaries",
        "load_molsys_payload",
        "clear_all",
    ]


def test_qt_messages_are_not_enveloped():
    """The connector owns its wire format: enveloping lives in the AnyWidget
    widget, so Qt must receive the domain message unchanged."""
    channel = _channel()
    domain = {"op": "set_whole_representation", "representation": "cartoon"}
    channel.send(domain)
    delivered = channel._bridge.sent[0]  # noqa: SLF001
    assert delivered == domain
    assert "protocolVersion" not in delivered
    assert "direction" not in delivered


def _bridge_with_view(view):
    """A QtMessageBridge wired to a real view, without Qt objects."""
    from molsysviewer.standalone_qt.utils import QtMessageBridge

    bridge = QtMessageBridge.__new__(QtMessageBridge)
    bridge.payloads = {}
    bridge.binary_payload_ids = set()
    bridge.payload_ref_threshold_bytes = 1  # anything qualifies
    bridge.view = view
    return bridge


def test_a_large_load_becomes_an_array_native_reference_served_as_bytes():
    """D4-Qt: the same scheme handler carries raw arrays, not JSON text."""
    import molsysmt as msm

    from molsysviewer import MolSysView

    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    bridge = _bridge_with_view(view)

    message = {
        "id": "load-1",
        "op": "load_molsys_payload",
        "payload": {"atoms": {"atom_id": [1]}, "structures": [{"coordinates": [[0, 0, 0]]}]},
    }
    payload_id = bridge._materialize_payload_ref(message)  # noqa: SLF001

    assert payload_id == "load-1"
    # The message now points at the blob and carries the topology inline.
    assert message["op"] == "load_molsys_array_payload_ref"
    assert message["ref"]["content_type"] == "application/octet-stream"
    assert message["ref"]["url"].startswith("molsysviewer-payload://payload/")
    assert "payload" not in message, "the JSON payload must not travel as well"
    assert message["metadata"]["n_atoms"] == view.molsys.get_n_atoms()

    # The blob is exactly the descriptors' bytes, concatenated in order.
    blob = bridge.payloads[payload_id]
    assert payload_id in bridge.binary_payload_ids
    expected = sum(d["byte_length"] for d in message["metadata"]["structural_arrays"])
    assert len(blob) == expected


def test_the_scheme_handler_serves_binary_and_json_by_id():
    from molsysviewer.standalone_qt.utils import _make_payload_scheme_handler

    replies = []

    class _FakeJob:
        def __init__(self, path):
            self._path = path

        def requestUrl(self):
            return type("U", (), {"path": lambda _self: self._path})()

        def reply(self, content_type, _buffer):
            replies.append(bytes(content_type))

    class _FakeHandlerBase:
        def __init__(self, *_a, **_k):
            pass

    class _FakeBuffer:
        # `OpenModeFlag` is read off the class, as PySide6 exposes it.
        OpenModeFlag = type("F", (), {"ReadOnly": 1})

        def __init__(self, *_a):
            pass

        def setData(self, *_a):
            pass

        def open(self, *_a):
            pass

    handler = _make_payload_scheme_handler(
        _FakeHandlerBase,
        _FakeBuffer,
        bytes,
        {"json-1": b"{}", "bin-1": b"\x00\x01"},
        binary_payload_ids={"bin-1"},
    )
    handler.requestStarted(_FakeJob("/json-1"))
    handler.requestStarted(_FakeJob("/bin-1"))
    assert replies == [b"application/json", b"application/octet-stream"]


# --- R3: the two connectors must not fork the protocol ---------------------

def test_both_connectors_classify_from_the_same_manifest():
    """Qt had a hardcoded set of transport events; now it reads the manifest.

    A hardcoded list is how the two connectors drift: an action added to the
    manifest would stay unknown to Qt, and one added to Qt's set would be
    invisible to the shared contract.
    """
    from molsysviewer.runtime_contract import QT_TRANSPORT_ACTIONS
    from molsysviewer.standalone_qt import utils

    source = (Path(utils.__file__)).read_text(encoding="utf-8")
    assert "QT_TRANSPORT_ACTIONS" in source
    # The old hardcoded literal must not come back.
    assert '{"message_ack", "message_error", "structure_ready", "render_ready"}' not in source
    assert {"message_ack", "message_error", "structure_ready", "render_ready"} <= QT_TRANSPORT_ACTIONS


def test_an_unknown_action_is_observable_and_refused_on_qt_as_on_anywidget():
    """The fork R3 closes: same event, silently ignored on one side only.

    Before: AnyWidget rejected an unknown action observably, Qt forwarded it and
    the handler ignored it without a trace. The handler ignores it either way,
    so what had to match was the *visibility*.
    """
    from molsysviewer.standalone_qt import utils

    bridge = utils.QtMessageBridge.__new__(utils.QtMessageBridge)
    bridge.ready = True
    forwarded: list = []
    bridge._forward_to_view = forwarded.append  # noqa: SLF001

    signalled: list = []
    original = utils.emit_suppressed_exception
    utils.emit_suppressed_exception = lambda *a, **k: signalled.append(a[0])
    try:
        assert bridge.handle_frontend_event({"event": "totally_unknown_event"}) is False
    finally:
        utils.emit_suppressed_exception = original

    assert signalled, "an unknown action must leave a trace on Qt too"
    assert "unknown_frontend_action" in signalled[0]
    assert forwarded == []


def test_the_explicit_qt_payload_probe_reaches_the_test_sink_without_weakening_product_actions():
    from molsysviewer.standalone_qt import utils

    bridge = utils.QtMessageBridge.__new__(utils.QtMessageBridge)
    bridge.ready = True
    forwarded: list = []
    bridge._forward_to_view = forwarded.append  # noqa: SLF001

    assert bridge.handle_frontend_event({"event": "qt_payload_probe", "atoms": 2}) is True
    assert forwarded == [{"event": "qt_payload_probe", "atoms": 2}]


def test_a_known_product_event_stays_silent_and_reaches_the_view():
    from molsysviewer.standalone_qt import utils

    bridge = utils.QtMessageBridge.__new__(utils.QtMessageBridge)
    bridge.ready = True
    forwarded: list = []
    bridge._forward_to_view = forwarded.append  # noqa: SLF001

    signalled: list = []
    original = utils.emit_suppressed_exception
    utils.emit_suppressed_exception = lambda *a, **k: signalled.append(a[0])
    try:
        bridge.handle_frontend_event({"event": "interaction_hover", "kind": "empty"})
    finally:
        utils.emit_suppressed_exception = original

    assert not signalled, "a manifest-known event must not be reported as unknown"
    assert [e["event"] for e in forwarded] == ["interaction_hover"]


class _RecordingWebView:
    """A web view that records deliveries without answering them.

    Nothing acknowledges here on purpose: the question these tests ask is what
    the bridge does *while* a message is outstanding.
    """

    def __init__(self) -> None:
        self.delivered: list[str] = []
        self._page = self

    def page(self):
        return self._page

    def runJavaScript(self, script, callback=None):  # noqa: N802 - Qt's name
        self.delivered.append(script)
        if callback is not None:
            callback("molsysviewer-message-accepted")


class _NoTimer:
    """QTimer stand-in: the bridge only ever arms timeouts with it."""

    @staticmethod
    def singleShot(_ms, _fn):  # noqa: N802 - Qt's name
        return None


def _ready_bridge():
    from molsysviewer.standalone_qt.utils import QtMessageBridge

    webview = _RecordingWebView()
    bridge = QtMessageBridge(webview, _NoTimer)
    bridge.ready = True
    return bridge, webview


def _acknowledge(bridge, *, event: str | None = None) -> None:
    entry = bridge.inflight
    assert entry is not None, "nothing was in flight to acknowledge"
    bridge.handle_frontend_event({
        "event": event or entry["wait_event"],
        "id": entry["id"],
        "generation": entry["generation"],
    })


def test_qt_delivers_one_message_at_a_time_and_waits_for_it_to_be_handled():
    """This is where Qt's ordering guarantee actually lives.

    S8 — a scene op reaching a frontend that has no structure yet — is solved on
    the AnyWidget seam by deferring in `_send_widget_message`, gated on the
    array-native transfer manager. **That gate never opens for Qt**: the binary
    path is `isinstance(self.widget, MolSysViewerWidget)`, and the Qt channel
    refuses buffers outright. So nothing defers on the Python side here.

    Nothing needs to, because the bridge is stricter: one message in flight, and
    the next is not even delivered until the frontend reports the current one
    *handled*. The page emits `message_ack` after `await
    controller.handleMessage(msg)` returns, so the acknowledgement means
    completed, not received.

    Pinned because it is a guarantee by construction that nothing states and
    nothing tested. `qt-delivery-ordering.probe.ts` shows what a fire-and-forget
    bridge would cost: with two unawaited deliveries against a real page, the
    region survives (the state handler queues ops until the structure loads) and
    the annotation and the measurement are **silently lost**.
    """
    bridge, webview = _ready_bridge()

    bridge.send({"op": "load_molsys_payload", "payload": {"atoms": {}, "structures": []}})
    bridge.send({"op": "add_label", "tag": "late", "options": {"tag": "late"}})

    assert len(webview.delivered) == 1, "the second message was delivered before the first was handled"
    assert bridge.inflight is not None
    assert len(bridge.queue) == 1

    _acknowledge(bridge)

    assert len(webview.delivered) == 2, "the queued message was not released by the acknowledgement"
    assert "add_label" in webview.delivered[1]


def test_a_load_waits_for_the_structure_and_not_merely_for_the_message():
    """`message_ack` is not enough after a load: the structure has to exist.

    A load resolves when the browser has built the structure, which is later
    than when the handler was entered. The bridge therefore waits for a
    different event for loads than for everything else, and 30 s rather than 5.
    """
    bridge, webview = _ready_bridge()

    bridge.send({"op": "load_molsys_payload", "payload": {"atoms": {}, "structures": []}})
    assert bridge.inflight["wait_event"] == "structure_ready"
    assert bridge.inflight["timeout_s"] == 30.0

    # The wrong acknowledgement must not release the queue.
    bridge.send({"op": "add_label", "tag": "late", "options": {"tag": "late"}})
    _acknowledge(bridge, event="message_ack")
    assert len(webview.delivered) == 1, "a load was released by a plain message_ack"

    _acknowledge(bridge, event="structure_ready")
    assert len(webview.delivered) == 2

    assert bridge.inflight["wait_event"] == "message_ack"
    assert bridge.inflight["timeout_s"] == 5.0
