"""D3 backpressure: a stream whose acknowledgement never arrives must not pin
the retained arrays, and must fall back observably.

The deadline is evaluated on main-thread entry points, never from a timer
thread: `widget.send` is not safe to call off the kernel thread for AnyWidget.
Tests inject a clock rather than sleeping.
"""

import threading

import pytest

from molsysviewer.demo import demo
from molsysviewer.loaders.json_molsys import serialize_json_molsys
from molsysviewer.transport import TransferState
import molsysviewer.viewer.core as viewer_core


def _capture_widget_send(view):
    sent: list[tuple[dict, list]] = []

    def send(message, buffers=None):
        sent.append((dict(message), list(buffers or [])))

    view.widget.send = send  # type: ignore[method-assign]
    return sent


class _Clock:
    """Injectable monotonic clock."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _view_with_pending_stream():
    """A view that has sent `structure_data_begin` and is awaiting its ack."""
    view = demo["dialanine"]
    clock = _Clock()
    view._monotonic = clock  # noqa: SLF001
    sent = _capture_widget_send(view)
    view._handle_frontend_event({  # noqa: SLF001
        "event": "ready",
        "capabilities": {"binary_structure_data": [1], "max_buffer_bytes": 16 * 1024 * 1024},
    })
    assert any(m.get("op") == "structure_data_begin" for m, _ in sent)
    assert view._structure_transfers.active is not None  # noqa: SLF001
    assert view._structure_transfers.active.state is TransferState.WAITING_BEGIN_ACK  # noqa: SLF001
    return view, clock, sent


def test_a_stream_whose_ack_never_arrives_releases_arrays_and_builds_json_once(monkeypatch):
    view, clock, sent = _view_with_pending_stream()
    json_builds: list[int] = []
    original_build = viewer_core.build_json_molsys_message

    def recording_build(*args, **kwargs):
        json_builds.append(1)
        return original_build(*args, **kwargs)

    monkeypatch.setattr(viewer_core, "build_json_molsys_message", recording_build)
    transfer = view._structure_transfers.active  # noqa: SLF001
    assert transfer.payload is not None, "arrays are retained while in flight"

    clock.advance(view._structure_transfers.timeout_s + 1)  # noqa: SLF001
    sent.clear()

    # Any main-thread entry point triggers the check; unrelated frontend traffic
    # is the realistic one.
    with pytest.warns(RuntimeWarning, match="no acknowledgement"):
        view._handle_inbound_message({"event": "widget_resize", "height": 10, "width": 10})  # noqa: SLF001

    # The stream is gone and its arrays are released, not merely dereferenced.
    assert view._structure_transfers.active is None  # noqa: SLF001
    assert transfer.payload is None
    assert transfer.chunks == []

    ops = [m.get("op") for m, _ in sent]
    # The receiver is told to drop its half, and the JSON path is used instead.
    assert "structure_data_cancel" in ops
    assert "load_molsys_payload" in ops
    fallback = next(m for m, _ in sent if m.get("op") == "load_molsys_payload")
    assert fallback["payload"] == serialize_json_molsys(view.molsys)
    assert json_builds == [1]


def test_a_stream_that_is_acknowledged_in_time_is_not_dropped():
    view, clock, sent = _view_with_pending_stream()
    # Just under the deadline: still alive.
    clock.advance(view._structure_transfers.timeout_s - 1)  # noqa: SLF001
    view._handle_inbound_message({"event": "widget_resize", "height": 10, "width": 10})  # noqa: SLF001
    assert view._structure_transfers.active is not None  # noqa: SLF001


def test_each_acknowledgement_restarts_the_deadline():
    view, clock, sent = _view_with_pending_stream()
    first_deadline = view._structure_transfers.active.deadline  # noqa: SLF001

    clock.advance(view._structure_transfers.timeout_s - 1)  # noqa: SLF001
    view._handle_frontend_event({  # noqa: SLF001
        "event": "structure_data_begin_ack",
        "viewer_id": view._binary_viewer_id,  # noqa: SLF001
        "session_id": view._binary_session_id,  # noqa: SLF001
        "stream_id": "structures:main",
        "generation": view._structure_transfers.active.generation,  # noqa: SLF001
    })
    transfer = view._structure_transfers.active  # noqa: SLF001
    assert transfer is not None, "progress must keep the stream alive"
    # A peer that is slow but alive gets a fresh budget rather than being dropped.
    assert transfer.deadline > first_deadline


def test_a_completed_stream_is_released_and_never_expires():
    view, clock, sent = _view_with_pending_stream()
    generation = view._structure_transfers.active.generation  # noqa: SLF001
    identity = {
        "viewer_id": view._binary_viewer_id,  # noqa: SLF001
        "session_id": view._binary_session_id,  # noqa: SLF001
        "stream_id": "structures:main",
        "generation": generation,
    }
    view._handle_frontend_event({"event": "structure_data_begin_ack", **identity})  # noqa: SLF001
    chunk_id = 0
    while (
        view._structure_transfers.active is not None  # noqa: SLF001
        and view._structure_transfers.active.state is not TransferState.WAITING_COMPLETE  # noqa: SLF001
    ):
        view._handle_frontend_event({  # noqa: SLF001
            "event": "structure_data_chunk_ack", "chunk_id": chunk_id, **identity,
        })
        chunk_id += 1
        if chunk_id > 64:
            pytest.fail("chunk acknowledgement loop did not converge")

    view._handle_frontend_event({"event": "structure_data_complete", **identity})  # noqa: SLF001
    assert view._structure_transfers.active is None  # noqa: SLF001

    # A late deadline sweep on a finished stream must not warn or fall back.
    clock.advance(10_000)
    view._check_binary_structure_ack_timeout()  # noqa: SLF001


def test_the_ack_deadline_is_never_driven_from_a_timer_thread():
    # The design forbids a timer thread, because widget.send is unsafe off the
    # kernel thread for AnyWidget. Sending must happen on the calling thread.
    view, clock, sent = _view_with_pending_stream()
    threads: list = []
    original_send = view.widget.send

    def recording_send(message, buffers=None):
        threads.append(threading.current_thread())
        return original_send(message, buffers=buffers)

    view.widget.send = recording_send  # type: ignore[method-assign]
    clock.advance(view._structure_transfers.timeout_s + 1)  # noqa: SLF001
    with pytest.warns(RuntimeWarning):
        view._handle_inbound_message({"event": "widget_resize", "height": 1, "width": 1})  # noqa: SLF001

    assert threads, "the timeout path must send the cancel and the JSON fallback"
    assert all(t is threading.current_thread() for t in threads)
