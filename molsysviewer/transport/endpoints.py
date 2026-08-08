"""Endpoint-scoped ownership for structure transfer coordination."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from .transfer import StructureTransferManager


DeferredMessage = tuple[Mapping[str, Any], Any]


@dataclass
class EndpointTransferState:
    """Mutable transport state owned by one rendering destination."""

    endpoint_id: str | None
    manager: StructureTransferManager | None = None
    mode: str | None = None
    deferred: deque[DeferredMessage] = field(default_factory=deque)
    flushing: bool = False


class EndpointTransferRegistry:
    """Own endpoint managers, modes and deferred queues as one lifecycle."""

    def __init__(
        self,
        embedded_manager: StructureTransferManager,
        popup_manager_factory: Callable[[str], StructureTransferManager],
    ) -> None:
        self._embedded = EndpointTransferState(None, manager=embedded_manager)
        self._popups: dict[str, EndpointTransferState] = {}
        self._popup_manager_factory = popup_manager_factory

    def _state(
        self,
        endpoint_id: str | None,
        *,
        create: bool = False,
    ) -> EndpointTransferState | None:
        if endpoint_id is None:
            return self._embedded
        state = self._popups.get(endpoint_id)
        if state is None and create:
            state = EndpointTransferState(endpoint_id)
            self._popups[endpoint_id] = state
        return state

    def manager(
        self,
        endpoint_id: str | None,
        *,
        create: bool = False,
    ) -> StructureTransferManager | None:
        state = self._state(endpoint_id, create=create)
        if state is None:
            return None
        if endpoint_id is not None and state.manager is None and create:
            state.manager = self._popup_manager_factory(endpoint_id)
        return state.manager

    def iter_managers(self) -> Iterator[tuple[str | None, StructureTransferManager]]:
        if self._embedded.manager is not None:
            yield None, self._embedded.manager
        for endpoint_id, state in self._popups.items():
            if state.manager is not None:
                yield endpoint_id, state.manager

    def register(self, endpoint_id: str, mode: str) -> None:
        state = self._state(endpoint_id, create=True)
        if state is None:  # pragma: no cover - endpoint_id is non-null by contract
            raise RuntimeError("popup endpoint state was not created")
        state.mode = mode

    def mode_items(self) -> Iterator[tuple[str, str]]:
        for endpoint_id, state in self._popups.items():
            if state.mode is not None:
                yield endpoint_id, state.mode

    def defer(
        self,
        endpoint_id: str | None,
        message: Mapping[str, Any],
        buffers: Any,
    ) -> None:
        state = self._state(endpoint_id, create=True)
        if state is None:  # pragma: no cover - embedded state always exists
            raise RuntimeError("endpoint state was not created")
        state.deferred.append((message, buffers))

    def begin_flush(self, endpoint_id: str | None) -> EndpointTransferState | None:
        state = self._state(endpoint_id)
        if state is None or state.flushing:
            return None
        state.flushing = True
        return state

    @staticmethod
    def end_flush(state: EndpointTransferState) -> None:
        state.flushing = False

    def close(self, endpoint_id: str) -> EndpointTransferState | None:
        return self._popups.pop(endpoint_id, None)

    def clear(self) -> None:
        self._embedded.deferred.clear()
        self._embedded.flushing = False
        self._popups.clear()

    def state(self, endpoint_id: str | None) -> EndpointTransferState | None:
        """Return endpoint state for diagnostics and focused tests."""

        return self._state(endpoint_id)

    @property
    def popup_count(self) -> int:
        return len(self._popups)

    @property
    def has_deferred(self) -> bool:
        return bool(self._embedded.deferred) or any(
            state.deferred for state in self._popups.values()
        )

    @property
    def modes(self) -> dict[str, str]:
        return dict(self.mode_items())
