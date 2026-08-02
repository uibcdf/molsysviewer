"""State and ownership for one-chunk-in-flight structure transfers."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TransferState(str, Enum):
    """Every active and terminal state of a structure transfer."""

    WAITING_BEGIN_ACK = "waiting_begin_ack"
    WAITING_CHUNK_ACK = "waiting_chunk_ack"
    WAITING_COMPLETE = "waiting_complete"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FALLBACK = "fallback"


TERMINAL_STATES = frozenset({
    TransferState.COMPLETED,
    TransferState.CANCELLED,
    TransferState.EXPIRED,
    TransferState.FALLBACK,
})


class AckDisposition(str, Enum):
    """Effect requested by an accepted or ignored frontend event."""

    IGNORED = "ignored"
    FOREIGN = "foreign"
    SEND_CHUNK = "send_chunk"
    WAIT_COMPLETE = "wait_complete"
    COMPLETED = "completed"
    FALLBACK = "fallback"


@dataclass
class TransferChunk:
    message: dict[str, Any]
    buffers: list[memoryview]


@dataclass(frozen=True)
class TransferTermination:
    transfer: "StructureTransfer"
    state: TransferState
    reason: str


@dataclass(frozen=True)
class TransferAck:
    disposition: AckDisposition
    chunk: TransferChunk | None = None
    termination: TransferTermination | None = None


@dataclass
class StructureTransfer:
    """One molecular generation and the resources retained while it is live."""

    viewer_id: str
    session_id: str
    stream_id: str
    generation: int
    begin_message: dict[str, Any]
    chunks: list[TransferChunk]
    fallback_factory: Callable[[], dict[str, Any]]
    payload: Any
    target_endpoint_id: str | None
    timeout_s: float
    deadline: float
    state: TransferState = TransferState.WAITING_BEGIN_ACK
    next_chunk: int = 0
    awaited_chunk: int | None = None
    terminal_reason: str | None = None
    release_count: int = field(default=0, init=False)

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def matches(self, event: Mapping[str, Any]) -> bool:
        return (
            event.get("viewer_id") == self.viewer_id
            and event.get("session_id") == self.session_id
            and event.get("stream_id") == self.stream_id
            and event.get("generation") == self.generation
        )

    def acknowledge_begin(self, now: float) -> TransferAck:
        if self.state is not TransferState.WAITING_BEGIN_ACK:
            return TransferAck(AckDisposition.IGNORED)
        return self._advance(now)

    def acknowledge_chunk(self, chunk_id: Any, now: float) -> TransferAck:
        if (
            self.state is not TransferState.WAITING_CHUNK_ACK
            or not isinstance(chunk_id, int)
            or isinstance(chunk_id, bool)
            or chunk_id != self.awaited_chunk
        ):
            return TransferAck(AckDisposition.IGNORED)
        self.next_chunk = chunk_id + 1
        return self._advance(now)

    def _advance(self, now: float) -> TransferAck:
        self.deadline = now + self.timeout_s
        if self.next_chunk >= len(self.chunks):
            self.state = TransferState.WAITING_COMPLETE
            self.awaited_chunk = None
            return TransferAck(AckDisposition.WAIT_COMPLETE)
        chunk = self.chunks[self.next_chunk]
        self.state = TransferState.WAITING_CHUNK_ACK
        self.awaited_chunk = self.next_chunk
        return TransferAck(AckDisposition.SEND_CHUNK, chunk=chunk)

    def terminate(self, state: TransferState, reason: str) -> TransferTermination | None:
        if state not in TERMINAL_STATES:
            raise ValueError(f"{state!r} is not a terminal transfer state")
        if self.is_terminal:
            return None
        self.state = state
        self.terminal_reason = reason
        self._release()
        return TransferTermination(self, state, reason)

    def materialize_fallback(self) -> dict[str, Any]:
        return self.fallback_factory()

    def _release(self) -> None:
        if self.release_count:
            return
        self.chunks.clear()
        self.payload = None
        self.release_count = 1


class StructureTransferManager:
    """Own generation allocation, active transfer identity and transitions."""

    def __init__(
        self,
        viewer_id: str,
        session_id: str,
        *,
        timeout_s: float = 30.0,
        monotonic: Callable[[], float],
        stream_id: str = "structures:main",
    ) -> None:
        self.viewer_id = viewer_id
        self.session_id = session_id
        self.stream_id = stream_id
        self.timeout_s = float(timeout_s)
        self.monotonic = monotonic
        self._generation = 0
        self._active: StructureTransfer | None = None

    @property
    def active(self) -> StructureTransfer | None:
        return self._active

    @property
    def has_active(self) -> bool:
        return self._active is not None

    def start(
        self,
        *,
        begin_message: Mapping[str, Any],
        chunks: Sequence[tuple[Mapping[str, Any], Sequence[memoryview]]],
        fallback_factory: Callable[[int], dict[str, Any]],
        payload: Any,
        target_endpoint_id: str | None,
    ) -> StructureTransfer:
        if self._active is not None:
            raise RuntimeError("cannot start a structure transfer while another is active")
        self._generation += 1
        identity = {
            "viewer_id": self.viewer_id,
            "session_id": self.session_id,
            "stream_id": self.stream_id,
            "generation": self._generation,
        }
        begin = {**begin_message, **identity}
        prepared_chunks = [
            TransferChunk({**message, **identity}, list(buffers))
            for message, buffers in chunks
        ]
        if target_endpoint_id is not None:
            begin["target_endpoint_id"] = target_endpoint_id
            for chunk in prepared_chunks:
                chunk.message["target_endpoint_id"] = target_endpoint_id
        generation = self._generation
        transfer = StructureTransfer(
            viewer_id=self.viewer_id,
            session_id=self.session_id,
            stream_id=self.stream_id,
            generation=self._generation,
            begin_message=begin,
            chunks=prepared_chunks,
            fallback_factory=lambda: fallback_factory(generation),
            payload=payload,
            target_endpoint_id=target_endpoint_id,
            timeout_s=self.timeout_s,
            deadline=self.monotonic() + self.timeout_s,
        )
        self._active = transfer
        return transfer

    def cancel(self, reason: str) -> TransferTermination | None:
        return self._terminate(TransferState.CANCELLED, reason)

    def fallback(self, reason: str) -> TransferTermination | None:
        return self._terminate(TransferState.FALLBACK, reason)

    def expire_if_due(self) -> TransferTermination | None:
        transfer = self._active
        if (
            transfer is None
            or transfer.state is TransferState.WAITING_COMPLETE
            or self.monotonic() < transfer.deadline
        ):
            return None
        return self._terminate(
            TransferState.EXPIRED,
            f"no acknowledgement within {self.timeout_s:g}s while awaiting {transfer.state.value!r}",
        )

    def handle_event(self, event: Mapping[str, Any]) -> TransferAck:
        transfer = self._active
        if transfer is None:
            return TransferAck(AckDisposition.IGNORED)
        if not transfer.matches(event):
            return TransferAck(AckDisposition.FOREIGN)

        event_name = event.get("event")
        if event_name == "structure_data_begin_ack":
            return transfer.acknowledge_begin(self.monotonic())
        if event_name == "structure_data_chunk_ack":
            return transfer.acknowledge_chunk(event.get("chunk_id"), self.monotonic())
        if event_name == "structure_data_complete":
            if transfer.state is not TransferState.WAITING_COMPLETE:
                return TransferAck(AckDisposition.IGNORED)
            termination = self._terminate(TransferState.COMPLETED, "frontend completed transfer")
            return TransferAck(AckDisposition.COMPLETED, termination=termination)
        if event_name == "structure_data_error":
            termination = self._terminate(
                TransferState.FALLBACK,
                f"frontend rejected generation {transfer.generation}: {event.get('error')}",
            )
            return TransferAck(AckDisposition.FALLBACK, termination=termination)
        return TransferAck(AckDisposition.IGNORED)

    def _terminate(self, state: TransferState, reason: str) -> TransferTermination | None:
        transfer = self._active
        if transfer is None:
            return None
        termination = transfer.terminate(state, reason)
        if termination is not None:
            self._active = None
        return termination
