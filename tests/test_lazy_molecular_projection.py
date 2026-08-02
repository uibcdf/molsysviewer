from __future__ import annotations

import json

import pytest

from molsysviewer.transport import LazyMolecularMessage, StaleMolecularProjectionError


def _message(revision: list[int], calls: list[int]) -> LazyMolecularMessage:
    return LazyMolecularMessage(
        label="system",
        multiple_structures=False,
        molecular_revision=revision[0],
        current_revision=lambda: revision[0],
        builder=lambda: (
            calls.append(1)
            or {
                "op": "load_molsys_payload",
                "payload": {"atoms": []},
                "label": "system",
                "multiple_structures": False,
            }
        ),
    )


def test_lazy_projection_materializes_once_and_returns_defensive_copies():
    revision = [1]
    calls: list[int] = []
    message = _message(revision, calls)

    first = message.materialize(transfer_generation=7)
    first["payload"]["atoms"].append("tampered")
    second = message.materialize(transfer_generation=7)

    assert calls == [1]
    assert second["payload"]["atoms"] == []


def test_lazy_projection_rejects_a_stale_molecular_revision_before_building():
    revision = [1]
    calls: list[int] = []
    message = _message(revision, calls)
    revision[0] = 2

    with pytest.raises(
        StaleMolecularProjectionError,
        match="revision 1 is stale.*transfer generation 8",
    ):
        message.materialize(transfer_generation=8)

    assert calls == []


def test_internal_lazy_projection_cannot_cross_a_json_seam_unmaterialized():
    message = _message([1], [])

    with pytest.raises(TypeError):
        json.dumps(message)
