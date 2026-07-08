from __future__ import annotations

from typing import Any, Literal

from smonitor import signal

from ._private.arg_digestion import digest

SelectionCombineOperation = Literal["replace", "add", "subtract", "intersect", "invert"]


def _dedupe_indices(indices: Any) -> list[int]:
    seen: set[int] = set()
    out: list[int] = []
    for item in indices or []:
        value = int(item)
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _combine(
    current: Any,
    incoming: Any,
    op: SelectionCombineOperation,
    *,
    universe: Any | None = None,
) -> list[int]:
    """Combine atom-index selections with the shared selection operation vocabulary."""
    current_indices = _dedupe_indices(current)
    incoming_indices = _dedupe_indices(incoming)
    incoming_set = set(incoming_indices)

    if op == "replace":
        return incoming_indices
    if op == "add":
        current_set = set(current_indices)
        return current_indices + [item for item in incoming_indices if item not in current_set]
    if op == "subtract":
        return [item for item in current_indices if item not in incoming_set]
    if op == "intersect":
        return [item for item in current_indices if item in incoming_set]
    if op == "invert":
        base = _dedupe_indices(incoming_indices if universe is None else universe)
        current_set = set(current_indices)
        return [item for item in base if item not in current_set]

    raise ValueError(f"Unsupported selection combine operation: {op!r}.")


def _empty_payload() -> dict[str, Any]:
    return {
        "event": "interaction_active_selection_changed",
        "source_kind": "empty",
        "element_level": "none",
        "target_level": "none",
        "items": [],
        "atom_indices": [],
        "group_indices": [],
        "component_indices": [],
        "chain_indices": [],
        "molecule_indices": [],
        "entity_indices": [],
        "count_atoms": 0,
        "count_groups": 0,
        "count_shapes": 0,
        "count_annotations": 0,
    }


