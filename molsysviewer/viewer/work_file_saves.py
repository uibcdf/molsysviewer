"""Deferred Studio save intentions over the shared capture and file owners."""

from collections import OrderedDict
from concurrent.futures import CancelledError, Future
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from time import monotonic
from weakref import ref

from .frontend_requests import FrontendRequestError
from .visual_capture import (
    capture_endpoint,
    finish_live_capture,
    prepare_live_capture,
    send_live_capture,
    write_captured_state,
)

CAPTURE_TIMEOUT = 10.0


class WorkFileSaveCancelled(FrontendRequestError):
    catalog_key = "work_file_save_cancelled"


@dataclass
class _Save:
    key: tuple[str, str]
    endpoint: str
    kind: str
    path: Path
    overwrite: bool
    captured: object
    ticket: object
    result: Future = field(default_factory=Future)
    phase: str = "capturing"
    timer: object = None
    lock: object = field(default_factory=RLock)


class WorkFileSaves:
    """One bounded pending intention per authenticated requester and id.

    No thread is created. Capture deadlines run on the connector's own loop;
    a successful reply alone may enter the synchronous atomic writer. Cancel
    is accepted only before that commit phase, never after writing has begun.
    """

    def __init__(self, view):
        self._view_ref = ref(view)
        self._pending = {}
        self._completed = OrderedDict()
        self._lock = RLock()
        self._closed = False

    def _owner(self, view, value):
        host = f"widget-host:{view._binary_session_id}"
        if value is None or value in ("primary", host):
            return "primary"
        if not isinstance(value, str) or value not in view._endpoint_transfers.modes:
            raise FrontendRequestError(reason="endpoint_closed")
        return value

    def start(self, content, *, kind: str, path: Path, overwrite: bool) -> Future:
        view = self._view_ref()
        if view is None or view.closed or self._closed:
            raise FrontendRequestError(reason="view_closed")
        owner = self._owner(view, content.get("_work_file_owner_endpoint_id"))
        key = (owner, content["request_id"])
        endpoint = capture_endpoint(view, content.get("_capture_endpoint_id"))
        schedule = getattr(view.widget, "_schedule_callback", None)
        if not callable(schedule):
            raise FrontendRequestError(reason="scheduler_unavailable")
        with self._lock:
            if key in self._completed or key in self._pending:
                raise FrontendRequestError(reason="duplicate_save")
            if len(self._pending) >= 32:
                raise FrontendRequestError(reason="request_capacity")
            captured, ticket = prepare_live_capture(view, timeout=CAPTURE_TIMEOUT, endpoint_id=endpoint)
            operation = _Save(key, endpoint, kind, path, overwrite, captured, ticket)
            self._pending[key] = operation
        try:
            operation.timer = schedule(CAPTURE_TIMEOUT, lambda: self._expire(operation))
        except Exception as error:
            self._finish(operation, FrontendRequestError(reason="scheduler_unavailable"))
            view._frontend_requests.cancel(ticket)
            raise FrontendRequestError(reason="scheduler_unavailable") from error
        ticket.future.add_done_callback(lambda future: self._captured(operation, future))
        try:
            send_live_capture(view, ticket, protocol_version=captured.protocol_version)
        except BaseException as error:
            self._finish(operation, error)
            raise
        return operation.result

    def cancel(self, content) -> bool:
        view = self._view_ref()
        if view is None:
            return False
        key = (self._owner(view, content.get("_work_file_owner_endpoint_id")), content["request_id"])
        with self._lock:
            operation = self._pending.get(key)
            completed = self._completed.get(key)
        if operation is None:
            return completed == "cancelled"
        return self._cancel(operation, WorkFileSaveCancelled())

    def _cancel(self, operation, error) -> bool:
        with operation.lock:
            if operation.phase != "capturing":
                return False
            operation.phase = "cancelling"
            ticket = operation.ticket
        self._finish(operation, error)
        if ticket is not None:
            view = self._view_ref()
            if view is not None:
                view._frontend_requests.cancel(ticket)
            else:
                ticket.future.cancel()
        return True

    def _expire(self, operation):
        with operation.lock:
            if operation.phase != "capturing" or operation.ticket is None:
                return
            remaining = operation.ticket.deadline - monotonic()
        view = self._view_ref()
        if view is None or view.closed:
            self._cancel(operation, FrontendRequestError(reason="view_closed"))
        elif remaining > 0:
            with operation.lock:
                if operation.phase == "capturing":
                    operation.timer = view.widget._schedule_callback(remaining, lambda: self._expire(operation))
        else:
            view._frontend_requests.expire()

    def _captured(self, operation, future):
        try:
            reply = future.result()
            with operation.lock:
                if operation.phase != "capturing":
                    return
                timer, operation.timer = operation.timer, None
                captured = operation.captured
            if timer is not None:
                timer.cancel()
            view = self._view_ref()
            if view is None:
                raise FrontendRequestError(reason="view_closed")
            with view._system_edits._locked():
                captured = finish_live_capture(view, captured, reply)
                if operation.path.exists() and not operation.overwrite:
                    raise ValueError("This file already exists. Allow overwrite or choose another path.")
                with operation.lock:
                    if operation.phase != "capturing":
                        return
                    operation.phase = "writing"
                write_captured_state(view, captured, operation.path, kind=operation.kind)
        except CancelledError:
            self._finish(operation, FrontendRequestError(reason="capture_interrupted"))
        except BaseException as error:
            self._finish(operation, error)
            if not isinstance(error, Exception):
                raise
        else:
            self._finish(operation, None)

    def _finish(self, operation, error):
        with operation.lock:
            if operation.phase in {"saved", "failed", "cancelled"}:
                return
            operation.phase = (
                "saved" if error is None else "cancelled" if isinstance(error, WorkFileSaveCancelled) else "failed"
            )
            timer, operation.timer = operation.timer, None
            operation.captured = None
            operation.ticket = None
        with self._lock:
            self._pending.pop(operation.key, None)
            self._completed[operation.key] = operation.phase
            while len(self._completed) > 64:
                self._completed.popitem(last=False)
        if timer is not None:
            timer.cancel()

        # Consumers may resume on another kernel thread. Publish only after
        # both registry and molecular writer locks have been released.
        def publish():
            if error is None:
                operation.result.set_result(None)
            else:
                operation.result.set_exception(error)

        view = self._view_ref()
        if view is not None:
            view._system_edits._after_unlock(publish)
        else:
            publish()

    def cancel_endpoint(self, endpoint):
        with self._lock:
            pending = [op for op in self._pending.values() if endpoint in (op.key[0], op.endpoint)]
        for operation in pending:
            self._cancel(operation, FrontendRequestError(reason="endpoint_closed"))

    def close(self):
        with self._lock:
            self._closed = True
            pending = tuple(self._pending.values())
        for operation in pending:
            self._cancel(operation, FrontendRequestError(reason="view_closed"))
