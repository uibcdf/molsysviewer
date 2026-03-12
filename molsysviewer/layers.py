from __future__ import annotations

from typing import Any, Dict, Optional

from smonitor import signal

from ._private.arg_digestion import digest


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
        self._hidden = False

    def _send(self, op: str, **payload: Any) -> None:
        if not self._active:
            return
        msg = {"op": op, "tag": self.tag, **payload}
        self._view._send(msg)  # noqa: SLF001

    def _send_create(self) -> None:
        self._send("create_layer", kind=self.kind, meta=self.meta)

    @signal(tags=["visibility", "layer"])
    @digest()
    def show(self, skip_digestion: bool = False) -> None:
        """Show this layer (all contained visuals)."""
        self._hidden = False
        self._send("show_layer")

    @signal(tags=["visibility", "layer"])
    @digest()
    def hide(self, skip_digestion: bool = False) -> None:
        """Hide this layer (all contained visuals)."""
        self._hidden = True
        self._send("hide_layer")

    @signal(
        tags=["layer"],
        extra_factory=lambda args, kwargs: {"new_tag": kwargs.get("new_tag", args[1] if len(args) > 1 else None)},
    )
    @digest()
    def delete(self, skip_digestion: bool = False) -> None:
        """Remove this layer and its visuals."""
        if not self._active:
            return
        self._view._send({"op": "delete_layer", "tag": self.tag})  # noqa: SLF001
        self._active = False
        self._view._unregister_layer(self.tag)  # noqa: SLF001

    @signal(tags=["layer"])
    @digest()
    def set_tag(self, new_tag: str, skip_digestion: bool = False) -> None:
        """Change this layer's tag (and update the registry)."""
        if not self._active or new_tag == self.tag:
            return
        old_tag = self.tag
        self._view._send({"op": "set_layer_tag", "tag": old_tag, "new_tag": new_tag})  # noqa: SLF001
        self.tag = new_tag
        self._view._reregister_layer(old_tag, new_tag, self)  # noqa: SLF001
