"""Qt keeps the JSON path, and says so instead of losing data quietly.

Qt is in scope for 1.0, but a green AnyWidget transport does not imply Qt: the
bridge carries JSON, has no binary mechanism, and has not been benchmarked. What
must hold today is that this is *true by construction* and *loud when violated*,
so the binary work can proceed on AnyWidget without leaving a trap behind.
"""

import pytest

from molsysviewer.standalone_qt.view_channel import QtViewChannel
from molsysviewer.widget import MolSysViewerWidget


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


def test_the_binary_path_cannot_reach_qt_by_construction():
    # `_binary_structure_transport_limit` gates on the AnyWidget connector, so a
    # Qt channel never negotiates the array-native transport.
    assert not issubclass(QtViewChannel, MolSysViewerWidget)


def test_qt_refuses_buffers_instead_of_dropping_them():
    channel = _channel()
    with pytest.raises(NotImplementedError, match="no binary transport"):
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
