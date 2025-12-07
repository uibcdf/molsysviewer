from __future__ import annotations

from typing import Any, Dict, Optional


class Layer:
    """Wrapper for a non-structural visual layer (shapes, overlays) addressed by tag."""

    def __init__(
        self,
        view: Any,
        tag: str,
        *,
        kind: str | None = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._view = view
        self.tag = tag
        self.kind = kind
        self.meta = meta or {}
        self._active = True

    def _send(self, op: str, **payload: Any) -> None:
        if not self._active:
            return
        msg = {"op": op, "tag": self.tag, **payload}
        self._view._send(msg)  # noqa: SLF001

    def _send_create(self) -> None:
        self._send("create_layer", kind=self.kind, meta=self.meta)

    def show(self) -> None:
        """Show this layer (all contained visuals)."""
        self._send("show_layer")

    def hide(self) -> None:
        """Hide this layer (all contained visuals)."""
        self._send("hide_layer")

    def delete(self) -> None:
        """Remove this layer and its visuals."""
        if not self._active:
            return
        self._active = False
        self._send("delete_layer")
        self._view._unregister_layer(self.tag)  # noqa: SLF001

    def set_tag(self, new_tag: str) -> None:
        """Change this layer's tag (and update the registry)."""
        if not self._active or new_tag == self.tag:
            return
        old_tag = self.tag
        self.tag = new_tag
        self._send("set_layer_tag", new_tag=new_tag)
        self._view._reregister_layer(old_tag, new_tag, self)  # noqa: SLF001