class ActiveSelection:
    """Public wrapper around the current interaction-driven active selection."""

    def __init__(self, view: Any) -> None:
        self._view = view

    def _event(self) -> dict[str, Any]:
        event = self._view.get_last_active_selection_event()
        if event is None:
            return _empty_payload()
        return dict(event)

    @property
    def source_kind(self) -> str:
        return str(self._event().get("source_kind", "empty"))

    @property
    def element_level(self) -> str:
        return str(self._event().get("element_level", "none"))

    @property
    def target_level(self) -> str:
        return str(self._event().get("target_level", "none"))

    @property
    def items(self) -> list[dict[str, Any]]:
        return list(self._event().get("items", []))

    @property
    def atom_indices(self) -> list[int]:
        return list(self._event().get("atom_indices", []))

    @property
    def group_indices(self) -> list[int]:
        return list(self._event().get("group_indices", []))

    @property
    def component_indices(self) -> list[int]:
        return list(self._event().get("component_indices", []))

    @property
    def chain_indices(self) -> list[int]:
        return list(self._event().get("chain_indices", []))

    @property
    def molecule_indices(self) -> list[int]:
        return list(self._event().get("molecule_indices", []))

    @property
    def entity_indices(self) -> list[int]:
        return list(self._event().get("entity_indices", []))

    @signal(tags=["selection", "query"])
    @digest()
    def info(self, skip_digestion: bool = False) -> dict[str, Any]:
        """Return the current active-selection payload."""
        return self._event()

    @signal(tags=["selection", "query"])
    @digest()
    def is_empty(self, skip_digestion: bool = False) -> bool:
        """Return whether the active selection is empty."""
        return (self.source_kind == "empty") or (len(self.atom_indices) == 0 and len(self.items) == 0)

    @signal(tags=["selection", "camera"])
    @digest()
    def focus(
        self,
        *,
        duration: Any = '250 ms',
        duration_ms: Any | None = None,
        extra_radius: Any = '4.0 angstroms',
        min_radius: Any = '1.0 angstroms',
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on the current active selection."""
        if self.is_empty(skip_digestion=True):
            raise ValueError("No active selection stored. Select something before calling active_selection.focus().")
        self._view.zoom(
            selection=self.atom_indices,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(tags=["selection"])
    @digest()
    def set(
        self,
        selection: Any = "all",
        *,
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
    ) -> "ActiveSelection":
        """Set the active selection to the atoms matching ``selection``.

        ``selection`` is a MolSysMT selection expression or an explicit list of
        atom indices, both in the **loaded system** (``view._molsys``) index space —
        the same space the frontend uses. Updates the Python-side active-selection
        payload and the frontend runtime, mirroring an interaction-driven selection.
        A selection that resolves to no atoms clears the active selection. Returns
        ``self``. Note: this only *reads* the loaded system (via ``msm.get``) to derive
        metadata; it never mutates it and never queries the original input form.
        """
        import molsysmt as msm

        molsys = self._view._molsys  # noqa: SLF001
        if molsys is None:
            raise ValueError("No molecular system loaded.")

        # Resolve the target to atom indices in _molsys' index space.
        if syntax == "Indices" or not isinstance(selection, str):
            raw_indices = [] if selection is None else selection
            atom_indices = [int(i) for i in raw_indices]
        else:
            atom_indices = [
                int(i)
                for i in msm.select(molsys, selection=selection, element="atom", syntax=syntax, skip_digestion=True)
            ]
        atom_indices = list(dict.fromkeys(atom_indices))  # dedupe, keep incorporation order
        if not atom_indices:
            self.clear(skip_digestion=True)
            return self

        # Derive the full per-level metadata from _molsys (in-memory MolSys) — a
        # read-only query; never against the original input (view.molecular_system).
        levels = ("group", "component", "chain", "molecule", "entity")
        metadata = msm.get(
            molsys,
            element="atom",
            selection=atom_indices,
            output_type="dictionary",
            skip_digestion=True,
            **{f"{level}_index": True for level in levels},
        )
        level_indices = {
            level: sorted({int(value) for value in metadata[f"{level}_index"]})
            for level in levels
        }

        # _molsys index space == frontend index space, so send the atoms as-is.
        self._view._send({  # noqa: SLF001
            "op": "set_active_selection",
            "atom_indices": list(atom_indices),
        })
        self._view._last_active_selection_event = {  # noqa: SLF001
            "event": "interaction_active_selection_changed",
            "source_kind": "element",
            "element_level": "atom",
            "target_level": "none",
            "items": [],
            "atom_indices": list(atom_indices),
            "group_indices": level_indices["group"],
            "component_indices": level_indices["component"],
            "chain_indices": level_indices["chain"],
            "molecule_indices": level_indices["molecule"],
            "entity_indices": level_indices["entity"],
            "count_atoms": len(atom_indices),
            "count_groups": len(level_indices["group"]),
            "count_shapes": 0,
            "count_annotations": 0,
        }
        if hasattr(self._view, "_selection_recipe_step") and hasattr(self._view, "_set_active_selection_recipe"):
            source = "query" if isinstance(selection, str) and syntax != "Indices" else "indices"
            step = self._view._selection_recipe_step(  # noqa: SLF001
                source=source,
                op="replace",
                atom_indices=atom_indices,
                expression=selection if source == "query" else None,
                syntax=syntax,
                element="atom",
            )
            self._view._set_active_selection_recipe([step])  # noqa: SLF001
        return self

    @signal(tags=["selection"])
    @digest()
    def clear(self, skip_digestion: bool = False) -> None:
        """Clear the active selection in both Python and the frontend runtime."""
        self._view._send({"op": "clear_active_selection"})  # noqa: SLF001
        self._view._last_active_selection_event = _empty_payload()  # noqa: SLF001
        if hasattr(self._view, "_set_active_selection_recipe"):
            self._view._set_active_selection_recipe([])  # noqa: SLF001

    @signal(tags=["selection", "region"])
    @digest()
    def new_region(
        self,
        *,
        tag: str | None = None,
        representation: str | None = None,
        skip_digestion: bool = False,
        **params: Any,
    ):
        """Create a reproducible region from the current active selection."""
        return self._view.new_region_from_active_selection(
            tag=tag,
            representation=representation,
            skip_digestion=True,
            **params,
        )

    @signal(tags=["selection", "annotation"])
    @digest()
    def add_label(
        self,
        text: str,
        *,
        tag: str | None = None,
        skip_digestion: bool = False,
    ):
        """Create a persistent label from the current active selection."""
        return self._view.annotations.add_label_from_active_selection(
            text=text,
            tag=tag,
            skip_digestion=True,
        )

    @signal(tags=["selection"])
    @digest()
    def save(self, tag: str, skip_digestion: bool = False):
        """Persist the current active selection as a named selection."""
        return self._view.selections.add_from_active_selection(tag=tag, skip_digestion=True)


__all__ = ["ActiveSelection", "_combine"]
