from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import pytest

from molsysviewer.transport import (
    AckDisposition,
    StructureTransferManager,
    TransferState,
)


@dataclass
class Clock:
    now: float = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_manager(*, target: str | None = "canvas-popup-1"):
    clock = Clock()
    manager = StructureTransferManager(
        "view-1",
        "session-1",
        timeout_s=30.0,
        monotonic=clock,
    )
    payload = object()
    transfer = manager.start(
        begin_message={"op": "structure_data_begin", "chunk_count": 1},
        chunks=[(
            {"op": "structure_data_chunk", "chunk_id": 0},
            [memoryview(b"coordinates")],
        )],
        fallback_message={"op": "load_molsys_payload"},
        payload=payload,
        target_endpoint_id=target,
    )
    return manager, transfer, clock, payload


def identity(transfer):
    return {
        "viewer_id": transfer.viewer_id,
        "session_id": transfer.session_id,
        "stream_id": transfer.stream_id,
        "generation": transfer.generation,
    }


def complete(manager, transfer):
    begin = manager.handle_event({"event": "structure_data_begin_ack", **identity(transfer)})
    assert begin.disposition is AckDisposition.SEND_CHUNK
    chunk = manager.handle_event({
        "event": "structure_data_chunk_ack",
        "chunk_id": 0,
        **identity(transfer),
    })
    assert chunk.disposition is AckDisposition.WAIT_COMPLETE
    return manager.handle_event({"event": "structure_data_complete", **identity(transfer)})


@pytest.mark.parametrize(
    ("terminal_state", "terminate"),
    [
        (TransferState.COMPLETED, lambda manager, transfer, clock: complete(manager, transfer)),
        (TransferState.CANCELLED, lambda manager, transfer, clock: manager.cancel("cancelled")),
        (TransferState.EXPIRED, lambda manager, transfer, clock: (
            clock.advance(31.0), manager.expire_if_due()
        )[1]),
        (TransferState.FALLBACK, lambda manager, transfer, clock: manager.fallback("failed")),
    ],
)
def test_every_terminal_transition_releases_once_and_preserves_identity(
    terminal_state,
    terminate,
):
    manager, transfer, clock, payload = make_manager()
    generation = transfer.generation

    result = terminate(manager, transfer, clock)
    termination = result.termination if hasattr(result, "termination") else result

    assert termination is not None
    assert termination.state is terminal_state
    assert termination.transfer is transfer
    assert transfer.generation == generation
    assert transfer.target_endpoint_id == "canvas-popup-1"
    assert transfer.payload is None
    assert transfer.chunks == []
    assert transfer.release_count == 1
    assert manager.active is None

    # Repeating any terminal operation cannot release or mutate the detached transfer.
    manager.cancel("late cancel")
    transfer.terminate(TransferState.CANCELLED, "direct late cancel")
    assert transfer.state is terminal_state
    assert transfer.release_count == 1


def test_start_allocates_monotonic_generations_and_stamps_the_exact_destination():
    manager, first, _, _ = make_manager()
    first_identity = identity(first)
    assert first.begin_message["target_endpoint_id"] == "canvas-popup-1"
    assert first.chunks[0].message["target_endpoint_id"] == "canvas-popup-1"
    manager.cancel("replace")

    second = manager.start(
        begin_message={"op": "structure_data_begin"},
        chunks=[],
        fallback_message={"op": "load_molsys_payload"},
        payload=object(),
        target_endpoint_id=None,
    )
    assert second.generation == first.generation + 1
    assert "target_endpoint_id" not in second.begin_message

    stale = manager.handle_event({"event": "structure_data_begin_ack", **first_identity})
    assert stale.disposition is AckDisposition.FOREIGN
    assert manager.active is second
    assert second.state is TransferState.WAITING_BEGIN_ACK


def test_start_refuses_to_overwrite_an_active_transfer():
    manager, first, _, _ = make_manager()

    with pytest.raises(RuntimeError, match="another is active"):
        manager.start(
            begin_message={"op": "structure_data_begin"},
            chunks=[],
            fallback_message={"op": "load_molsys_payload"},
            payload=object(),
            target_endpoint_id=None,
        )

    assert manager.active is first
    assert first.payload is not None
    assert first.release_count == 0


def test_only_the_expected_ack_advances_and_refreshes_the_deadline():
    manager, transfer, clock, _ = make_manager()
    original_deadline = transfer.deadline

    foreign = manager.handle_event({
        "event": "structure_data_begin_ack",
        **{**identity(transfer), "session_id": "another-session"},
    })
    assert foreign.disposition is AckDisposition.FOREIGN
    assert transfer.state is TransferState.WAITING_BEGIN_ACK
    assert transfer.deadline == original_deadline

    clock.advance(20.0)
    accepted = manager.handle_event({"event": "structure_data_begin_ack", **identity(transfer)})
    assert accepted.disposition is AckDisposition.SEND_CHUNK
    assert accepted.chunk is not None
    assert accepted.chunk.message["chunk_id"] == 0
    assert transfer.deadline == clock.now + manager.timeout_s

    duplicate = manager.handle_event({"event": "structure_data_begin_ack", **identity(transfer)})
    assert duplicate.disposition is AckDisposition.IGNORED
    assert transfer.awaited_chunk == 0


@pytest.mark.parametrize("terminal", ["cancel", "expired", "fallback", "complete"])
def test_late_ack_cannot_revive_a_terminal_generation(terminal):
    manager, transfer, clock, _ = make_manager()
    if terminal == "cancel":
        manager.cancel("cancelled")
    elif terminal == "expired":
        clock.advance(31.0)
        manager.expire_if_due()
    elif terminal == "fallback":
        manager.fallback("failed")
    else:
        complete(manager, transfer)

    late = manager.handle_event({"event": "structure_data_begin_ack", **identity(transfer)})
    assert late.disposition is AckDisposition.IGNORED
    assert manager.active is None
    assert transfer.is_terminal


def test_frontend_error_terminates_as_fallback_with_the_reported_generation():
    manager, transfer, _, _ = make_manager()

    result = manager.handle_event({
        "event": "structure_data_error",
        "error": "bad descriptor",
        **identity(transfer),
    })

    assert result.disposition is AckDisposition.FALLBACK
    assert result.termination is not None
    assert result.termination.state is TransferState.FALLBACK
    assert f"generation {transfer.generation}" in result.termination.reason
    assert "bad descriptor" in result.termination.reason
    assert transfer.release_count == 1


def test_core_orchestrates_transfer_effects_without_owning_transfer_state():
    source = (Path(__file__).parents[1] / "molsysviewer" / "viewer" / "core.py").read_text()

    assert re.search(r"self\._binary_structure_stream\b", source) is None
    assert re.search(r"self\._binary_structure_generation\b", source) is None
    assert "TransferState." not in source
    assert "_structure_transfers._" not in source
