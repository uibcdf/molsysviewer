from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import Any, Dict, List, Optional
import warnings

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal
from ._private.argdigest import digest
from ._private.exceptions import ArgumentError
from ._private.smonitor_emit import emit_suppressed_exception
from .colors import expand_values_to_atoms, normalize_color
from .scene_history import records_scene_history


class Region:
    """Wrapper for a molecular region (Mol* component) addressed by tag."""

    def __init__(
        self,
        view: Any,
        tag: str,
        selection: str | Any,
        *,
        atom_indices: Optional[list[int]] = None,
        representation: str | None = None,
        repr_params: Optional[Dict[str, Any]] = None,
        uid: str | None = None,
        provenance: dict[str, Any] | None = None,
        mode: str = "static",
        frame_dependent: bool | None = None,
    ) -> None:
        self._view = view
        current_owner = getattr(view, "_current_scene_owner", None)
        self._owner = current_owner() if callable(current_owner) else None
        self.uid = uid or view._next_region_uid()  # noqa: SLF001
        self._tag = tag
        self.selection = selection
        self._atom_indices = tuple(atom_indices) if atom_indices is not None else None
        self._provenance = deepcopy(provenance) if provenance is not None else {"kind": "imported", "state_version": None}
        if frame_dependent is not None:
            self._provenance["frame_dependent"] = bool(frame_dependent)
        else:
            self._provenance.setdefault("frame_dependent", False)
        self._mode = "static"
        self._set_mode(mode)
        self._representation = representation
        self._preset: str | None = None
        self._repr_params = repr_params or {}
        self.order: int = view._next_region_order()  # noqa: SLF001
        self._active = True
        self._hidden = False
        # Layer membership (Contract B3, Phase 9): the tag of the layer this
        # region belongs to, or None for a region that belongs to no layer.
        self._layer: str | None = None

    @property
    def owner(self) -> str | None:
        """Creator attribution captured when this region was created."""
        return self._owner

    @property
    def atom_indices(self) -> tuple[int, ...] | None:
        return self._atom_indices

    def _set_atom_indices(self, atom_indices: Optional[list[int] | tuple[int, ...]]) -> None:
        self._atom_indices = tuple(int(index) for index in atom_indices) if atom_indices is not None else None

    @property
    def provenance(self):
        return MappingProxyType(deepcopy(self._provenance))

    @property
    def mode(self) -> str:
        return self._mode

    def _set_mode(self, mode: str) -> None:
        normalized = str(mode or "static").strip().lower()
        if normalized not in {"static", "dynamic"}:
            raise ValueError("Region.mode must be 'static' or 'dynamic'.")
        if normalized == "dynamic" and not self._can_be_dynamic():
            raise ValueError(f"Region {self.tag!r} has no re-evaluable recipe and cannot be dynamic.")
        previous = getattr(self, "_mode", None)
        if previous != normalized and hasattr(self._view, "_clear_dynamic_region_cache"):
            self._view._clear_dynamic_region_cache(self.uid)  # noqa: SLF001
        self._mode = normalized
        if (
            previous != normalized
            and hasattr(self._view, "_sync_region_summaries_runtime")
            and getattr(self._view, "_regions", {}).get(self.tag) is self
        ):
            self._view._sync_region_summaries_runtime()  # noqa: SLF001

    def _can_be_dynamic(self) -> bool:
        if not self._is_reevaluable_provenance(self._provenance):
            return False
        kind = self._provenance.get("kind")
        if kind in {"query", "split"}:
            return True
        if kind == "duplicate":
            source = self._view._region_by_uid(str(self._provenance.get("of")))  # noqa: SLF001
            return bool(source and source.mode == "dynamic")
        if kind == "complement":
            operands = [
                self._view._region_by_uid(str(uid))  # noqa: SLF001
                for uid in self._provenance.get("of", [])
            ]
            return bool(operands) and all(region is not None and region.mode == "dynamic" for region in operands)
        if kind == "boolean":
            operands = [
                self._view._region_by_uid(str(uid))  # noqa: SLF001
                for uid in self._provenance.get("operands", [])
            ]
            return bool(operands) and all(region is not None and region.mode == "dynamic" for region in operands)
        return False

    def _set_provenance(self, provenance: dict[str, Any]) -> None:
        self._provenance = deepcopy(provenance)
        self._provenance.setdefault("frame_dependent", False)
        if hasattr(self._view, "_clear_dynamic_region_cache"):
            self._view._clear_dynamic_region_cache(self.uid)  # noqa: SLF001
        if not self._is_reevaluable_provenance(self._provenance):
            self._mode = "static"

    def _freeze_broken_recipe(self, missing_uid: str) -> None:
        provenance = deepcopy(self._provenance)
        missing = [str(uid) for uid in provenance.get("missing", [])]
        if str(missing_uid) not in missing:
            missing.append(str(missing_uid))
        provenance["broken"] = True
        provenance["missing"] = missing
        self._set_provenance(provenance)
        self._mode = "static"

    @mode.setter
    def mode(self, value: str) -> None:
        self._set_mode(value)

    @property
    def frame_dependent(self) -> bool:
        return bool(self._provenance.get("frame_dependent", False))

    @property
    def dependencies(self) -> tuple[str, ...]:
        return tuple(self._dependency_uids_from_provenance(self._provenance))

    @property
    def dependents(self) -> tuple[str, ...]:
        return tuple(
            region.uid
            for region in self._view._regions.values()  # noqa: SLF001
            if self.uid in region.dependencies
        )

    @property
    def visible(self) -> bool:
        """Whether this region's own representation is currently shown."""
        return not self._hidden

    @property
    def layer(self) -> str | None:
        """The tag of the layer this region belongs to, or ``None``.

        Read-only; use :meth:`set_layer` / :meth:`remove_from_layer` to change
        it. Serialised in state v2 and honoured by layer show/hide/delete.
        """
        return self._layer

    def _set_layer_membership(self, layer_tag: str | None) -> None:
        """Internal: move this region into *layer_tag* (or out, when ``None``).

        Ensures the target layer group exists and cleans up a previous layer
        group left empty by the move. No signal/history — the public
        :meth:`set_layer` wraps this."""
        old_tag = self._layer
        text = layer_tag.strip() if isinstance(layer_tag, str) else None
        if text == "":
            raise ValueError("Layer tag must be a non-empty string, or None.")
        if text == old_tag:
            return
        if text is not None:
            self._view._ensure_layer_group(text, provenance="user")  # noqa: SLF001
        self._layer = text
        if isinstance(old_tag, str):
            self._view._cleanup_empty_layer_group(old_tag)  # noqa: SLF001

    @property
    def tag(self) -> str:
        """The region's tag. Read-only; use :meth:`rename` to change it."""
        return self._tag

    @property
    def representation(self) -> str | None:
        """The region's representation type. Read-only; use :meth:`set_representation`."""
        return self._representation

    @property
    def preset(self) -> str | None:
        """The region's preset. Read-only; use :meth:`set_representation`."""
        return self._preset

    @property
    def repr_params(self) -> Dict[str, Any]:
        """The region's representation params. Read-only; use :meth:`set_representation`."""
        return self._repr_params

    def _set_visual_fields(
        self,
        *,
        representation: str | None,
        preset: str | None,
        repr_params: Dict[str, Any],
    ) -> None:
        """Internal: set the cached visual state. Public writes go through
        :meth:`set_representation` / :meth:`reset_representation`."""
        self._representation = representation
        self._preset = preset
        self._repr_params = repr_params

    @staticmethod
    def _dependency_uids_from_provenance(provenance: dict[str, Any]) -> list[str]:
        kind = provenance.get("kind")
        if kind == "boolean":
            return [str(uid) for uid in provenance.get("operands", [])]
        if kind == "complement":
            return [str(uid) for uid in provenance.get("of", [])]
        if kind == "duplicate":
            uid = provenance.get("of")
            return [str(uid)] if uid is not None else []
        return []

    @staticmethod
    def _is_reevaluable_provenance(provenance: dict[str, Any]) -> bool:
        if provenance.get("broken"):
            return False
        return provenance.get("kind") in {"query", "split", "complement", "boolean", "duplicate"}

    # --- helpers ---

    def _has_own_visual(self) -> bool:
        return self.representation is not None or self.preset is not None

    def _scoped_indices_for_element(self, element: str):
        if self.atom_indices is None:
            return None

        if element == "atom":
            return sorted(set(self.atom_indices))

        if element == "system":
            return None

        if element == "bond":
            per_atom = msm.get(
                self._view._molsys,  # noqa: SLF001
                element="atom",
                selection=list(self.atom_indices),
                output_type="values",
                skip_digestion=True,
                bond_index=True,
            )
            scoped: list[int] = []
            for bonds in per_atom or []:
                for b in bonds or []:
                    try:
                        scoped.append(int(b))
                    except Exception as exc:
                        emit_suppressed_exception(
                            "Region._scoped_indices_for_element.bond_index",
                            exc,
                            context={"tag": self.tag, "value": repr(b)},
                        )
                        continue
            return sorted(set(scoped))

        element_to_atom_attribute = {
            "group": "group_index",
            "component": "component_index",
            "chain": "chain_index",
            "molecule": "molecule_index",
            "entity": "entity_index",
        }
        if element not in element_to_atom_attribute:
            raise ValueError(f"Unsupported element level: {element!r}")

        atom_attribute = element_to_atom_attribute[element]
        values = msm.get(
            self._view._molsys,  # noqa: SLF001
            element="atom",
            selection=list(self.atom_indices),
            output_type="values",
            skip_digestion=True,
            **{atom_attribute: True},
        )
        scoped: list[int] = []
        for value in values or []:
            try:
                if value is None:
                    continue
                scoped.append(int(value))
            except Exception as exc:
                emit_suppressed_exception(
                    "Region._scoped_indices_for_element.hierarchy_index",
                    exc,
                    context={"tag": self.tag, "element": element, "value": repr(value)},
                )
                continue
        return sorted(set(scoped))

    def _intersect_indices(self, a, b):
        if a is None:
            return b
        if b is None:
            return a
        aset = set(a)
        return sorted({ii for ii in b if ii in aset})

    def _require_atom_indices(self) -> tuple[int, ...]:
        if self.atom_indices is None:
            raise ValueError(f"Boolean region composition requires known atom_indices for region {self.tag!r}.")
        return tuple(int(index) for index in self.atom_indices)

    def _coerce_region_operand(self, other: Any) -> tuple[str, tuple[int, ...]]:
        if isinstance(other, Region):
            return other.tag, other._require_atom_indices()
        try:
            indices = tuple(int(index) for index in other)
        except TypeError as exc:
            raise TypeError("Boolean region composition expects another Region or an iterable of atom indices.") from exc
        return "indices", indices

    def _new_boolean_region(
        self,
        *,
        operation: str,
        others: tuple[Any, ...],
        atom_indices: list[int],
        tag: str | None,
        representation: str | None,
        repr_params: dict[str, Any],
    ) -> "Region":
        other_tags = [self._coerce_region_operand(other)[0] for other in others]
        base_tag = tag or self._view._unique_region_tag(  # noqa: SLF001
            f"{self.tag}_{operation}_{'_'.join(other_tags)}"
        )
        if not atom_indices:
            raise ValueError(f"Boolean region composition produced an empty region for {base_tag!r}.")
        operand_uids = [self.uid]
        region_others = [other for other in others if isinstance(other, Region)]
        has_non_region = len(region_others) != len(others)
        operand_uids.extend(other.uid for other in region_others)
        frame_dependent = self.frame_dependent or any(o.frame_dependent for o in region_others)
        # Dynamic only if every operand is a dynamic region; a raw-index or static
        # operand makes the result static (§R.5, closure under composition).
        mode = (
            "dynamic"
            if not has_non_region and self.mode == "dynamic"
            and all(o.mode == "dynamic" for o in region_others)
            else "static"
        )
        provenance: dict[str, Any] = {
            "kind": "boolean",
            "op": operation,
            "operands": operand_uids,
            "frame_dependent": frame_dependent,
        }
        if has_non_region:
            provenance["broken"] = True
            provenance["missing"] = ["non-region-operand"]
        region = self._view._new_region_impl(  # noqa: SLF001
            atom_indices=atom_indices,
            tag=base_tag,
            representation=representation,
            provenance=provenance,
            skip_digestion=True,
            **repr_params,
        )
        region.mode = mode
        return region

    def _combined_operand_indices(self, others: tuple[Any, ...]) -> list[int]:
        """Union of the atom sets of every operand (order-preserving)."""
        seen: set[int] = set()
        combined: list[int] = []
        for other in others:
            _, indices = self._coerce_region_operand(other)
            for index in indices:
                if index not in seen:
                    seen.add(index)
                    combined.append(index)
        return combined

    @records_scene_history
    def difference(
        self,
        *others: Any,
        tag: str | None = None,
        representation: str | None = None,
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> "Region":
        """Create a region with this region's atoms excluding every operand: ``A - (B | C | ...)``."""
        if not others:
            raise TypeError("difference() requires at least one operand.")
        lhs = self._require_atom_indices()
        rhs_set = set(self._combined_operand_indices(others))
        atom_indices = [index for index in lhs if index not in rhs_set]
        return self._new_boolean_region(
            operation="minus",
            others=others,
            atom_indices=atom_indices,
            tag=tag,
            representation=representation,
            repr_params=repr_params,
        )

    @records_scene_history
    def intersection(
        self,
        *others: Any,
        tag: str | None = None,
        representation: str | None = None,
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> "Region":
        """Create a region with atoms common to this region and every operand: ``A & B & C & ...``."""
        if not others:
            raise TypeError("intersection() requires at least one operand.")
        atom_indices = list(self._require_atom_indices())
        for other in others:
            _, rhs = self._coerce_region_operand(other)
            rhs_set = set(rhs)
            atom_indices = [index for index in atom_indices if index in rhs_set]
        return self._new_boolean_region(
            operation="and",
            others=others,
            atom_indices=atom_indices,
            tag=tag,
            representation=representation,
            repr_params=repr_params,
        )

    @records_scene_history
    def union(
        self,
        *others: Any,
        tag: str | None = None,
        representation: str | None = None,
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> "Region":
        """Create a region containing this region's atoms and every operand's: ``A | B | C | ...``."""
        if not others:
            raise TypeError("union() requires at least one operand.")
        seen: set[int] = set()
        atom_indices: list[int] = []
        for index in (*self._require_atom_indices(), *self._combined_operand_indices(others)):
            if index not in seen:
                seen.add(index)
                atom_indices.append(index)
        return self._new_boolean_region(
            operation="or",
            others=others,
            atom_indices=atom_indices,
            tag=tag,
            representation=representation,
            repr_params=repr_params,
        )

    def __sub__(self, other: Any) -> "Region":
        return self.difference(other)

    def __and__(self, other: Any) -> "Region":
        return self.intersection(other)

    def __or__(self, other: Any) -> "Region":
        return self.union(other)

    def _send(self, op: str, **payload: Any) -> None:
        if not self._active:
            return
        msg = {"op": op, "tag": self.tag, **payload}
        self._view._send_region_operation(msg)  # noqa: SLF001

    def _create_message(self, *, include_visual: bool = True) -> dict:
        """Build this region's current ``create_region`` op from live state.

        Shared by the live send path (``_send_create``) and the R2 popup snapshot
        projector so both regenerate the same message. Returns a fresh dict with
        copied indices; the caller may mutate it without affecting the region.
        For dynamic regions ``atom_indices`` are the materialized indices of the
        current frame.
        """
        atom_indices = None
        if self.atom_indices is not None:
            atom_indices = list(self.atom_indices)
        payload = {
            "op": "create_region",
            "tag": self.tag,
            "selection": self.selection,
            "atom_indices": atom_indices,
            "order": self.order,
        }
        if include_visual and self._has_own_visual():
            payload["representation"] = self.representation
            payload["params"] = dict(self.repr_params) if isinstance(self.repr_params, dict) else self.repr_params
        return payload

    def _send_create(self, *, include_visual: bool = True) -> None:
        payload = self._create_message(include_visual=include_visual)
        payload.pop("op", None)
        payload.pop("tag", None)
        self._send("create_region", **payload)
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    # --- public API ---

    @signal(tags=["region", "selection"])
    @digest()
    def select(
        self,
        selection="all",
        structure_indices="all",
        element="atom",
        mask=None,
        syntax="MolSysMT",
        skip_digestion=False,
    ):
        """Select indices, scoped to this region."""
        scope = self._scoped_indices_for_element(element)
        if scope is None:
            return self._view.select(  # noqa: SLF001
                selection=selection,
                structure_indices=structure_indices,
                element=element,
                mask=mask,
                syntax=syntax,
                skip_digestion=True,
            )

        if selection == "all" and (mask is None or mask == "all"):
            return scope

        selected = self._view.select(  # noqa: SLF001
            selection=selection,
            structure_indices=structure_indices,
            element=element,
            mask=None,
            syntax=syntax,
            skip_digestion=True,
        )
        if mask is not None and mask != "all":
            masked = self._view.select(  # noqa: SLF001
                selection=mask,
                structure_indices=structure_indices,
                element=element,
                mask=None,
                syntax=syntax,
                skip_digestion=True,
            )
            selected = self._intersect_indices(selected, masked)

        return self._intersect_indices(selected, scope)

    @signal(tags=["region", "query"])
    @digest()
    def get(
        self,
        element="system",
        selection="all",
        structure_indices="all",
        mask=None,
        syntax="MolSysMT",
        get_missing_bonds=True,
        output_type="values",
        skip_digestion=False,
        **kwargs,
    ):
        """Retrieve values, scoped to this region."""
        scope = self._scoped_indices_for_element(element)
        if scope is None:
            return self._view.get(  # noqa: SLF001
                element=element,
                selection=selection,
                structure_indices=structure_indices,
                mask=mask,
                syntax=syntax,
                get_missing_bonds=get_missing_bonds,
                output_type=output_type,
                skip_digestion=True,
                **kwargs,
            )

        if element == "system":
            return self._view.get(  # noqa: SLF001
                element=element,
                selection=selection,
                structure_indices=structure_indices,
                mask=mask,
                syntax=syntax,
                get_missing_bonds=get_missing_bonds,
                output_type=output_type,
                skip_digestion=True,
                **kwargs,
            )

        indices = self.select(
            selection=selection,
            structure_indices=structure_indices,
            element=element,
            mask=mask,
            syntax=syntax,
            skip_digestion=True,
        )
        return self._view.get(  # noqa: SLF001
            element=element,
            selection=indices,
            structure_indices=structure_indices,
            mask=None,
            syntax=syntax,
            get_missing_bonds=get_missing_bonds,
            output_type=output_type,
            skip_digestion=True,
            **kwargs,
        )

    def _region_info_records(self) -> list[dict]:
        """Build the region-state rows for the info table."""
        return [
            {
                "field": "tag",
                "value": self.tag,
            },
            {
                "field": "n atoms",
                "value": len(self.atom_indices) if self.atom_indices is not None else "all",
            },
            {
                "field": "visible",
                "value": not self._hidden,
            },
            {
                "field": "representation",
                "value": self.representation,
            },
            {
                "field": "preset",
                "value": self.preset,
            },
        ]

    @signal(tags=["region", "query"])
    @digest()
    def info(
        self,
        element="system",
        selection="all",
        syntax="MolSysMT",
        mask="all",
        output_type="styler",
        skip_digestion=False,
    ):
        """Show a summary table, scoped to this region.

        Returns a ``RegionInfo`` with a *molsys* section (filtered to the region's
        atoms) and a *region* section (tag, atom count, visibility, representation).
        When the region has no fixed atom set, delegates to the full viewer info.
        """
        from .viewer.core import RegionInfo  # noqa: PLC0415 – avoid circular import at module level

        # --- element != "system": scope to region atoms for that element ---
        scope = self._scoped_indices_for_element(element)
        if element != "system" and scope is not None:
            indices = self.select(
                selection=selection,
                element=element,
                mask=mask,
                syntax=syntax,
                skip_digestion=True,
            )
            return self._view.info(  # noqa: SLF001
                element=element,
                selection=indices,
                syntax=syntax,
                mask="all",
                output_type=output_type,
                skip_digestion=True,
            )

        # --- element == "system" with defined atom_indices: return RegionInfo ---
        if self.atom_indices is not None:
            molsys_section = self._view.info(  # noqa: SLF001
                element="system",
                selection=list(self.atom_indices),
                syntax=syntax,
                mask="all",
                source="molsys",
                output_type=output_type,
                skip_digestion=True,
            )
            region_section = self._view._convert_info_output(  # noqa: SLF001
                self._region_info_records(), output_type
            )
            return RegionInfo(
                tag=self.tag,
                molsys_section=molsys_section,
                region_section=region_section,
            )

        # --- fallback: region covers the full system ---
        return self._view.info(  # noqa: SLF001
            element=element,
            selection=selection,
            syntax=syntax,
            mask=mask,
            output_type=output_type,
            skip_digestion=True,
        )

    @signal(tags=["region", "query"])
    @digest()
    def contains(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ) -> bool:
        """Check whether this region contains the requested features."""
        if self.atom_indices is None:
            return self._view.contains(  # noqa: SLF001
                selection=selection,
                syntax=syntax,
                skip_digestion=True,
                **kwargs,
            )

        scoped = self.select(
            selection=selection,
            element="atom",
            syntax=syntax,
            skip_digestion=True,
        )
        return self._view.contains(  # noqa: SLF001
            selection=scoped,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["region", "query"])
    @digest()
    def is_composed_of(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ) -> bool:
        """Check whether this region is composed of the requested classes/counts."""
        if self.atom_indices is None:
            return self._view.is_composed_of(  # noqa: SLF001
                selection=selection,
                syntax=syntax,
                skip_digestion=True,
                **kwargs,
            )

        scoped = self.select(
            selection=selection,
            element="atom",
            syntax=syntax,
            skip_digestion=True,
        )
        return self._view.is_composed_of(  # noqa: SLF001
            selection=scoped,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["region", "query"])
    @digest()
    def get_center(
        self,
        structure_indices: str | Any = "all",
        skip_digestion: bool = False,
    ):
        """Return the geometric centroid of this region's atoms as a ``puw`` quantity in nm.

        Parameters
        ----------
        structure_indices
            Structure frame(s) to average over.  Defaults to ``"all"``.

        Returns
        -------
        puw.Quantity
            ``[x, y, z]`` centroid in the configured standard length unit.
        """
        from . import pyunitwizard as puw

        if self.atom_indices is None:
            raise ValueError("get_center() requires known atom_indices for this region.")
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded.")

        from molsysmt.structure import get_center
        import numpy as np

        center = get_center(
            self._view._molsys,  # noqa: SLF001
            selection=list(self.atom_indices),
            structure_indices=structure_indices,
            syntax="MolSysMT",
            skip_digestion=True,
        )
        arr = np.asarray(puw.get_value(center, to_unit="nm"), dtype=float)
        arr = np.squeeze(arr)
        centroid = arr.mean(axis=0) if arr.ndim == 2 else arr
        return puw.standardize(puw.quantity(centroid.tolist(), "nm"))

    @signal(tags=["region", "camera"])
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
        """Focus the camera on this region."""
        self._view.focus_region(
            self,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(
        tags=["region", "representation"],
        extra_factory=lambda args, kwargs: {
            "representation": kwargs.get("representation", args[1] if len(args) > 1 else None),
            "preset": kwargs.get("preset"),
        },
    )
    @digest()
    @records_scene_history
    def set_representation(self, representation: str | None = None, *, preset: str | None = None, skip_digestion: bool = False, **params: Any) -> None:
        """Apply or update a representation for this region.

        Allowed Mol* types (normalized, case-insensitive): cartoon, backbone,
        ball-and-stick (aliases: sticks, ballstick), carbohydrate, ellipsoid,
        gaussian-surface, gaussian-volume, label, line (aliases: licorice, wire),
        molecular-surface (alias: surface), orientation, plane, point, putty, spacefill (alias: vdw).

        If ``preset`` is provided, it supersedes ``representation`` and applies a Mol* preset
        (auto, atomic-detail, polymer-and-ligand, polymer-cartoon, coarse-surface, empty).
        """
        color = params.pop("color", None)
        if color is not None:
            params["molstar_color_theme"] = {"name": "uniform", "params": {"value": normalize_color(color)}}
        normalized_preset = self._view._normalize_representation_preset(preset)  # noqa: SLF001
        user_preset_payload = self._view._resolve_user_preset(normalized_preset)  # noqa: SLF001
        if normalized_preset:
            normalized = None
        elif isinstance(representation, str) and representation.strip().lower() == "inherit":
            normalized = "inherit"
        else:
            normalized = self._view._normalize_representation_type(representation)  # noqa: SLF001
        has_visual = normalized is not None or normalized_preset is not None or user_preset_payload is not None
        if self.atom_indices is not None and has_visual:
            self._view._warn_region_visual_overlap(  # noqa: SLF001
                self.tag,
                list(self.atom_indices),
                exclude_tag=self.tag,
                stacklevel=3,
            )
        self._set_visual_fields(
            representation=normalized,
            preset=normalized_preset,
            # State None owns no visual, so there is nothing for the parameters to
            # apply to: they are dropped rather than retained (Contract A). Keeping
            # them would make `repr_params` report styling the region does not have,
            # and would serialise it into the state file.
            repr_params=(params or {}) if has_visual else {},
        )
        self._view._bump_region_order(self)  # noqa: SLF001
        self._send(
            "set_region_representation",
            order=self.order,
            representation=normalized,
            preset=normalized_preset if user_preset_payload is None else None,
            user_preset=user_preset_payload,
            params=self.repr_params,
        )
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "representation"])
    @digest()
    def reset_representation(self, skip_digestion: bool = False) -> None:
        """Revert this region to the viewer's base representation."""
        self._set_visual_fields(representation=None, preset=None, repr_params={})
        self._view._bump_region_order(self)  # noqa: SLF001
        self._send(
            "set_region_representation",
            order=self.order,
            representation=None,
            preset=None,
            user_preset=None,
            params={},
        )
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "order"])
    @digest()
    def raise_to_front(self, skip_digestion: bool = False) -> None:
        """Move this region above every other region for colour and render ownership."""
        self._view._raise_region_to_front(self)  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "order"])
    @digest()
    def send_to_back(self, skip_digestion: bool = False) -> None:
        """Move this region below every other region for colour and render ownership."""
        self._view._send_region_to_back(self)  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "color"])
    @digest()
    def set_color_scheme(self, scheme: str, skip_digestion: bool = False) -> None:
        """Set the structural colour theme used by this region's own representation.

        Mirrors :meth:`Whole.set_color_scheme`. The region must have its own
        representation (state *Inherit* or *Own*); a state-*None* region is
        painted by the whole and has no structural theme of its own to set.
        """
        normalized = str(scheme).strip()
        if not normalized:
            raise ValueError("set_color_scheme requires a non-empty scheme.")
        if not self._has_own_visual():
            raise ValueError(
                f"Region {self.tag!r} has no own representation; set a representation "
                "before its colour scheme, or colour it through the whole."
            )
        params = dict(self.repr_params)
        params["color_scheme"] = normalized
        self.set_representation(
            self.representation,
            preset=self.preset,
            skip_digestion=True,
            **params,
        )

    @records_scene_history
    @signal(tags=["region", "color"])
    @digest()
    def set_color_by_attribute(
        self,
        attribute: str,
        *,
        element: str = "atom",
        palette: Any = "viridis",
        value_range: Any = None,
        structure_indices: Any = None,
        replace: bool = False,
        skip_digestion: bool = False,
    ) -> None:
        """Color this region by a scalar attribute already present in the system."""
        if self.atom_indices is None:
            raise ValueError("set_color_by_attribute requires known atom_indices for this region.")
        molsys = self._view._molsys  # noqa: SLF001
        if molsys is None:
            raise ValueError("No molecular system loaded.")

        available = set(msm.get_attributes(molsys, include_none=False, output_type="list", skip_digestion=True))
        requested = str(attribute).strip()
        aliases = {"bfactor": "b_factor"}
        resolved = aliases.get(requested, requested)
        if requested == "charge":
            resolved = "partial_charge" if "partial_charge" in available else "formal_charge"
        if resolved not in available:
            recognized = set(msm.get_attributes(molsys, include_none=True, output_type="list", skip_digestion=True))
            if resolved in recognized:
                raise ValueError(
                    f"Attribute {attribute!r} has no values in the loaded system "
                    "(it may not have been loaded with this data)."
                )
            raise ValueError(f"Attribute {attribute!r} is not a recognized atom attribute.")

        scoped_indices = self._scoped_indices_for_element(element)
        if scoped_indices is None:
            raise ValueError(f"Cannot resolve attribute {resolved!r} at element level {element!r}.")
        values = msm.get(
            molsys,
            element=element,
            selection=scoped_indices,
            structure_indices=(
                [int(self._view.current_structure_index)]
                if structure_indices is None
                else structure_indices
            ),
            output_type="values",
            skip_digestion=True,
            **{resolved: True},
        )

        from . import pyunitwizard as puw
        import numpy as np

        raw_values = puw.get_value(values) if puw.is_quantity(values) else values
        array = np.asarray(raw_values)
        array = np.squeeze(array)
        if array.ndim != 1 or array.shape[0] != len(scoped_indices):
            raise ValueError(
                f"Attribute {resolved!r} did not produce one scalar per {element} in this region."
            )
        if any(value is None for value in array.tolist()):
            raise ValueError(f"Attribute {resolved!r} contains missing values in this region.")
        try:
            scalar_values = array.astype(float).tolist()
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Attribute {resolved!r} is not scalar numeric data.") from exc

        self.set_color_by_values(
            scalar_values,
            element=element,
            palette=palette,
            value_range=value_range,
            replace=replace,
            skip_digestion=True,
        )

    @records_scene_history
    @signal(tags=["region"])
    @digest()
    def duplicate(
        self,
        *,
        tag: str | None = None,
        representation: str | None = None,
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> "Region":
        """Create a new region with the same atoms and visual specification."""
        atom_indices = self._require_atom_indices()
        duplicate_tag = tag or self._view._unique_region_tag(f"{self.tag}_copy")  # noqa: SLF001
        params = dict(self.repr_params)
        params.update(repr_params)
        duplicate = self._view._new_region_impl(  # noqa: SLF001
            selection=self.selection,
            atom_indices=list(atom_indices),
            tag=duplicate_tag,
            provenance={
                "kind": "duplicate",
                "of": self.uid,
                "frame_dependent": self.frame_dependent,
            },
            skip_digestion=True,
        )
        if self.mode == "dynamic":
            duplicate.mode = "dynamic"
        self._view._copy_atom_color_layer(self.tag, duplicate.tag, bump=duplicate)  # noqa: SLF001
        target_representation = representation if representation is not None else self.representation
        if target_representation is not None or self.preset is not None:
            duplicate.set_representation(
                target_representation,
                preset=self.preset if representation is None else None,
                skip_digestion=True,
                **params,
            )
        return duplicate

    @signal(tags=["region"])
    @digest()
    def overlaps(self, skip_digestion: bool = False) -> list[str]:
        """Return visible represented regions that overlap this region."""
        if self.atom_indices is None:
            return []
        return self._view._overlapping_visual_region_tags(  # noqa: SLF001
            self.atom_indices,
            exclude_tag=self.tag,
        )

    @records_scene_history
    @signal(tags=["region"])
    @digest()
    def new_complementary_region(self, tag: str | None = None, skip_digestion: bool = False, **kwargs: Any) -> "Region":
        """Create a new region with the complement of this region's atoms.

        The resulting tag defaults to ``f\"Global-{self.tag}\"`` if not provided.
        """
        if self.atom_indices is None:
            raise ValueError("Complement unavailable: atom_indices not known for this region.")
        if self._view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded. Load a system before creating complementary regions.")
        comp_tag = tag or f"Global-{self.tag}"
        total_atoms = int(self._view._molsys.get_n_atoms())  # noqa: SLF001
        complement = [i for i in range(total_atoms) if i not in set(self.atom_indices)]
        region = self._view._new_region_impl(  # noqa: SLF001
            atom_indices=complement,
            tag=comp_tag,
            provenance={
                "kind": "complement",
                "of": [self.uid],
                "frame_dependent": self.frame_dependent,
            },
            **kwargs,
        )
        if self.mode == "dynamic":
            region.mode = "dynamic"
        return region

    @records_scene_history
    @signal(tags=["region", "visibility"])
    @digest()
    def show(self, skip_digestion: bool = False) -> None:
        """Show this region (all attached representations)."""
        if not self._has_own_visual():
            warnings.warn(
                f"Region {self.tag!r} has no own representation to show.",
                UserWarning,
                stacklevel=2,
            )
            return
        self._hidden = False
        self._send("show_region")
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "visibility"])
    @digest()
    def hide(self, skip_digestion: bool = False) -> None:
        """Hide this region (all attached representations)."""
        if not self._has_own_visual():
            warnings.warn(
                f"Region {self.tag!r} has no own representation to hide.",
                UserWarning,
                stacklevel=2,
            )
            return
        self._hidden = True
        self._send("hide_region")
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "visibility"])
    @digest()
    def show_only(self, skip_digestion: bool = False) -> None:
        """Leave only this region visible in the current view."""
        if self.atom_indices is None:
            raise ValueError("Cannot show only a region without known atom indices.")
        for tag, region in self._view._regions.items():  # noqa: SLF001
            if not getattr(region, "_active", False):
                continue
            region._hidden = tag != self.tag  # noqa: SLF001
        self._send("show_only_region")
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region"])
    @digest()
    def delete(self, skip_digestion: bool = False) -> None:
        """Remove this region and its representations."""
        if not self._active:
            return
        self._active = False
        self._send("delete_region")
        self._view._drop_atom_color_layer(self.tag)  # noqa: SLF001
        self._view._unregister_region(self.tag)  # noqa: SLF001
        if isinstance(self._layer, str):
            self._view._cleanup_empty_layer_group(self._layer)  # noqa: SLF001
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region"])
    @digest()
    def rename(self, new_tag: str, skip_digestion: bool = False) -> None:
        """Rename this region to *new_tag* on both the Python and JS sides."""
        if not self._active:
            return
        old_tag = self.tag
        self._send("rename_region", new_tag=new_tag)
        self._tag = new_tag
        self._view._regions[new_tag] = self  # noqa: SLF001
        self._view._regions.pop(old_tag, None)  # noqa: SLF001
        self._view._rename_atom_color_layer(old_tag, new_tag)  # noqa: SLF001
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "layer"])
    @digest()
    def set_layer(self, layer: Any, skip_digestion: bool = False) -> None:
        """Assign this region to *layer* (a :class:`Layer`, a tag, or ``None``).

        The layer group is created if it does not exist yet; a previous layer
        left empty by the move is cleaned up. Layer show/hide/delete then apply
        to this region.
        """
        if not self._active:
            return
        tag = layer.tag if hasattr(layer, "tag") else (None if layer is None else str(layer))
        self._set_layer_membership(tag)
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "layer"])
    @digest()
    def remove_from_layer(self, skip_digestion: bool = False) -> None:
        """Detach this region from its layer (it belongs to no layer afterwards)."""
        if not self._active or self._layer is None:
            return
        self._set_layer_membership(None)
        self._view._sync_region_summaries_runtime()  # noqa: SLF001

    # --- Scalar colour mapping ---

    @records_scene_history
    @signal(tags=["color", "region"])
    @digest()
    def set_color(self, color: Any, skip_digestion: bool = False) -> None:
        """Paint this region's atom-color layer uniformly."""
        if self.atom_indices is None:
            raise ValueError("set_color requires known atom_indices for this region.")
        try:
            normalized = normalize_color(color)
        except (TypeError, ValueError) as exc:
            raise ArgumentError("color", value=color, caller="Region.set_color") from exc
        self._view._set_atom_color_layer(  # noqa: SLF001
            self.tag,
            {int(atom_index): normalized for atom_index in self.atom_indices},
            bump=self,
        )

    @records_scene_history
    @signal(tags=["color", "region"])
    @digest()
    def set_color_by_values(
        self,
        values: Any,
        element: str = "atom",
        palette: Any = "viridis",
        value_range: Any = None,
        replace: bool = False,
        skip_digestion: bool = False,
    ) -> None:
        """Map a scalar array to per-atom colors for this region.

        One scalar value is mapped to a color and broadcast to all atoms in the
        corresponding structural element *within this region*.

        Parameters
        ----------
        values
            Iterable of scalars, one per *element* present in this region.
        element
            Structural level: ``"atom"``, ``"group"``, ``"component"``,
            ``"molecule"``, ``"chain"``, ``"entity"``.  Defaults to ``"atom"``.
        palette
            Palette name, matplotlib colormap, or list of colors.
        value_range
            ``[vmin, vmax]`` normalization range.  Auto-detected when ``None``.
        replace
            If ``True``, replace any existing per-atom color map for the entire
            canvas.  If ``False`` (default), the region colors are *merged*
            with any existing assignments.
        """
        if self.atom_indices is None:
            raise ValueError("set_color_by_values requires known atom_indices for this region.")
        atom_indices, per_atom_colors = expand_values_to_atoms(
            self._view._molsys,  # noqa: SLF001
            values=values,
            element=element,
            palette=palette,
            value_range=value_range,
            scope_atom_indices=list(self.atom_indices),
        )
        layer_update = dict(zip(atom_indices, per_atom_colors))
        if replace:
            self._view._set_atom_color_layer(self.tag, layer_update, bump=self)  # noqa: SLF001
        else:
            self._view._update_atom_color_layer(self.tag, layer_update, bump=self)  # noqa: SLF001

    @records_scene_history
    @signal(tags=["color", "region"])
    @digest()
    def reset_colors(self, skip_digestion: bool = False) -> None:
        """Remove this region's per-atom colour layer only."""
        self._view._clear_atom_color_layer(self.tag)  # noqa: SLF001


