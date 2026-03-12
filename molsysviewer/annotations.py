from __future__ import annotations

from typing import Any

import molsysmt as msm
from smonitor import signal

from ._private.arg_digestion import digest
from .layers import Layer


class AnnotationsManager:
    """Annotation manager bound to a MolSysView."""

    def __init__(self, view: Any) -> None:
        self._view = view

    def _ensure_layer(self, tag: str) -> Layer:
        if tag not in self._view._layers:  # noqa: SLF001
            self._view._layers[tag] = Layer(self._view, tag, kind="annotation", meta={})  # noqa: SLF001
        else:
            self._view._layers[tag].kind = "annotation"  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001

    @signal(tags=["annotation"])
    @digest()
    def add_label(
        self,
        text: str,
        group_index: Any,
        tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        """Add a persistent label anchored to a single group."""
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded. Load a system before adding labels.")

        if not isinstance(group_index, list) or len(group_index) != 1:
            raise ValueError("add_label() currently requires exactly one group_index.")

        group_idx = int(group_index[0])
        atom_indices = msm.select(
            self._view._molsys,  # noqa: SLF001
            selection=f"group_index=={group_idx}",
            syntax="MolSysMT",
            skip_digestion=True,
        )
        atom_indices = [int(ii) for ii in atom_indices]
        if len(atom_indices) == 0:
            raise ValueError(f"Group index {group_idx} did not resolve to any atoms.")

        layer_tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        layer = self._ensure_layer(layer_tag)

        self._view._send(  # noqa: SLF001
            {
                "op": "add_label",
                "tag": layer_tag,
                "options": {
                    "text": text,
                    "tag": layer_tag,
                    "atom_indices": atom_indices,
                },
            }
        )
        return layer


__all__ = ["AnnotationsManager"]
