"""Qt keeps control messages JSON and refuses AnyWidget-style buffers.

Qt remains an experimental host for 1.0. Its control bridge carries JSON while
structural binary payloads use a separate Qt payload-scheme path. Passing
AnyWidget-style ``buffers`` to the control channel must fail loudly instead of
dropping them.
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


def _live_view(source, *, version=1, threshold=1):
    from molsysviewer.standalone_qt.utils import QtMessageBridge

    from molsysviewer import MolSysView

    # A real connector held before page readiness: inspect its queued wire data
    # without importing Qt or pretending that a browser acknowledged it.
    bridge = QtMessageBridge(None, None)
    bridge.payload_ref_threshold_bytes = threshold
    view = MolSysView(transport=QtViewChannel(bridge))
    view.load(source, structure_indices=[8, 0, 3])
    view._handle_frontend_event({"event": "ready", "capabilities": {"array_native_molsys_ref": [version]}})
    return view, bridge


def test_a_canonical_live_load_uses_numeric_scheme_bytes_without_json():
    import numpy as np
    from molsysviewer._pyunitwizard import puw

    from molsysviewer import demo

    with demo["pentalanine"] as source:
        view, bridge = _live_view(source.molsys)
        try:
            assert not view._current_molecular_projection.is_materialized
            entry = next(x for x in bridge.queue if x["message"]["op"] == "load_molsys_array_payload_ref")
            message = entry["message"]
            assert message["metadata"]["n_atoms"] == 62
            assert message["metadata"]["n_structures"] == 3
            assert entry["wait_event"] == "structure_ready"
            assert entry["timeout_s"] == 30
            assert entry["payload_id"] in bridge.binary_payload_ids
            blob = bridge.payloads[entry["payload_id"]]
            offset = 0
            for descriptor in message["metadata"]["structural_arrays"]:
                stop = offset + descriptor["byte_length"]
                actual = np.frombuffer(blob[offset:stop], dtype=descriptor["dtype"]).reshape(descriptor["shape"])
                field = descriptor["kind"]
                values = getattr(source.molsys.structures, field)[[8, 0, 3]]
                expected = puw.get_value(values, to_unit="ps" if field == "time" else "angstroms")
                if field == "coordinates":
                    expected = expected.transpose(0, 2, 1)
                np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)
                offset = stop
            assert offset == len(blob)
            bridge.begin_generation()
            assert not bridge.payloads and not bridge.binary_payload_ids
        finally:
            view.close()


@pytest.mark.parametrize("version, threshold", [(999, 1), (1, 10**12)])
def test_unsupported_reference_or_small_load_retains_json_fallback(version, threshold):
    from molsysviewer import demo

    with demo["pentalanine"] as source:
        view, bridge = _live_view(source.molsys, version=version, threshold=threshold)
        try:
            assert view._current_molecular_projection.is_materialized
            assert not bridge.binary_payload_ids
            assert not any(x["message"]["op"] == "load_molsys_array_payload_ref" for x in bridge.queue)
        finally:
            view.close()


def test_raw_payload_is_not_replaced_with_an_implicit_view_system():
    import json

    from molsysviewer.standalone_qt.utils import QtMessageBridge

    bridge = QtMessageBridge(None, None)
    bridge.payload_ref_threshold_bytes = 1
    payload = {"atoms": {"atom_id": [1]}, "structures": [{"coordinates": [[1, 2, 3]]}]}
    bridge.send({"op": "load_molsys_payload", "payload": payload})
    entry = bridge.queue[0]
    assert entry["message"]["op"] == "load_molsys_payload_ref"
    assert json.loads(bridge.payloads[entry["payload_id"]]) == payload
    assert not bridge.binary_payload_ids


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

    bridge = utils.QtMessageBridge(None, None)
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

    bridge = utils.QtMessageBridge(None, None)
    bridge.ready = True
    forwarded: list = []
    bridge._forward_to_view = forwarded.append  # noqa: SLF001

    assert bridge.handle_frontend_event({"event": "qt_payload_probe", "atoms": 2}) is True
    assert forwarded == [{"event": "qt_payload_probe", "atoms": 2}]


def test_a_known_product_event_stays_silent_and_reaches_the_view():
    from molsysviewer.standalone_qt import utils

    bridge = utils.QtMessageBridge(None, None)
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
    bridge.handle_frontend_event(
        {
            "event": event or entry["wait_event"],
            "id": entry["id"],
            "generation": entry["generation"],
        }
    )


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


def _capture(request_id="capture-a", revision="revision-a"):
    return {
        "op": "request_visual_state",
        "request_id": request_id,
        "capture_revision": revision,
        "capture_timeout_ms": 10000,
    }


def _cancel_capture(request_id="capture-a", revision="revision-a"):
    return {"op": "cancel_visual_state", "request_id": request_id, "capture_revision": revision}


def test_qt_abort_reaches_a_waiting_capture_and_late_ack_cannot_release_the_next_scene():
    bridge, webview = _ready_bridge()
    bridge.send(_capture())
    original = bridge.inflight
    bridge.send({"op": "add_label", "tag": "next"})
    bridge.send(_cancel_capture())
    assert len(webview.delivered) == 3
    assert '"op":"cancel_visual_state"' in webview.delivered[1]
    assert '"op":"add_label"' in webview.delivered[2]
    following = bridge.inflight
    assert following is not original
    bridge.send({"op": "clear_all"})
    bridge.handle_frontend_event({"event": "message_ack", "id": original["id"], "generation": original["generation"]})
    assert bridge.inflight is following
    assert len(webview.delivered) == 3
    control = next(iter(bridge._controls.values()))
    bridge.handle_frontend_event({"event": "message_ack", "id": control["id"], "generation": control["generation"]})
    assert bridge.inflight is following and not bridge._controls
    _acknowledge(bridge)
    assert '"op":"clear_all"' in webview.delivered[-1]


def test_qt_abort_purges_only_its_exact_unsent_capture_tuple():
    bridge, webview = _ready_bridge()
    bridge.send({"op": "clear_all"})
    original = bridge.inflight
    bridge.send(_capture())
    bridge.send(_capture(revision="revision-b"))
    bridge.send(_capture(request_id="capture-b"))
    bridge.send(_cancel_capture())
    assert bridge.inflight is original
    assert len(webview.delivered) == 2
    assert [entry["message"] for entry in bridge.queue] == [
        {**_capture(revision="revision-b"), "id": "qt-3", "generation": 0},
        {**_capture(request_id="capture-b"), "id": "qt-4", "generation": 0},
    ]


@pytest.mark.parametrize("action", ["save_work_file", "cancel_work_file"])
def test_qt_save_verdict_has_its_own_ack_while_restore_stays_ordered(action):
    bridge, webview = _ready_bridge()
    bridge.send(_capture())
    original = bridge.inflight
    bridge.send({"op": "studio_action_result", "action": action, "request_id": "studio-a", "ok": True})
    bridge.send({"op": "studio_action_result", "action": "restore_work_file", "request_id": "restore", "ok": True})
    assert bridge.inflight is original
    assert len(webview.delivered) == 2
    assert len(bridge.queue) == 1
    control = next(iter(bridge._controls.values()))
    bridge.handle_frontend_event({"event": "message_ack", "id": control["id"], "generation": control["generation"] + 1})
    assert bridge._controls
    bridge.handle_frontend_event(
        {"event": "message_error", "id": control["id"], "generation": control["generation"], "error": "rejected"}
    )
    assert not bridge._controls
    assert bridge.inflight is original and len(webview.delivered) == 2


def test_qt_capture_ack_deadline_covers_its_requested_draw_wait():
    bridge, _ = _ready_bridge()
    bridge.send(_capture())
    assert bridge.inflight["timeout_s"] >= 11.0


@pytest.mark.parametrize("transition", ["reload", "generation", "close"])
def test_qt_control_ownership_ends_on_reload_generation_or_close(transition):
    bridge, webview = _ready_bridge()
    bridge.ready = False
    bridge.send(_capture())
    bridge.send(_cancel_capture())
    assert not bridge.queue, "an unseen cancelled capture must not survive bootstrap"
    assert not webview.delivered and len(bridge._controls) == 1
    if transition == "reload":
        bridge.on_load_started()
    elif transition == "generation":
        bridge.begin_generation()
    else:
        bridge._close()
    assert not bridge._controls
    bridge._flush_controls()
    assert not webview.delivered


def test_qt_lifecycle_lane_is_bounded_and_malformed_abort_cannot_retire_a_capture():
    bridge, webview = _ready_bridge()
    bridge.MAX_LIFECYCLE_CONTROLS = 2
    bridge.send(_capture())
    original = bridge.inflight
    with pytest.raises(ValueError, match="exact request id"):
        bridge.send({"op": "cancel_visual_state", "request_id": "capture-a"})
    assert bridge.inflight is original
    for request_id in ("a", "b"):
        bridge.send({"op": "studio_action_result", "action": "save_work_file", "request_id": request_id, "ok": True})
    with pytest.raises(RuntimeError, match="capacity"):
        bridge.send(_cancel_capture())
    assert bridge.inflight is original and len(bridge._controls) == 2
    assert len(webview.delivered) == 3


def test_qt_pending_control_flushes_before_queued_scene_at_real_ready():
    bridge, webview = _ready_bridge()
    bridge.ready = False
    bridge.send({"op": "clear_all"})
    bridge.send(_cancel_capture())
    assert not webview.delivered
    bridge.handle_frontend_event({"event": "ready"})
    assert len(webview.delivered) == 2
    assert '"op":"cancel_visual_state"' in webview.delivered[0]
    assert '"op":"clear_all"' in webview.delivered[1]


def test_qt_controls_retry_and_expire_on_real_qt_timers_without_changing_the_scene_owner():
    """Native loop/transport evidence; this is not WebEngine/capture acceptance."""
    import json
    import subprocess
    import sys
    import textwrap

    pytest.importorskip("PySide6.QtCore")
    script = textwrap.dedent(
        """
        import json, runpy, time
        from PySide6.QtCore import QCoreApplication, QTimer
        from molsysviewer.standalone_qt.utils import QtMessageBridge

        app = QCoreApplication([])
        transport = runpy.run_path("tests/test_qt_transport_contract.py")
        Page = transport["_RecordingWebView"]
        capture = transport["_capture"]
        cancel = transport["_cancel_capture"]
        class DelayedPage(Page):
            def runJavaScript(self, script, callback=None):
                self.delivered.append(script)
                if callback:
                    callback("molsysviewer-handler-missing" if len(self.delivered) == 2
                             else "molsysviewer-message-accepted")
        page = DelayedPage()
        statuses = []
        bridge = QtMessageBridge(page, QTimer, status_callback=statuses.append)
        bridge.ready = True
        bridge.RETRY_BASE_DELAY_MS = 1
        bridge.send(capture())
        scene = bridge.inflight
        bridge.send({"op":"studio_action_result", "action":"save_work_file", "request_id":"studio", "ok":True})
        control = next(iter(bridge._controls.values()))
        timed = QtMessageBridge(Page(), QTimer, status_callback=statuses.append)
        timed.ready = True
        timed.send(capture())
        timed_scene = timed.inflight
        timed.send({"op":"studio_action_result", "action":"cancel_work_file", "request_id":"timeout", "ok":True})
        expiry = next(iter(timed._controls.values()))
        expiry["timeout_s"] = 0.005
        expiry["deadline"] = time.monotonic() + 0.005
        timed._arm_timeout(expiry)
        retired = []
        for transition in ("generation", "reload", "close"):
            item = QtMessageBridge(DelayedPage(), QTimer)
            item.ready = True
            item.RETRY_BASE_DELAY_MS = 1
            item.send(capture())
            item.send({"op":"studio_action_result", "action":"save_work_file", "request_id":transition, "ok":True})
            before = len(item.webview.delivered)
            {"generation":item.begin_generation, "reload":item.on_load_started, "close":item._close}[transition]()
            retired.append((item, before))
        failure = []
        def finish():
            try:
                assert control["delivery_attempts"] == 2
                assert bridge.inflight is scene
                assert not bridge.queue
                bridge.handle_frontend_event({"event":"message_ack", "id":control["id"], "generation":control["generation"]})
                assert not bridge._controls and bridge.inflight is scene
                assert not timed._controls and timed.inflight is timed_scene
                assert any("timed out" in str(item) for item in statuses)
                for item, before in retired:
                    assert len(item.webview.delivered) == before and not item._controls
                print(json.dumps({"retry_attempts":control["delivery_attempts"], "expiry":True,
                                  "scene_owners_unchanged":True, "retired_controls":len(retired)}), flush=True)
            except BaseException as error:
                failure.append(error)
            finally:
                bridge._close(); timed._close()
                for item, _ in retired: item._close()
                app.quit()
        QTimer.singleShot(40, finish)
        app.exec()
        if failure: raise failure[0]
        """
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert report == {"retry_attempts": 2, "expiry": True, "scene_owners_unchanged": True, "retired_controls": 3}