class RegionsManager(dict):
    """Dict-like registry of :class:`Region` objects with an :meth:`info` helper."""

    def __init__(self, view: Any) -> None:
        super().__init__()
        self._view = view

    @dep_digest('molsysmt')
    @records_scene_history
    @signal(tags=["region"])
    @digest()
    def add(
        self,
        selection: str | Any = "all",
        *,
        atom_indices: list[int] | None = None,
        tag: str | None = None,
        representation: str | None = None,
        complement_of_regions: str | list[str] | None = None,
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> "Region":
        """Create and register a new region — the region-side twin of
        ``view.selections.add(...)``."""
        return self._view._new_region_impl(  # noqa: SLF001
            selection=selection,
            atom_indices=atom_indices,
            tag=tag,
            representation=representation,
            complement_of_regions=complement_of_regions,
            syntax=syntax,
            skip_digestion=True,
            **repr_params,
        )

    # ── Registry queries (parity with SelectionsManager) ───────────────────
    # RegionsManager *is* the live registry dict, so `dict.clear()` is left
    # untouched (scene reset relies on it); a message-based bulk delete is
    # exposed as delete_all() instead of overriding clear().

    @signal(tags=["region", "query"])
    @digest()
    def tags(self) -> list[str]:
        """The tags of every managed region."""
        return list(self.keys())

    @signal(tags=["region", "query"])
    @digest()
    def contains(self, tag: str, skip_digestion: bool = False) -> bool:
        """Whether a region with *tag* is registered."""
        return tag in self

    @signal(tags=["region", "query"])
    @digest()
    def count(self, skip_digestion: bool = False) -> int:
        """How many regions are registered."""
        return len(self)

    @signal(tags=["region", "query"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """A summary record per region (the list form of :meth:`info`)."""
        result = self.info()
        return result if isinstance(result, list) else [result]

    @signal(tags=["region"])
    @digest()
    def delete(self, tag: str, skip_digestion: bool = False) -> None:
        """Delete the region with *tag* (and its representations)."""
        region = self.get(tag)
        if region is None:
            raise KeyError(f"No region with tag {tag!r}.")
        region.delete(skip_digestion=True)

    @records_scene_history
    @signal(tags=["region"])
    @digest()
    def set_tag(self, tag: str, new_tag: str, skip_digestion: bool = False) -> None:
        """Rename the region *tag* to *new_tag*."""
        region = self.get(tag)
        if region is None:
            raise KeyError(f"No region with tag {tag!r}.")
        region.rename(new_tag, skip_digestion=True)

    @records_scene_history
    @signal(tags=["region"])
    @digest()
    def delete_all(self, skip_digestion: bool = False) -> None:
        """Delete every managed region, emitting a scene message for each."""
        for tag in list(self.keys()):
            region = self.get(tag)
            if region is not None:
                region.delete(skip_digestion=True)

    @records_scene_history
    @signal(tags=["region", "visibility"])
    @digest()
    def show_all(self, skip_digestion: bool = False) -> None:
        """Show every active region."""
        self._view._set_all_regions_visibility(hidden=False)  # noqa: SLF001

    @records_scene_history
    @signal(tags=["region", "visibility"])
    @digest()
    def hide_all(self, skip_digestion: bool = False) -> None:
        """Hide every active region."""
        self._view._set_all_regions_visibility(hidden=True)  # noqa: SLF001

    @signal(tags=["region"])
    @digest()
    def overlaps(self, skip_digestion: bool = False) -> dict[str, list[str]]:
        """Return overlap tags for every managed region."""
        return {tag: region.overlaps(skip_digestion=True) for tag, region in self.items()}

    @signal(tags=["region", "recipe"])
    @digest()
    def dependencies(self, skip_digestion: bool = False) -> dict[str, tuple[str, ...]]:
        """Return region dependency uids keyed by region tag."""
        return {tag: region.dependencies for tag, region in self.items()}

    @signal(tags=["region", "recipe"])
    @digest()
    def dependents(self, skip_digestion: bool = False) -> dict[str, tuple[str, ...]]:
        """Return dependent region uids keyed by region tag."""
        return {tag: region.dependents for tag, region in self.items()}

    @signal(tags=["region", "order"])
    @digest()
    def raise_to_front(self, tag: str, skip_digestion: bool = False) -> None:
        """Move the named region above every other region."""
        region = self.get(tag)
        if region is None:
            raise KeyError(tag)
        region.raise_to_front(skip_digestion=True)

    @signal(tags=["region", "order"])
    @digest()
    def send_to_back(self, tag: str, skip_digestion: bool = False) -> None:
        """Move the named region below every other region."""
        region = self.get(tag)
        if region is None:
            raise KeyError(tag)
        region.send_to_back(skip_digestion=True)

    @signal(tags=["region", "query"])
    @digest()
    def info(self, tag: str | None = None) -> dict[str, Any] | List[dict[str, Any]]:
        """Return compact metadata for one region (by *tag*) or all regions."""

        def summarize(region: Region) -> dict[str, Any]:
            atom_indices = list(region.atom_indices) if region.atom_indices is not None else []
            return {
                "tag": region.tag,
                "owner": region.owner,
                "n_atoms": len(atom_indices),
                "atom_indices": atom_indices,
                "representation": region.representation,
                "order": region.order,
                "uid": region.uid,
                "mode": region.mode,
                "frame_dependent": region.frame_dependent,
                "provenance": dict(region.provenance),
                "dependencies": region.dependencies,
                "dependents": region.dependents,
                "visible": region.visible,
                "active": region._active,  # noqa: SLF001
            }

        if tag is not None:
            region = self.get(tag)
            if region is None:
                raise ValueError(f"No region found for tag {tag!r}.")
            return summarize(region)
        return [summarize(r) for r in self.values()]
