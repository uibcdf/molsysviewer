from __future__ import annotations

from typing import Any

from smonitor import signal

from ._private.argdigest import digest


def _empty_payload(event_name: str) -> dict[str, Any]:
    return {
        "event": event_name,
        "kind": "empty",
        "atom_indices": [],
    }


class InteractionTarget:
    """Lightweight public wrapper around the last hover/context interaction target."""

    def __init__(self, view: Any, *, event_getter_name: str, empty_event_name: str) -> None:
        self._view = view
        self._event_getter_name = event_getter_name
        self._empty_event_name = empty_event_name

    def _event(self) -> dict[str, Any]:
        getter = getattr(self._view, self._event_getter_name)
        event = getter()
        if event is None:
            return _empty_payload(self._empty_event_name)
        return dict(event)

    @property
    def event(self) -> str:
        return str(self._event().get("event", self._empty_event_name))

    @property
    def kind(self) -> str:
        return str(self._event().get("kind", "empty"))

    @property
    def atom_indices(self) -> list[int]:
        return list(self._event().get("atom_indices", []))

    @property
    def tag(self) -> str | None:
        tag = self._event().get("tag")
        return tag if isinstance(tag, str) else None

    @property
    def text(self) -> str | None:
        text = self._event().get("text")
        return text if isinstance(text, str) else None

    @property
    def page_x(self) -> int | None:
        value = self._event().get("page_x")
        return int(value) if isinstance(value, (int, float)) else None

    @property
    def page_y(self) -> int | None:
        value = self._event().get("page_y")
        return int(value) if isinstance(value, (int, float)) else None

    @signal(tags=["interaction", "query"])
    @digest()
    def info(self, skip_digestion: bool = False) -> dict[str, Any]:
        return self._event()

    @signal(tags=["interaction", "query"])
    @digest()
    def is_empty(self, skip_digestion: bool = False) -> bool:
        event = self._event()
        state = event.get("kind")
        if state == "telemetry_disabled":
            raise RuntimeError("hover telemetry is disabled")
        if state == "telemetry_waiting":
            raise RuntimeError("hover telemetry is enabled but no hover event has been received")
        return event.get("kind", "empty") == "empty" and len(event.get("atom_indices", []) or []) == 0


__all__ = ["InteractionTarget"]
