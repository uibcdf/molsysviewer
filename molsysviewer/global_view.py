from __future__ import annotations

from typing import Any, Optional


class GlobalView:
    """Wrapper for operations on the whole structure (non-deletable, non-retaggable)."""

    def __init__(self, view: Any) -> None:
        self._view = view
        self._representation: Optional[str] = None
        self._repr_params: dict[str, Any] = {}

    def set_representation(self, representation: str, **params: Any) -> None:
        """Set or update the global representation for the whole structure.

        If the global representation was hidden, this call will show it again.
        """
        normalized = self._view._normalize_representation_type(representation)  # noqa: SLF001
        self._representation = normalized
        self._repr_params = params or {}
        self._view._send(  # noqa: SLF001
            {
                "op": "set_global_representation",
                "representation": normalized,
                "params": self._repr_params,
            }
        )

    def show(self) -> None:
        """Show the global representation(s)."""
        self._view._send({"op": "show_global"})  # noqa: SLF001

    def hide(self) -> None:
        """Hide the global representation(s)."""
        self._view._send({"op": "hide_global"})  # noqa: SLF001
