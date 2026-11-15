"""Immutable bootstrap replies do not depend on a molecular scene transaction."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from hashlib import sha256
from threading import Event, get_ident

import pytest
from molsysviewer.system_edits import SystemEditPendingError
from molsysviewer.widget import MolSysViewerWidget

import molsysviewer as msv


@pytest.fixture
def view():
    result = msv.demo["dialanine"]
    try:
        yield result
    finally:
        result.close()


@contextmanager
def _scene_owned_elsewhere(view):
    acquired = Event()
    release = Event()

    def hold():
        with view._system_edits._locked():  # noqa: SLF001
            acquired.set()
            assert release.wait(5), "The test did not release its scene owner."

    with ThreadPoolExecutor(max_workers=1) as worker:
        task = worker.submit(hold)
        try:
            assert acquired.wait(5), "The worker did not acquire scene ownership."
            yield
        finally:
            release.set()
            task.result(timeout=5)


def _observe_actual_sends(view, monkeypatch):
    """Observe and delegate real connector sends; never supply a fake reply."""
    send = view.widget.send
    observations = []

    def observe(message, buffers=None):
        source = message.get("source")
        observations.append(
            {
                "op": message.get("op"),
                "source_sha256": sha256(source.encode()).hexdigest() if isinstance(source, str) else None,
                "thread": get_ident(),
            }
        )
        if buffers is None:
            return send(message)
        return send(message, buffers=buffers)

    monkeypatch.setattr(view.widget, "send", observe)
    return observations


@pytest.mark.parametrize(
    ("event", "operation"),
    [
        ("request_widget_runtime_source", "widget_runtime_source"),
        ("request_popup_source", "popup_source"),
    ],
)
def test_runtime_source_reply_survives_contended_scene_owner(view, monkeypatch, event, operation):
    initial_state = view.export_state()
    history = list(view._test_message_log)  # noqa: SLF001
    system = view.molsys
    observed = _observe_actual_sends(view, monkeypatch)
    host_thread = get_ident()

    with _scene_owned_elsewhere(view):
        view._handle_frontend_event({"event": event})  # noqa: SLF001
        assert observed == [
            {"op": operation, "source_sha256": MolSysViewerWidget._viewer_js_digest, "thread": host_thread}  # noqa: SLF001
        ]
        assert view._ready is False  # noqa: SLF001

    assert view.molsys is system
    assert view.export_state() == initial_state
    assert view._test_message_log == history  # noqa: SLF001


@pytest.mark.parametrize("event", ["request_widget_runtime_source", "request_popup_source"])
def test_closed_view_does_not_reply_to_runtime_source_request(view, monkeypatch, event):
    view.close()
    observed = _observe_actual_sends(view, monkeypatch)
    view._handle_frontend_event({"event": event})  # noqa: SLF001
    assert observed == []


def test_mutable_frontend_event_still_requires_scene_ownership(view):
    height = view.widget.layout.height
    with _scene_owned_elsewhere(view), pytest.raises(SystemEditPendingError):
        view._handle_frontend_event({"event": "widget_resize", "height": 333, "width": 444})  # noqa: SLF001
    assert view.widget.layout.height == height
