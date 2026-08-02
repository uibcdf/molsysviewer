"""Lazy portable molecular projections retained only as transport fallback."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


_LAZY_MARKER = "_molsysviewer_lazy_molecular_projection"


class StaleMolecularProjectionError(RuntimeError):
    """Raised rather than serializing a different molecular revision."""


class LazyMolecularMessage(dict[str, Any]):
    """Message metadata plus a generation-safe, memoized JSON producer.

    The marker value is intentionally not JSON serializable. A transport or
    export seam that forgets to materialize this internal message fails loudly
    instead of delivering `load_molsys_payload` without a payload.
    """

    def __init__(
        self,
        *,
        label: str | None,
        multiple_structures: bool,
        molecular_revision: int,
        current_revision: Callable[[], int],
        builder: Callable[[], dict[str, Any]],
    ) -> None:
        super().__init__({
            "op": "load_molsys_payload",
            "label": label,
            "multiple_structures": bool(multiple_structures),
            _LAZY_MARKER: object(),
        })
        self._molecular_revision = molecular_revision
        self._current_revision = current_revision
        self._builder = builder
        self._materialized: dict[str, Any] | None = None

    @property
    def molecular_revision(self) -> int:
        return self._molecular_revision

    @property
    def is_materialized(self) -> bool:
        return self._materialized is not None

    def materialize(self, *, transfer_generation: int | None = None) -> dict[str, Any]:
        if self._materialized is None:
            current = self._current_revision()
            if current != self._molecular_revision:
                suffix = (
                    f" for transfer generation {transfer_generation}"
                    if transfer_generation is not None
                    else ""
                )
                raise StaleMolecularProjectionError(
                    f"molecular revision {self._molecular_revision} is stale; "
                    f"current revision is {current}{suffix}"
                )
            message = self._builder()
            if message.get("op") != "load_molsys_payload" or "payload" not in message:
                raise ValueError("lazy molecular builder returned an invalid load message")
            self._materialized = message
        return deepcopy(self._materialized)

    def __getitem__(self, key: str) -> Any:
        if key == "payload":
            return self.materialize()["payload"]
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "payload":
            try:
                return self.materialize()["payload"]
            except KeyError:
                return default
        return super().get(key, default)

    def __deepcopy__(self, memo):
        # The producer is immutable from consumers' perspective; explicit
        # projection seams materialize and defensively copy its result.
        return self


def is_lazy_molecular_message(message: Any) -> bool:
    return isinstance(message, LazyMolecularMessage)
