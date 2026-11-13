"""Pending renderer replies owned by one View, independent of its GUI host.

This is the correlation/lifetime layer for explicit visual capture. It never
reads a camera cache, writes a file, drives a GUI loop or starts a worker thread.
The connector must validate the source endpoint before calling ``receive``.
"""

from __future__ import annotations

import asyncio
import math
import time
from concurrent.futures import Future
from copy import deepcopy
from dataclasses import dataclass
from numbers import Real
from threading import RLock
from uuid import uuid4

from smonitor.integrations import CatalogException

from .._private.smonitor import CATALOG, META


class FrontendRequestError(CatalogException, RuntimeError):
    """An explicit renderer request could not obtain its own valid reply."""

    catalog_key = "frontend_request_failed"

    def __init__(self, message=None, *, reason=None):
        super().__init__(message, catalog=CATALOG, meta=META, extra={"reason": reason})


class _MovieOverlayUnavailable(FrontendRequestError):
    catalog_key = "movie_overlay_unavailable"


class _MovieOverlayChanged(FrontendRequestError):
    catalog_key = "movie_overlay_changed"


class _MovieOverlayLimit(FrontendRequestError):
    catalog_key = "movie_overlay_limit"


def _renderer_failure(content):
    # Only fixed authored types have public recovery instructions. Arbitrary
    # renderer messages/paths never become user-facing diagnostic text.
    known = {
        "MovieOverlayUnavailable": _MovieOverlayUnavailable,
        "MovieOverlayChanged": _MovieOverlayChanged,
        "MovieOverlayLimit": _MovieOverlayLimit,
    }
    error_type = content.get("error_type")
    selected = known.get(error_type) if isinstance(error_type, str) else None
    return selected(reason=selected.catalog_key) if selected else FrontendRequestError(reason="renderer_refused")


@dataclass(frozen=True)
class FrontendRequest:
    owner_id: str
    request_id: str
    endpoint_id: str
    reply_event: str
    revision: str
    deadline: float
    future: Future


class FrontendRequests:
    """Bounded, single-use requests; callbacks run on the connector's thread.

    Native hosts can consume the standard Future in their own event loop.
    Notebook callers await it without blocking the kernel's comm dispatcher.
    No lock or scientific-edit context is held across the asynchronous wait.
    """

    def __init__(self, *, capacity: int = 32, publish=None, abandon=None):
        if type(capacity) is not int or capacity < 1:
            raise ValueError("Frontend request capacity must be a positive integer.")
        self._capacity = capacity
        self._pending: dict[str, FrontendRequest] = {}
        self._closed = False
        self._owner_id = uuid4().hex
        self._lock = RLock()
        self._publish = publish if publish is not None else lambda callback: callback()
        self._abandon = abandon

    def begin(self, *, endpoint_id: str, reply_event: str, revision: str, timeout: float) -> FrontendRequest:
        for value in (endpoint_id, reply_event, revision):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Renderer requests require an endpoint, reply event and revision.")
        if isinstance(timeout, bool) or not isinstance(timeout, Real) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Renderer request timeout must be finite and positive.")
        self.expire()
        with self._lock:
            if self._closed:
                raise FrontendRequestError(reason="view_closed")
            if len(self._pending) >= self._capacity:
                raise FrontendRequestError(reason="request_capacity")
            request = FrontendRequest(
                self._owner_id, uuid4().hex, endpoint_id, reply_event, revision, time.monotonic() + timeout, Future()
            )
            self._pending[request.request_id] = request
            # Cancellation releases this entry too; a late reply cannot revive
            # it or complete a subsequent request.
            request.future.add_done_callback(
                lambda future: self.cancel(request) if future.cancelled() else self._release(request)
            )
        return request

    def receive(self, content: dict, *, endpoint_id: str) -> bool:
        """Accept one matching reply from a connector-validated endpoint.

        Wrong owners/revisions and unsolicited or duplicate events cannot
        satisfy a pending request. Expired requests fail before any consumer
        callback can use their payload. Returned payloads are detached.
        """
        self.expire()
        request_id = content.get("request_id")
        if not isinstance(request_id, str):
            return False
        with self._lock:
            request = self._pending.get(request_id)
            if request is None or (
                endpoint_id != request.endpoint_id
                or content.get("event") != request.reply_event
                or content.get("capture_revision") != request.revision
            ):
                return False
            self._pending.pop(request_id)
        # Never invoke Future callbacks while holding the registry lock.
        if not request.future.set_running_or_notify_cancel():
            return False
        if request.deadline <= time.monotonic():
            try:
                self._notify_abandon(request)
            finally:
                self._publish(lambda: request.future.set_exception(FrontendRequestError(reason="request_timeout")))
            return False
        if content.get("ok") is not True:
            error_type = content.get("error_type")
            failure = {"error_type": error_type if isinstance(error_type, str) else None}
            self._publish(lambda: request.future.set_exception(_renderer_failure(failure)))
        else:
            payload = deepcopy(content)
            self._publish(lambda: request.future.set_result(payload))
        return True

    async def wait(self, request: FrontendRequest) -> dict:
        """Await only this request, with cleanup on timeout or cancellation."""
        if request.owner_id != self._owner_id:
            raise FrontendRequestError(reason="unknown_request")
        try:
            if request.future.done():
                return request.future.result()
            remaining = max(0.0, request.deadline - time.monotonic())
            return await asyncio.wait_for(asyncio.wrap_future(request.future), timeout=remaining)
        except TimeoutError as error:
            raise FrontendRequestError(reason="request_timeout") from error
        finally:
            self.cancel(request)

    def cancel(self, request: FrontendRequest) -> None:
        try:
            if self._release(request):
                self._notify_abandon(request)
        finally:
            self._publish(request.future.cancel)

    def cancel_endpoint(self, endpoint_id: str) -> None:
        with self._lock:
            pending = [request for request in self._pending.values() if request.endpoint_id == endpoint_id]
            for request in pending:
                self._pending.pop(request.request_id)
        self._fail_all(pending, "endpoint_closed")

    def expire(self) -> None:
        now = time.monotonic()
        with self._lock:
            pending = [request for request in self._pending.values() if request.deadline <= now]
            for request in pending:
                self._pending.pop(request.request_id)
        self._fail_all(pending, "request_timeout")

    def close(self) -> None:
        with self._lock:
            self._closed = True
            pending = tuple(self._pending.values())
            self._pending.clear()
        self._fail_all(pending, "view_closed")

    def _release(self, request: FrontendRequest) -> bool:
        with self._lock:
            if self._pending.get(request.request_id) is request:
                self._pending.pop(request.request_id)
                return True
        return False

    def _notify_abandon(self, request: FrontendRequest) -> None:
        if self._abandon is not None:
            self._publish(lambda: self._abandon(request))

    def _fail(self, request: FrontendRequest, reason: str) -> None:
        self._release(request)
        try:
            self._notify_abandon(request)
        finally:
            if request.future.set_running_or_notify_cancel():
                self._publish(lambda: request.future.set_exception(FrontendRequestError(reason=reason)))

    def _fail_all(self, pending, reason):
        errors = []
        for request in pending:
            try:
                self._fail(request, reason)
            except BaseException as error:
                errors.append(error)
        if len(errors) == 1:
            raise errors[0]
        if errors:
            raise BaseExceptionGroup("Renderer capture cleanup failed", errors)
