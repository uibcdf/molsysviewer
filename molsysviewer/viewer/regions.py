from __future__ import annotations


import re
import time
import warnings
from contextlib import contextmanager
from typing import Any, Mapping

import molsysmt as msm
from smonitor.integrations import emit_from_catalog
from smonitor import signal
from depdigest import dep_digest

from .._private.arg_digestion import digest
from .._private.smonitor import CATALOG, PACKAGE_ROOT, META
from .._private.smonitor_emit import emit_suppressed_exception
from ..regions import Region
from .representations import normalize_representation_type
from .presets import normalize_representation_preset, resolve_user_preset


class RegionsMixin:
    _REGION_ATTRIBUTE_CANDIDATES = ("b_factor", "occupancy", "partial_charge", "formal_charge")
    _TRANSIENT_REGION_TAG = re.compile(
        r"^(?:(?:orientation|plane)-(?:region)?\d+|focus\d+)$"
    )

    def _enrich_interaction_payload(self, payload: dict) -> dict:
        if payload.get("kind") != "structure":
            return payload
        raw = payload.get("atom_indices")
        if not raw:
            return payload
        pick_set = set(raw)
        tags = [
            tag
            for tag, region in self._regions.items()
            if region.atom_indices is not None and pick_set.isdisjoint(region.atom_indices) is False
        ]
        payload["region_tags"] = tags
        return payload

    def _next_region_tag(self) -> str:
        self._region_counter += 1
        return f"region{self._region_counter}"

    def _next_region_uid(self) -> str:
        self._region_uid_counter += 1
        return f"region-uid-{self._region_uid_counter}"

    def _slugify_region_tag(self, value: str) -> str:
        text = re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_")
        return text or self._next_region_tag()

    def _unique_region_tag(self, base: str, used_tags: set[str] | None = None) -> str:
        used = set(self._regions.keys()) if used_tags is None else set(used_tags) | set(self._regions.keys())
        if base not in used:
            return base
        counter = 2
        candidate = f"{base}__{counter}"
        while candidate in used:
            counter += 1
            candidate = f"{base}__{counter}"
        return candidate

    def _recipe_frame_dependent(self, expression: Any, syntax: str = "MolSysMT") -> bool:
        text = str(expression or "").lower()
        return any(token in text for token in (" within ", "within ", "distance", "around", "near"))

    def _region_by_uid(self, uid: str) -> Region | None:
        for region in self._regions.values():
            if region.uid == uid:
                return region
        return None

    def _operands_are_dynamic(self, operand_uids: list[str]) -> bool:
        if not operand_uids:
            return False
        operands = [self._region_by_uid(uid) for uid in operand_uids]
        if any(region is None for region in operands):
            return False
        return all(region.mode == "dynamic" for region in operands if region is not None)

    def _operands_frame_dependent(self, operand_uids: list[str]) -> bool:
        return any(
            bool(region and region.frame_dependent)
            for region in (self._region_by_uid(uid) for uid in operand_uids)
        )

    def _clear_dynamic_region_cache(self, uid: str | None = None) -> None:
        cache = getattr(self, "_dynamic_region_cache", None)
        if cache is None:
            return
        if uid is None:
            cache.clear()
            return
        for key in list(cache.keys()):
            if key[0] == uid:
                cache.pop(key, None)

    def _cache_dynamic_region_atoms(self, uid: str, structure_index: int, atom_indices: list[int]) -> tuple[int, ...]:
        cache = self._dynamic_region_cache
        key = (str(uid), int(structure_index))
        value = tuple(int(index) for index in atom_indices)
        cache[key] = value
        cache.move_to_end(key)
        limit = max(1, int(getattr(self, "_dynamic_region_cache_limit", 512)))
        while len(cache) > limit:
            cache.popitem(last=False)
        return value

    def _evaluate_region_provenance(self, region: Region, structure_index: int | None = None) -> list[int] | None:
        provenance = dict(region.provenance)
        if provenance.get("broken"):
            return None
        kind = provenance.get("kind")
        if kind == "query":
            select_kwargs: dict[str, Any] = {}
            if structure_index is not None:
                select_kwargs["structure_indices"] = [int(structure_index)]
            return [
                int(index)
                for index in msm.select(
                    self._molsys,
                    selection=provenance.get("expression", "all"),
                    syntax=str(provenance.get("syntax") or "MolSysMT"),
                    skip_digestion=True,
                    **select_kwargs,
                )
            ]
        if kind == "split":
            element = str(provenance.get("element"))
            value = int(provenance.get("value"))
            index_attribute = {
                "group": "group_index",
                "component": "component_index",
                "chain": "chain_index",
                "molecule": "molecule_index",
                "entity": "entity_index",
            }.get(element)
            if index_attribute is None:
                return None
            values = msm.get(
                self._molsys,
                element="atom",
                selection="all",
                output_type="dictionary",
                skip_digestion=True,
                **{index_attribute: True},
            )
            raw_indices = list(values.get(index_attribute, []))
            return [atom_index for atom_index, item_index in enumerate(raw_indices) if item_index == value]
        if kind == "duplicate":
            source = self._region_by_uid(str(provenance.get("of")))
            if source is None:
                return None
            if structure_index is not None and source.mode == "dynamic" and source.frame_dependent:
                cached = self._dynamic_region_cache.get((source.uid, int(structure_index)))
                if cached is not None:
                    return list(cached)
                evaluated = self._evaluate_region_provenance(source, structure_index=structure_index)
                if evaluated is None:
                    return None
                self._cache_dynamic_region_atoms(source.uid, int(structure_index), evaluated)
                return list(evaluated)
            return list(source.atom_indices or [])
        if kind == "complement":
            operand_uids = [str(uid) for uid in provenance.get("of", [])]
            excluded: set[int] = set()
            for uid in operand_uids:
                operand = self._region_by_uid(uid)
                if operand is None:
                    return None
                if structure_index is not None and operand.mode == "dynamic" and operand.frame_dependent:
                    cached = self._dynamic_region_cache.get((operand.uid, int(structure_index)))
                    if cached is None:
                        evaluated = self._evaluate_region_provenance(operand, structure_index=structure_index)
                        if evaluated is None:
                            return None
                        cached = self._cache_dynamic_region_atoms(operand.uid, int(structure_index), evaluated)
                    excluded.update(cached)
                else:
                    excluded.update(operand.atom_indices or ())
            total = int(self._molsys.get_n_atoms())
            return [index for index in range(total) if index not in excluded]
        if kind == "boolean":
            operand_uids = [str(uid) for uid in provenance.get("operands", [])]
            operands = [self._region_by_uid(uid) for uid in operand_uids]
            if any(operand is None for operand in operands):
                return None
            if not operands:
                return []
            operand_atoms: list[list[int]] = []
            for operand in operands:
                assert operand is not None
                if structure_index is not None and operand.mode == "dynamic" and operand.frame_dependent:
                    cached = self._dynamic_region_cache.get((operand.uid, int(structure_index)))
                    if cached is None:
                        evaluated = self._evaluate_region_provenance(operand, structure_index=structure_index)
                        if evaluated is None:
                            return None
                        cached = self._cache_dynamic_region_atoms(operand.uid, int(structure_index), evaluated)
                    operand_atoms.append(list(cached))
                else:
                    operand_atoms.append(list(operand.atom_indices or []))
            left = list(operand_atoms[0])
            op = provenance.get("op")
            if op in {"minus", "difference", "subtract"}:
                right: set[int] = set()
                for atoms in operand_atoms[1:]:
                    right.update(atoms)
                return [index for index in left if index not in right]
            if op in {"and", "intersection"}:
                current = set(left)
                for atoms in operand_atoms[1:]:
                    current &= set(atoms)
                return [index for index in left if index in current]
            if op in {"or", "union"}:
                seen: set[int] = set()
                result: list[int] = []
                for atoms in operand_atoms:
                    for index in atoms:
                        if index not in seen:
                            seen.add(index)
                            result.append(int(index))
                return result
        return None

    def _dynamic_regions_requiring_frame_evaluation(self) -> list[Region]:
        return [
            region
            for region in self._regions.values()
            if (
                bool(getattr(region, "_active", False))
                and region.mode == "dynamic"
                and region.frame_dependent
            )
        ]

    def _handle_dynamic_region_evaluation_request(self, content: Mapping[str, Any]) -> None:
        frame = int(content.get("frame", 0))
        changed = self._evaluate_dynamic_regions_for_frame(frame)
        self._send_runtime_only(
            {
                "op": "set_dynamic_region_atoms",
                "frame": frame,
                "regions": changed,
            }
        )

    def _evaluate_dynamic_regions_for_frame(self, structure_index: int) -> list[dict[str, Any]]:
        changed: list[dict[str, Any]] = []
        frame = int(structure_index)
        budget_ms = float(getattr(self, "_dynamic_region_evaluation_budget_ms", 25.0))
        for region in self._dynamic_regions_requiring_frame_evaluation():
            key = (region.uid, frame)
            cached = self._dynamic_region_cache.get(key)
            if cached is None:
                started = time.perf_counter()
                evaluated = self._evaluate_region_provenance(region, structure_index=frame)
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                if evaluated is None:
                    continue
                cached = self._cache_dynamic_region_atoms(region.uid, frame, evaluated)
                if elapsed_ms > budget_ms:
                    region._set_mode("static")  # noqa: SLF001
                    self._clear_dynamic_region_cache(region.uid)
                    emit_from_catalog(
                        CATALOG["dynamic_region_evaluation_over_budget"],
                        package_root=PACKAGE_ROOT,
                        meta=META,
                        extra={
                            "tag": region.tag,
                            "uid": region.uid,
                            "frame": frame,
                            "elapsed_ms": elapsed_ms,
                            "budget_ms": budget_ms,
                        },
                    )
                    self._send_runtime_only(
                        {
                            "op": "dynamic_region_evaluation_warning",
                            "tag": region.tag,
                            "frame": frame,
                            "elapsed_ms": elapsed_ms,
                            "budget_ms": budget_ms,
                            "action": "frozen_to_static",
                        }
                    )
            current = tuple(region.atom_indices or ())
            if tuple(cached) == current:
                continue
            region._set_atom_indices(cached)  # noqa: SLF001
            changed.append({"tag": region.tag, "atom_indices": list(cached)})
        if changed:
            self._sync_region_summaries_runtime()
        return changed

    def _label_for_split_region(self, *, element_label: str, item_index: int) -> str | None:
        template = "{name}"
        element = element_label
        if element_label not in {"chain", "molecule", "entity"}:
            return None
        try:
            label = msm.get_label(
                self._molsys,
                element=element,
                selection=[item_index],
                string=template,
                skip_digestion=True,
            )
        except Exception as exc:
            emit_suppressed_exception(
                "RegionsMixin._label_for_split_region",
                exc,
                context={"element": element, "item_index": item_index},
            )
            return None
        if isinstance(label, str) and label.strip():
            return label
        return None

    def _split_into_regions(
        self,
        *,
        selection: str | Any,
        structure_indices: str | Any,
        syntax: str,
        element_label: str,
        index_attribute: str,
        representation: str | None = None,
    ) -> dict[str, Region]:
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before splitting into regions.")

        atom_indices = self.select(
            selection=selection,
            structure_indices=structure_indices,
            element="atom",
            syntax=syntax,
            skip_digestion=True,
        )
        if not atom_indices:
            return {}

        get_kwargs: dict[str, Any] = {index_attribute: True}
        values = msm.get(
            self._molsys,
            element="atom",
            selection=atom_indices,
            output_type="dictionary",
            skip_digestion=True,
            **get_kwargs,
        )
        raw_indices = list(values.get(index_attribute, []))

        buckets: dict[int, dict[str, Any]] = {}
        for atom_index, item_index in zip(atom_indices, raw_indices):
            try:
                normalized_index = int(item_index)
            except Exception as exc:
                emit_suppressed_exception(
                    "RegionsMixin._split_into_regions.index_normalization",
                    exc,
                    context={"element": element_label, "value": repr(item_index)},
                )
                continue
            bucket = buckets.setdefault(normalized_index, {"atom_indices": []})
            bucket["atom_indices"].append(int(atom_index))

        created: dict[str, Region] = {}
        used_tags: set[str] = set()
        for item_index in sorted(buckets):
            bucket = buckets[item_index]
            label = self._label_for_split_region(element_label=element_label, item_index=item_index)
            if isinstance(label, str) and label.strip():
                slug = self._slugify_region_tag(label)
                if element_label == "chain":
                    base_tag = slug
                else:
                    base_tag = f"{element_label}_{slug}"
            else:
                base_tag = f"{element_label}_{item_index}"
            tag = self._unique_region_tag(base_tag, used_tags)
            used_tags.add(tag)
            created[tag] = self._new_region_impl(
                atom_indices=bucket["atom_indices"],
                tag=tag,
                representation=representation,
                provenance={
                    "kind": "split",
                    "element": element_label,
                    "value": item_index,
                    "frame_dependent": False,
                },
                skip_digestion=True,
            )
        return created

    def _normalize_representation_type(self, value: str | None) -> str | None:
        if isinstance(value, str) and value.strip().lower() == "inherit":
            raise ValueError("'inherit' is a region representation sentinel, not a Mol* representation type.")
        return normalize_representation_type(value)

    def _normalize_representation_preset(self, value: str | None) -> str | None:
        return normalize_representation_preset(value)

    @property
    def representations(self) -> list[str]:
        """Sorted list of allowed representation type identifiers."""
        from .representations import ALLOWED_REPRESENTATIONS
        return sorted(ALLOWED_REPRESENTATIONS)

    @property
    def presets(self) -> list[str]:
        """Sorted list of allowed preset identifiers (built-in and user-defined)."""
        from .presets import ALLOWED_PRESETS
        from ..config.user_presets import user_presets
        return sorted(ALLOWED_PRESETS | set(user_presets.keys()))

    def _unregister_region(self, tag: str) -> None:
        region = self._regions.get(tag)
        if region is not None:
            self._clear_dynamic_region_cache(region.uid)
            missing_uid = region.uid
            for candidate in list(self._regions.values()):
                if candidate is region:
                    continue
                if missing_uid in candidate.dependencies:
                    candidate._freeze_broken_recipe(missing_uid)  # noqa: SLF001
                    self._clear_dynamic_region_cache(candidate.uid)
        self._regions.pop(tag, None)
        self._refresh_region_dynamic_modes()

    def _refresh_region_dynamic_modes(self) -> None:
        changed = True
        while changed:
            changed = False
            for region in list(self._regions.values()):
                if region.mode == "dynamic" and not region._can_be_dynamic():  # noqa: SLF001
                    region._set_mode("static")  # noqa: SLF001
                    changed = True

    def _set_all_regions_visibility(self, *, hidden: bool) -> None:
        tags: list[str] = []
        for tag, region in self._regions.items():
            if not getattr(region, "_active", False):
                continue
            region._hidden = bool(hidden)  # noqa: SLF001
            tags.append(tag)
        self._send(
            {
                "op": "set_regions_visibility",
                "tags": tags,
                "hidden": bool(hidden),
            }
        )
        self._sync_region_summaries_runtime()

    def _send_region_operation(self, message: dict[str, Any]) -> None:
        if getattr(self, "_region_batch_depth", 0) > 0:
            self._region_batch_operations.append(dict(message))
            return
        self._send(message)

    @contextmanager
    def _batch_region_updates(self):
        outermost = getattr(self, "_region_batch_depth", 0) == 0
        if outermost:
            self._region_batch_operations = []
            self._region_batch_summary_dirty = False
        self._region_batch_depth += 1
        failed = False
        try:
            yield
        except Exception:
            failed = True
            raise
        finally:
            self._region_batch_depth -= 1
            if outermost:
                operations = list(self._region_batch_operations)
                summary_dirty = bool(self._region_batch_summary_dirty)
                self._region_batch_operations = []
                self._region_batch_summary_dirty = False
                if not failed and operations:
                    self._send(
                        {
                            "op": "batch_region_operations",
                            "operations": operations,
                        }
                    )
                if not failed and summary_dirty:
                    self._sync_region_summaries_runtime()

    def _available_region_attributes(self) -> list[str]:
        if self._molsys is None:
            return []
        available = set(
            msm.get_attributes(
                self._molsys,
                include_none=False,
                output_type="list",
                skip_digestion=True,
            )
        )
        return [name for name in self._REGION_ATTRIBUTE_CANDIDATES if name in available]

    def _region_summary_records(self) -> list[dict[str, Any]]:
        available_attributes = self._available_region_attributes()
        manageable = {
            tag: region
            for tag, region in self._regions.items()
            if not self._TRANSIENT_REGION_TAG.fullmatch(tag)
        }
        visual_sets = {
            tag: set(region.atom_indices or ())
            for tag, region in manageable.items()
            if self._region_has_visible_representation(region) and region.atom_indices is not None
        }
        overlap_map = {tag: [] for tag in manageable}
        visual_tags = sorted(visual_sets)
        for index, left_tag in enumerate(visual_tags):
            left_atoms = visual_sets[left_tag]
            for right_tag in visual_tags[index + 1:]:
                if left_atoms.isdisjoint(visual_sets[right_tag]):
                    continue
                overlap_map[left_tag].append(right_tag)
                overlap_map[right_tag].append(left_tag)

        records: list[dict[str, Any]] = []
        for tag, region in sorted(manageable.items()):
            atom_indices = list(region.atom_indices or ())
            records.append(
                {
                    "tag": tag,
                    "atom_indices": atom_indices,
                    "atom_count": len(atom_indices),
                    "selection": region.selection if isinstance(region.selection, str) else None,
                    "hidden": bool(region._hidden),  # noqa: SLF001
                    # Layer membership (Phase 9) so the Layers subpanel can group
                    # regions under their layer; None for a region in no layer.
                    "layer": region.layer,
                    "mode": region.mode,
                    "frame_dependent": region.frame_dependent,
                    "representation": region.representation,
                    "preset": region.preset,
                    "representation_params": dict(region.repr_params),
                    "overlap_tags": overlap_map[tag],
                    "available_attributes": list(available_attributes),
                }
            )
        return records

    def _sync_region_summaries_runtime(self) -> None:
        if getattr(self, "_region_batch_depth", 0) > 0:
            self._region_batch_summary_dirty = True
            return
        self._send_runtime_only(
            {
                "op": "set_region_summaries",
                "regions": self._region_summary_records(),
                "representations": self.representations,
                "presets": self.presets,
            }
        )

    def _region_has_visible_representation(self, region: Region) -> bool:
        return (
            bool(getattr(region, "_active", False))
            and not bool(getattr(region, "_hidden", False))
            and (
                region.representation is not None
                or region.preset is not None
            )
        )

    def _overlapping_visual_region_tags(
        self,
        atom_indices: list[int] | tuple[int, ...],
        *,
        exclude_tag: str | None = None,
    ) -> list[str]:
        atom_set = {int(index) for index in atom_indices}
        if not atom_set:
            return []
        overlaps: list[str] = []
        for tag, region in self._regions.items():
            if tag == exclude_tag or not self._region_has_visible_representation(region):
                continue
            if region.atom_indices is None:
                continue
            if atom_set.isdisjoint(region.atom_indices) is False:
                overlaps.append(tag)
        return overlaps

    def _warn_region_visual_overlap(
        self,
        tag: str,
        atom_indices: list[int] | tuple[int, ...],
        *,
        exclude_tag: str | None = None,
        stacklevel: int = 3,
    ) -> None:
        overlaps = self._overlapping_visual_region_tags(atom_indices, exclude_tag=exclude_tag)
        if not overlaps:
            return
        warnings.warn(
            f"Region {tag!r} overlaps visible represented region(s) {', '.join(overlaps)}. "
            "Overlapping region representations can produce z-fighting; use "
            "difference(), intersection(), or union() to compose non-overlapping regions.",
            UserWarning,
            stacklevel=stacklevel,
        )

    def _resolve_user_preset(self, preset: str | None):
        return resolve_user_preset(self, preset)

    def _new_region_impl(
        self,
        selection: str | Any = "all",
        *,
        atom_indices: list[int] | None = None,
        tag: str | None = None,
        representation: str | None = None,
        complement_of_regions: str | list[str] | None = None,
        syntax: str = "MolSysMT",
        provenance: dict[str, Any] | None = None,
        frame_dependent: bool | None = None,
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> Region:
        """Internal region constructor that may receive recipe metadata."""
        tag = tag or self._next_region_tag()
        if tag in self._regions:
            raise ValueError(f"A region with tag {tag!r} already exists.")
        if isinstance(representation, str) and representation.strip().lower() == "inherit":
            representation = "inherit"
        else:
            representation = self._normalize_representation_type(representation)
        region_mode = "static"

        if atom_indices is None and complement_of_regions is not None:
            region_tags = []
            if isinstance(complement_of_regions, str):
                if complement_of_regions.lower() == "all":
                    region_tags = list(self._regions.keys())
                else:
                    region_tags = [complement_of_regions]
            else:
                region_tags = list(complement_of_regions)
            exclude: set[int] = set()
            for rt in region_tags:
                r = self._regions.get(rt)
                if r and r.atom_indices is not None:
                    exclude.update(r.atom_indices)
            operand_uids = [self._regions[rt].uid for rt in region_tags if rt in self._regions]
            if self._molsys is None:
                raise ValueError("Cannot build complement: no molecular system loaded.")
            total = int(self._molsys.get_n_atoms())
            atom_indices = [i for i in range(total) if i not in exclude]
            if provenance is None:
                provenance = {
                    "kind": "complement",
                    "of": operand_uids,
                    "frame_dependent": self._operands_frame_dependent(operand_uids),
                }
                if self._operands_are_dynamic(operand_uids):
                    region_mode = "dynamic"
        elif atom_indices is None and self._molsys is not None:
            atom_indices = list(msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True))
            if provenance is None:
                provenance = {
                    "kind": "query",
                    "expression": selection,
                    "syntax": syntax,
                    "frame_dependent": self._recipe_frame_dependent(selection, syntax),
                }
        elif atom_indices is None and self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before creating regions.")

        if atom_indices is None or len(atom_indices) == 0:
            raise ValueError("Cannot create region: empty atom_indices for selection.")

        atom_indices = [int(i) for i in atom_indices]
        if provenance is None:
            provenance = {
                "kind": "active_selection",
                "atom_indices": list(atom_indices),
                "frame_dependent": False,
            }
        if frame_dependent is not None:
            provenance["frame_dependent"] = bool(frame_dependent)

        visual_representation = representation
        visual_repr_params = dict(repr_params)
        has_visual_spec = visual_representation is not None

        region = Region(
            self,
            tag,
            selection,
            atom_indices=atom_indices,
            representation=None if has_visual_spec else representation,
            repr_params={},
            provenance=provenance,
            mode=region_mode,
        )
        self._regions[tag] = region
        if has_visual_spec:
            region._send_create(include_visual=False)
            region.set_representation(
                visual_representation,
                skip_digestion=True,
                **visual_repr_params,
            )
        else:
            region._send_create()
        return region

    @signal(tags=["region", "selection"])
    @digest()
    def new_region_from_active_selection(
        self,
        *,
        tag: str | None = None,
        representation: str | None = None,
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> Region:
        """Create a region from the last active selection event."""
        event = self.get_last_active_selection_event()
        if event is None:
            raise ValueError("No active selection stored. Select an element before creating a region.")

        atom_indices = event.get("atom_indices") or []
        atom_indices = [int(ii) for ii in atom_indices]
        if len(atom_indices) == 0:
            raise ValueError("The current active selection does not resolve to any atoms.")

        return self._new_region_impl(
            atom_indices=atom_indices,
            tag=tag,
            representation=representation,
            skip_digestion=True,
            **repr_params,
        )

    @signal(tags=["region", "geometry"])
    @digest()
    def show_orientation_axes(
        self,
        selection: str | Any = "all",
        *,
        atom_indices: list[int] | None = None,
        tag: str | None = None,
        alpha: float | None = None,
        skip_digestion: bool = False,
    ) -> Region:
        """Overlay Mol* orientation-ellipsoid axes on a selection."""
        region_tag = tag or f"orientation-{self._next_region_tag()}"
        region = self._new_region_impl(
            selection=selection,
            atom_indices=atom_indices,
            tag=region_tag,
            skip_digestion=True,
        )
        params: dict[str, Any] = {}
        if alpha is not None:
            params["alpha"] = float(alpha)
        region._send(
            "set_region_representation",
            representation="orientation",
            preset=None,
            user_preset=None,
            params=params,
        )
        region._set_visual_fields(representation="orientation", preset=None, repr_params=params)  # noqa: SLF001
        return region

    @signal(tags=["region", "geometry"])
    @digest()
    def show_best_fit_plane(
        self,
        selection: str | Any = "all",
        *,
        atom_indices: list[int] | None = None,
        tag: str | None = None,
        alpha: float | None = None,
        skip_digestion: bool = False,
    ) -> Region:
        """Overlay Mol* best-fit plane on a selection."""
        region_tag = tag or f"plane-{self._next_region_tag()}"
        region = self._new_region_impl(
            selection=selection,
            atom_indices=atom_indices,
            tag=region_tag,
            skip_digestion=True,
        )
        params: dict[str, Any] = {}
        if alpha is not None:
            params["alpha"] = float(alpha)
        region._send(
            "set_region_representation",
            representation="plane",
            preset=None,
            user_preset=None,
            params=params,
        )
        region._set_visual_fields(representation="plane", preset=None, repr_params=params)  # noqa: SLF001
        return region

    _SPLIT_ELEMENT_ATTRIBUTES = {
        "group": "group_index",
        "component": "component_index",
        "chain": "chain_index",
        "molecule": "molecule_index",
        "entity": "entity_index",
    }

    @signal(tags=["region", "query"])
    @digest()
    def count_regions_by(
        self,
        element: str,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        *,
        skip_digestion: bool = False,
    ) -> int:
        """Return how many regions :meth:`make_regions_by` would create, without creating them.

        A cheap probe so a caller can size a split — a ``group`` split can produce
        hundreds of regions — and decide (or confirm) before running it.
        """
        if element not in self._SPLIT_ELEMENT_ATTRIBUTES:
            raise ValueError(
                f"Unsupported element for count_regions_by: {element!r}. "
                f"Allowed: {sorted(self._SPLIT_ELEMENT_ATTRIBUTES)}"
            )
        if self._molsys is None:
            raise ValueError("No molecular system loaded.")
        atom_indices = self.select(
            selection=selection,
            structure_indices=structure_indices,
            element="atom",
            syntax=syntax,
            skip_digestion=True,
        )
        if not atom_indices:
            return 0
        index_attribute = self._SPLIT_ELEMENT_ATTRIBUTES[element]
        values = msm.get(
            self._molsys,
            element="atom",
            selection=atom_indices,
            output_type="dictionary",
            skip_digestion=True,
            **{index_attribute: True},
        )
        distinct: set[int] = set()
        for raw in values.get(index_attribute, []):
            try:
                distinct.add(int(raw))
            except (TypeError, ValueError):
                continue
        return len(distinct)

    @signal(tags=["region", "split"])
    @digest()
    def make_regions_by(
        self,
        element: str,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        *,
        representation: str | None = None,
        skip_digestion: bool = False,
    ) -> dict[str, Region]:
        """Create one region per selected hierarchy element and return them by tag."""
        representation = self._normalize_representation_type(representation)
        if element not in self._SPLIT_ELEMENT_ATTRIBUTES:
            raise ValueError(
                f"Unsupported element for make_regions_by: {element!r}. "
                f"Allowed: {sorted(self._SPLIT_ELEMENT_ATTRIBUTES)}"
            )
        with self._batch_region_updates():
            return self._split_into_regions(
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
                element_label=element,
                index_attribute=self._SPLIT_ELEMENT_ATTRIBUTES[element],
                representation=representation,
            )


RegionsMixin.__module__ = "molsysviewer.viewer"
for _name, _value in RegionsMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception as exc:
            emit_suppressed_exception(
                "RegionsMixin.__module_assignment__",
                exc,
                context={"callable": _name},
            )
