from __future__ import annotations

from typing import Any

from smonitor import signal

from ._private.arg_digestion import digest


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
        atom indices (in the molecular-system index space). Updates both the
        Python-side active-selection payload and the frontend runtime, mirroring
        an interaction-driven selection. A selection that resolves to no atoms
        clears the active selection. Returns ``self``.
        """
        import molsysmt as msm

        molsys = self._view._molsys  # noqa: SLF001
        if molsys is None:
            raise ValueError("No molecular system loaded.")

        atom_indices = [
            int(i)
            for i in msm.select(molsys, selection=selection, syntax=syntax, skip_digestion=True)
        ]
        if not atom_indices:
            self.clear(skip_digestion=True)
            return self

        group_indices = sorted(
            {
                int(g)
                for g in msm.get(
                    molsys,
                    element="atom",
                    selection=atom_indices,
                    group_index=True,
                    skip_digestion=True,
                )
            }
        )

        local_atoms = atom_indices
        if self._view._index_mapper is not None:  # noqa: SLF001
            local_atoms = self._view._index_mapper.to_local_atoms(atom_indices)  # noqa: SLF001

        self._view._send({  # noqa: SLF001
            "op": "set_active_selection",
            "atom_indices": list(local_atoms),
        })
        self._view._last_active_selection_event = {  # noqa: SLF001
            "event": "interaction_active_selection_changed",
            "source_kind": "element",
            "element_level": "atom",
            "target_level": "none",
            "items": [],
            "atom_indices": list(atom_indices),
            "group_indices": list(group_indices),
            "component_indices": [],
            "chain_indices": [],
            "molecule_indices": [],
            "entity_indices": [],
            "count_atoms": len(atom_indices),
            "count_groups": len(group_indices),
            "count_shapes": 0,
            "count_annotations": 0,
        }
        return self

    @signal(tags=["selection"])
    @digest()
    def clear(self, skip_digestion: bool = False) -> None:
        """Clear the active selection in both Python and the frontend runtime."""
        self._view._send({"op": "clear_active_selection"})  # noqa: SLF001
        self._view._last_active_selection_event = _empty_payload()  # noqa: SLF001

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


__all__ = ["ActiveSelection"]
