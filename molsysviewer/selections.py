from __future__ import annotations

from typing import Any

import molsysmt as msm
from smonitor import signal

from ._private.arg_digestion import digest


class Selection:
    """Persistent named selection stored by atom indices."""

    def __init__(self, view: Any, tag: str) -> None:
        self._view = view
        self.tag = tag
        self._active = True

    def _record(self) -> dict[str, Any]:
        record = self._view.selections._record_for_tag(self.tag)  # noqa: SLF001
        if record is None:
            raise ValueError(f"No selection record found for tag {self.tag!r}.")
        return record

    @signal(tags=["selection", "query"])
    @digest()
    def info(self, skip_digestion: bool = False) -> dict[str, Any]:
        """Return compact metadata for this persistent selection."""
        return self._view.selections.info(self.tag, skip_digestion=True)  # noqa: SLF001

    @property
    def atom_indices(self) -> list[int]:
        return list(self.info(skip_digestion=True).get("atom_indices", []))

    @property
    def group_indices(self) -> list[int]:
        return list(self.info(skip_digestion=True).get("group_indices", []))

    @signal(tags=["selection", "camera"])
    @digest()
    def focus(
        self,
        *,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "4.0 angstroms",
        min_radius: Any = "1.0 angstroms",
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on this persistent selection."""
        atom_indices = self.atom_indices
        if len(atom_indices) == 0:
            raise ValueError(f"Selection {self.tag!r} does not resolve to any atoms.")
        self._view.zoom(  # noqa: SLF001
            selection=atom_indices,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(tags=["selection"])
    @digest()
    def activate(self, skip_digestion: bool = False):
        """Restore this persistent selection as the current active selection."""
        info = self.info(skip_digestion=True)
        atom_indices = info.get("atom_indices") or []
        if not isinstance(atom_indices, list) or len(atom_indices) == 0:
            raise ValueError(f"Selection {self.tag!r} does not resolve to any atoms.")
        self._view._send({  # noqa: SLF001
            "op": "set_active_selection",
            "atom_indices": list(atom_indices),
        })
        payload = {
            "event": "interaction_active_selection_changed",
            "source_kind": "element",
            "element_level": "group",
            "target_level": "none",
            "items": [],
            "atom_indices": list(info.get("atom_indices") or []),
            "group_indices": list(info.get("group_indices") or []),
            "component_indices": list(info.get("component_indices") or []),
            "chain_indices": list(info.get("chain_indices") or []),
            "molecule_indices": list(info.get("molecule_indices") or []),
            "entity_indices": list(info.get("entity_indices") or []),
            "count_atoms": int(info.get("n_atoms") or 0),
            "count_groups": len(list(info.get("group_indices") or [])),
            "count_shapes": 0,
            "count_annotations": 0,
        }
        self._view._last_active_selection_event = payload  # noqa: SLF001
        return self._view.active_selection  # noqa: SLF001

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
        """Create a region from this persistent selection."""
        info = self.info(skip_digestion=True)
        atom_indices = info.get("atom_indices") or []
        if not isinstance(atom_indices, list) or len(atom_indices) == 0:
            raise ValueError(f"Selection {self.tag!r} does not resolve to any atoms.")
        return self._view.new_region(  # noqa: SLF001
            tag=tag,
            selection="all",
            atom_indices=list(atom_indices),
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
        """Create a persistent label from this persistent selection."""
        info = self.info(skip_digestion=True)
        group_indices = info.get("group_indices") or []
        if not isinstance(group_indices, list) or len(group_indices) != 1:
            raise ValueError("Selection.add_label() currently requires exactly one resolved group.")
        return self._view.annotations.add_label(  # noqa: SLF001
            text=text,
            group_index=[int(group_indices[0])],
            tag=tag,
            skip_digestion=True,
        )

    @signal(tags=["selection"])
    @digest()
    def set_tag(self, new_tag: str, skip_digestion: bool = False):
        """Rename this persistent selection."""
        return self._view.selections.set_tag(self.tag, new_tag, skip_digestion=True)  # noqa: SLF001

    @signal(tags=["selection"])
    @digest()
    def delete(self, skip_digestion: bool = False) -> None:
        """Delete this persistent selection."""
        self._view.selections.delete(self.tag, skip_digestion=True)  # noqa: SLF001


class SelectionsManager:
    """Persistent named selections bound to a MolSysView."""

    def __init__(self, view: Any) -> None:
        self._view = view

    def __getitem__(self, tag: str) -> Selection:
        sel = self.get(tag, skip_digestion=True)
        if sel is None:
            raise KeyError(tag)
        return sel

    def __iter__(self):
        for tag in self.tags:
            yield self._selection(tag)

    def _selection(self, tag: str) -> Selection:
        if tag not in self._view._selections:  # noqa: SLF001
            self._view._selections[tag] = Selection(self._view, tag)  # noqa: SLF001
        return self._view._selections[tag]  # noqa: SLF001

    def _record_for_tag(self, tag: str) -> dict[str, Any] | None:
        for record in self._view._selection_history:  # noqa: SLF001
            if record.get("tag") == tag:
                return dict(record)
        return None

    @property
    def tags(self) -> list[str]:
        """Return the stored persistent selection tags."""
        return [str(record.get("tag")) for record in self._view._selection_history if isinstance(record.get("tag"), str)]  # noqa: SLF001

    @signal(tags=["selection"])
    @digest()
    def contains(self, tag: str, skip_digestion: bool = False) -> bool:
        """Return whether a persistent selection exists for ``tag``."""
        return self._record_for_tag(tag) is not None

    @signal(tags=["selection"])
    @digest()
    def get(self, tag: str, skip_digestion: bool = False) -> Selection | None:
        """Return the named selection wrapper for ``tag`` if present."""
        if not self.contains(tag, skip_digestion=True):
            return None
        return self._selection(tag)

    @signal(tags=["selection"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return the replayable persistent-selection records."""
        return [dict(record) for record in self._view._selection_history]  # noqa: SLF001

    @signal(tags=["selection"])
    @digest()
    def count(self, skip_digestion: bool = False) -> int:
        """Return the number of persistent selections."""
        return len(self._view._selection_history)  # noqa: SLF001

    @signal(tags=["selection"])
    @digest()
    def activate(self, tag: str, skip_digestion: bool = False):
        """Restore a persistent selection as the current active selection."""
        selection = self.get(tag, skip_digestion=True)
        if selection is None:
            raise ValueError(f"No persistent selection found for tag {tag!r}.")
        return selection.activate(skip_digestion=True)

    @signal(tags=["selection", "query"])
    @digest()
    def info(self, tag: str | None = None, skip_digestion: bool = False) -> dict[str, Any] | list[dict[str, Any]]:
        """Return compact selection metadata for one tag or all persistent selections."""

        def summarize(record: dict[str, Any]) -> dict[str, Any]:
            atom_indices = record.get("atom_indices")
            atom_indices = atom_indices if isinstance(atom_indices, list) else []
            group_indices = list(record.get("group_indices") or [])
            component_indices = list(record.get("component_indices") or [])
            chain_indices = list(record.get("chain_indices") or [])
            molecule_indices = list(record.get("molecule_indices") or [])
            entity_indices = list(record.get("entity_indices") or [])
            if self._view._molsys is not None and len(atom_indices) > 0:  # noqa: SLF001
                try:
                    group_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._view._molsys,  # noqa: SLF001
                                    element="atom",
                                    selection=atom_indices,
                                    group_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    component_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._view._molsys,  # noqa: SLF001
                                    element="atom",
                                    selection=atom_indices,
                                    component_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    chain_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._view._molsys,  # noqa: SLF001
                                    element="atom",
                                    selection=atom_indices,
                                    chain_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    molecule_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._view._molsys,  # noqa: SLF001
                                    element="atom",
                                    selection=atom_indices,
                                    molecule_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                    entity_indices = sorted(
                        {
                            int(ii)
                            for ii in (
                                msm.get(
                                    self._view._molsys,  # noqa: SLF001
                                    element="atom",
                                    selection=atom_indices,
                                    entity_index=True,
                                    output_type="values",
                                    skip_digestion=True,
                                )
                                or []
                            )
                            if ii is not None
                        }
                    )
                except Exception:
                    pass
            return {
                "kind": "selection",
                "tag": record.get("tag"),
                "source_kind": record.get("source_kind", "element"),
                "element_level": record.get("element_level", "group"),
                "target_level": record.get("target_level", "none"),
                "n_atoms": len(atom_indices),
                "atom_indices": list(atom_indices),
                "group_indices": group_indices,
                "component_indices": component_indices,
                "chain_indices": chain_indices,
                "molecule_indices": molecule_indices,
                "entity_indices": entity_indices,
                "count_items": len(record.get("items") or []),
            }

        records = self.records(skip_digestion=True)
        if tag is None:
            return [summarize(record) for record in records]

        for record in records:
            if record.get("tag") == tag:
                return summarize(record)
        raise ValueError(f"No persistent selection found for tag {tag!r}.")

    def _store_selection_record(
        self,
        tag: str,
        atom_indices: list[int],
        *,
        source_kind: str = "element",
        element_level: str = "group",
        target_level: str = "none",
        items: list[dict[str, Any]] | None = None,
        group_indices: list[int] | None = None,
        component_indices: list[int] | None = None,
        chain_indices: list[int] | None = None,
        molecule_indices: list[int] | None = None,
        entity_indices: list[int] | None = None,
    ) -> Selection:
        """Internal: build and send a save_selection message, return the Selection wrapper."""
        if self.contains(tag, skip_digestion=True):
            raise ValueError(f"A persistent selection with tag {tag!r} already exists.")
        msg = {
            "op": "save_selection",
            "tag": tag,
            "source_kind": source_kind,
            "element_level": element_level,
            "target_level": target_level,
            "items": [dict(item) for item in (items or [])],
            "atom_indices": atom_indices,
            "group_indices": list(group_indices or []),
            "component_indices": list(component_indices or []),
            "chain_indices": list(chain_indices or []),
            "molecule_indices": list(molecule_indices or []),
            "entity_indices": list(entity_indices or []),
        }
        self._view._send(msg)  # noqa: SLF001
        return self._selection(tag)

    @signal(tags=["selection"])
    @digest()
    def add(
        self,
        tag: str,
        *,
        atom_indices: list[int],
        items: list[dict[str, Any]] | None = None,
        skip_digestion: bool = False,
    ) -> "Selection":
        """Store a persistent selection directly from explicit atom indices.

        Parameters
        ----------
        tag
            Unique identifier for this persistent selection.
        atom_indices
            Explicit list of atom indices (integers).
        items
            Optional list of item descriptors stored alongside the selection.
        """
        resolved = [int(i) for i in atom_indices]
        if len(resolved) == 0:
            raise ValueError("Persistent selections require non-empty atom indices.")
        return self._store_selection_record(tag, resolved, items=items)

    @signal(tags=["selection"])
    @digest()
    def add_selection(
        self,
        tag: str,
        selection: Any = "all",
        *,
        element: str = "atom",
        mask: Any = None,
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
    ) -> Selection:
        """Store a persistent selection by MolSysMT selection expression.

        The signature mirrors ``msm.select()``: *selection* can be a string
        query, a list of integer indices (interpreted at *element* level), or
        ``"all"``.  *element* controls which hierarchy level the indices refer
        to (``"atom"``, ``"group"``, ``"chain"``, etc.).  *mask* restricts
        the search universe.

        Parameters
        ----------
        tag
            Unique identifier for this persistent selection.
        selection
            MolSysMT selection string or integer index list.
        element
            Hierarchy level of *selection* indices (default ``"atom"``).
        mask
            Additional atom mask to restrict the selection universe.
        syntax
            Selection syntax (default ``"MolSysMT"``).
        """
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded.")
        resolved = [
            int(i)
            for i in msm.select(
                self._view._molsys,  # noqa: SLF001
                selection=selection,
                element=element,
                mask=mask,
                syntax=syntax,
                skip_digestion=True,
            )
        ]
        if len(resolved) == 0:
            raise ValueError("Persistent selections require non-empty atom indices.")
        return self._store_selection_record(tag, resolved)

    @signal(tags=["selection", "interaction"])
    @digest()
    def add_from_active_selection(self, tag: str, skip_digestion: bool = False) -> Selection:
        """Persist the current active selection as a named selection."""
        event = self._view.get_last_active_selection_event()  # noqa: SLF001
        if event is None:
            raise ValueError("No active selection stored. Select something before saving a named selection.")
        atom_indices = event.get("atom_indices") or []
        if not isinstance(atom_indices, list) or len(atom_indices) == 0:
            raise ValueError("The current active selection does not resolve to any atoms.")
        return self._store_selection_record(
            tag,
            list(atom_indices),
            source_kind=str(event.get("source_kind", "element")),
            element_level=str(event.get("element_level", "group")),
            target_level=str(event.get("target_level", "none")),
            items=[dict(item) for item in (event.get("items") or [])],
            group_indices=list(event.get("group_indices") or []),
            component_indices=list(event.get("component_indices") or []),
            chain_indices=list(event.get("chain_indices") or []),
            molecule_indices=list(event.get("molecule_indices") or []),
            entity_indices=list(event.get("entity_indices") or []),
        )

    @signal(tags=["selection"])
    @digest()
    def set_tag(self, tag: str, new_tag: str, skip_digestion: bool = False) -> Selection:
        """Rename a persistent selection."""
        if not self.contains(tag, skip_digestion=True):
            raise ValueError(f"No persistent selection found for tag {tag!r}.")
        if tag == new_tag:
            return self._selection(tag)
        if self.contains(new_tag, skip_digestion=True):
            raise ValueError(f"A persistent selection with tag {new_tag!r} already exists.")
        self._view._send({"op": "set_selection_tag", "tag": tag, "new_tag": new_tag})  # noqa: SLF001
        selection = self._view._selections.pop(tag, None)  # noqa: SLF001
        if selection is not None:
            selection.tag = new_tag
            self._view._selections[new_tag] = selection  # noqa: SLF001
        return self._selection(new_tag)

    @signal(tags=["selection"])
    @digest()
    def delete(self, tag: str, skip_digestion: bool = False) -> None:
        """Delete a persistent selection."""
        if not self.contains(tag, skip_digestion=True):
            raise ValueError(f"No persistent selection found for tag {tag!r}.")
        self._view._send({"op": "delete_selection", "tag": tag})  # noqa: SLF001
        self._view._selections.pop(tag, None)  # noqa: SLF001

    @signal(tags=["selection"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False) -> None:
        """Clear one or all persistent selections."""
        if tag is None:
            self._view._send({"op": "clear_selections"})  # noqa: SLF001
            self._view._selections.clear()  # noqa: SLF001
            return
        self.delete(tag, skip_digestion=True)


__all__ = ["Selection", "SelectionsManager"]
