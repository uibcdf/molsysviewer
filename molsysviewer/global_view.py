from __future__ import annotations

from typing import Any


class GlobalView:
    """Wrapper for operations on the whole structure (non-deletable, non-retaggable)."""

    def __init__(self, view: Any) -> None:
        self._view = view
        self._representation: str | None = None
        self._preset: str | None = None
        self._repr_params: dict[str, Any] = {}

    def set_representation(self, representation: str | None = None, *, preset: str | None = None, **params: Any) -> None:
        """Set or update the global representation for the whole structure.

        If the global representation was hidden, this call will show it again.

        Parameters
        ----------
        representation
            Simple representation type (e.g., cartoon, ball-and-stick, line). Ignored if `preset`
            is provided.
        preset
            Optional Mol* preset (`auto`, `atomic-detail`, `polymer-and-ligand`, `polymer-cartoon`,
            `coarse-surface`, `empty`). When provided, supersedes ``representation`` and applies
            the preconfigured style bundle.
        """
        normalized_preset = self._view._normalize_representation_preset(preset)  # noqa: SLF001
        user_preset_payload = self._view._resolve_user_preset(normalized_preset)  # noqa: SLF001
        normalized_repr = None if normalized_preset else self._view._normalize_representation_type(representation)  # noqa: SLF001
        self._preset = normalized_preset
        self._representation = normalized_repr
        self._repr_params = params or {}
        # Changing the representation implies showing the global view again.
        self._view._global_hidden = False  # noqa: SLF001
        payload = {
            "op": "set_global_representation",
            "representation": normalized_repr,
            "preset": normalized_preset if user_preset_payload is None else None,
            "params": self._repr_params,
        }
        if user_preset_payload is not None:
            payload["user_preset"] = user_preset_payload
        self._view._send(payload)  # noqa: SLF001

    def show(self) -> None:
        """Show the global representation(s)."""
        self._view._global_hidden = False  # noqa: SLF001
        self._view._send({"op": "show_global", "target": "global"})  # noqa: SLF001

    def hide(self) -> None:
        """Hide the global representation(s)."""
        self._view._global_hidden = True  # noqa: SLF001
        self._view._send({"op": "hide_global", "target": "global"})  # noqa: SLF001
