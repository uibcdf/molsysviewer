from __future__ import annotations

from typing import Any

from ._private.arg_digestion import digest


class Whole:
    """Wrapper for operations on the whole structure (non-deletable, non-retaggable)."""

    def __init__(self, view: Any) -> None:
        self._view = view
        self._representation: str | None = None
        self._preset: str | None = None
        self._repr_params: dict[str, Any] = {}

    @digest()
    def set_representation(self, representation: str | None = None, *, preset: str | None = None, skip_digestion: bool = False, **params: Any) -> None:
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

    @digest()
    def show(self, skip_digestion: bool = False) -> None:
        """Show the global representation(s)."""
        self._view._global_hidden = False  # noqa: SLF001
        self._view._send({"op": "show_global", "target": "global"})  # noqa: SLF001

    @digest()
    def hide(self, skip_digestion: bool = False) -> None:
        """Hide the global representation(s)."""
        self._view._global_hidden = True  # noqa: SLF001
        self._view._send({"op": "hide_global", "target": "global"})  # noqa: SLF001

    # --- MolSysMT query helpers (delegated to MolSysView) ---

    @digest()
    def select(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Select indices from the whole system (delegates to `MolSysView.select`)."""
        return self._view.select(*args, skip_digestion=skip_digestion, **kwargs)

    @digest()
    def get(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Retrieve values from the whole system (delegates to `MolSysView.get`)."""
        return self._view.get(*args, skip_digestion=skip_digestion, **kwargs)

    @digest()
    def info(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Show a summary table for the whole system (delegates to `MolSysView.info`)."""
        return self._view.info(*args, skip_digestion=skip_digestion, **kwargs)

    @digest()
    def append_structures(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Append structures to the underlying system (delegates to `MolSysView.append_structures`)."""
        return self._view.append_structures(*args, skip_digestion=skip_digestion, **kwargs)

    @digest()
    def set(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Set attributes on the underlying system (delegates to `MolSysView.set`)."""
        return self._view.set(*args, skip_digestion=skip_digestion, **kwargs)

    @digest()
    def add(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Add elements from another system (delegates to `MolSysView.add`)."""
        return self._view.add(*args, skip_digestion=skip_digestion, **kwargs)

    @digest()
    def remove(self, *args: Any, skip_digestion: bool = False, **kwargs: Any):
        """Remove atoms/structures from the system (delegates to `MolSysView.remove`)."""
        return self._view.remove(*args, skip_digestion=skip_digestion, **kwargs)
