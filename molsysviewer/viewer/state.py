from __future__ import annotations


from typing import Any

from .._private.smonitor_emit import emit_suppressed_exception
from ..regions import Region

STATE_VERSION = 2


class StateMixin:
    def export_state(self) -> dict:
        """Serialize the current viewer overlay state to a JSON-compatible dict.

        The returned dict (``version: 2``) captures annotations, measurements,
        saved selections, the **regions** with their full recipe, visual and
        colour state, and the **whole**'s representation and colour. The loaded
        structure is **not** included. Pass the dict to :meth:`import_state` to
        restore it on any viewer that has the same (or a compatible) structure.

        Transient overlay regions (``focus``/``orientation``/``plane``) are
        filtered out: they are not manageable regions and must not survive a
        round-trip as permanent ones.

        Returns
        -------
        dict
            Keys: ``version``, ``annotations``, ``measurements``,
            ``selections``, ``regions``, ``whole``, ``order_high_water_mark``,
            ``uid_high_water_mark``.
        """
        def _to_python(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _to_python(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_to_python(v) for v in obj]
            try:
                import numpy as np
                if isinstance(obj, (np.integer,)):
                    return int(obj)
                if isinstance(obj, (np.floating,)):
                    return float(obj)
            except ImportError:
                pass
            return obj

        regions = []
        for tag, region in self._regions.items():
            if self._TRANSIENT_REGION_TAG.fullmatch(tag):
                continue
            if region.atom_indices is None:
                continue
            regions.append({
                "uid": region.uid,
                "tag": tag,
                "selection": region.selection if isinstance(region.selection, str) else None,
                "provenance": dict(region.provenance),
                "mode": region.mode,
                "order": int(region.order),
                # Layer membership: the field lands in v2 so the format can express
                # it; the behaviour is Phase 9. `Region.layer` does not exist yet.
                "layer": getattr(region, "layer", None),
                "representation": region.representation,
                "preset": region.preset,
                "params": dict(region.repr_params),
                "hidden": bool(region._hidden),  # noqa: SLF001
                # Colour layer owned by this region, keyed by atom index.
                "color_layer": self._color_layer_record(tag),
                # atom_indices is a cache of the recipe result; re-derivable for
                # re-evaluable recipes, authoritative for click-born ones.
                "atom_indices": list(region.atom_indices),
            })

        active = {"atom_indices": list(self.active_selection.atom_indices)}

        whole = {
            "representation": self.whole.representation,
            "preset": self.whole.preset,
            "params": dict(self.whole.params),
            "visible": bool(self.whole.visible),
            "color_scheme": self.whole.color_scheme,
            "color_layer": self._color_layer_record("whole"),
        }

        return _to_python({
            "version": STATE_VERSION,
            "annotations": self.annotations.records(),
            "measurements": self.measurements.records(),
            "selections": self.selections.records(),
            "regions": regions,
            "whole": whole,
            "active_selection": active,
            # The high-water marks let a region created after a reload keep
            # winning over the ones restored from disk. A counter reset to zero
            # would silently invert the precedence of every overlap.
            "order_high_water_mark": int(self._region_order_counter),
            "uid_high_water_mark": int(self._region_uid_counter),
        })

    def _color_layer_record(self, owner: str) -> dict:
        layer = self._atom_color_layers.get(owner, {})
        return {str(int(index)): int(color) for index, color in layer.items()}

    def import_state(self, state: dict, *, clear_first: bool = True) -> None:
        """Restore viewer overlay state from a dict produced by :meth:`export_state`.

        Only ``version: 2`` documents are accepted; a ``version: 1`` document
        raises. The structure must already be loaded (or compatible with the
        stored ``atom_indices``) before calling this method.

        Regions are restored in **topological order** (dependencies before
        dependents), so recipe operands referenced by ``uid`` exist when a
        dependent is rebuilt. A dependency graph that cannot be sorted (a cycle
        or a missing operand) is corrupt: this raises rather than loading part
        of the state.
        """
        if not isinstance(state, dict):
            raise TypeError(f"state must be a dict, got {type(state).__name__}.")
        version = state.get("version")
        if version != STATE_VERSION:
            raise ValueError(
                f"Unsupported state version: {version!r}. This build reads only "
                f"version {STATE_VERSION}; version 1 documents are no longer supported."
            )

        region_records = list(state.get("regions", []))
        ordered_records = self._topologically_ordered_regions(region_records)

        if clear_first:
            self.clear_decorations(labels=True, shapes=False, styles=False, skip_digestion=True)
            self.measurements.clear(skip_digestion=True)
            self.selections.clear(skip_digestion=True)
            for tag in list(self._regions):
                try:
                    self._regions[tag].delete(skip_digestion=True)
                except Exception as exc:
                    emit_suppressed_exception(
                        "StateMixin.import_state.clear_region",
                        exc,
                        context={"tag": tag},
                    )
            self._atom_color_layers = {"whole": {}}

        for msg in state.get("annotations", []):
            if isinstance(msg, dict) and msg.get("op") == "add_label":
                self._send(msg)

        for msg in state.get("measurements", []):
            if isinstance(msg, dict) and msg.get("op") in (
                "add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"
            ):
                self._send(msg)

        for msg in state.get("selections", []):
            if isinstance(msg, dict) and msg.get("op") == "save_selection":
                tag = msg.get("tag")
                if tag and not self.selections.contains(tag, skip_digestion=True):
                    self._send(msg)

        self._restore_whole_state(state.get("whole"))
        self._restore_active_selection(state.get("active_selection"))

        if self._molsys is not None:
            for record in ordered_records:
                try:
                    self._restore_region_v2(record)
                except Exception as exc:
                    emit_suppressed_exception(
                        "StateMixin.import_state.restore_region",
                        exc,
                        context={"tag": record.get("tag")},
                    )

        # Restore the high-water marks so regions created after the import keep
        # winning over the restored ones, and uids never collide.
        self._region_order_counter = max(
            int(state.get("order_high_water_mark", self._region_order_counter)),
            self._region_order_counter,
        )
        self._region_uid_counter = max(
            int(state.get("uid_high_water_mark", self._region_uid_counter)),
            self._region_uid_counter,
        )

        self._send_resolved_atom_colors(replay=True)

    def _topologically_ordered_regions(self, records: list) -> list:
        """Return records ordered so every dependency precedes its dependents.

        Raises ``ValueError`` if the dependency graph has a cycle or references
        an operand uid that is not present in the document.
        """
        by_uid = {}
        for record in records:
            uid = record.get("uid")
            if uid is not None:
                by_uid[str(uid)] = record

        ordered: list = []
        placed: set = set()
        visiting: set = set()

        def visit(record) -> None:
            uid = str(record.get("uid"))
            if uid in placed:
                return
            if uid in visiting:
                raise ValueError(
                    f"Corrupt state: region dependency graph has a cycle involving {uid!r}."
                )
            visiting.add(uid)
            for dep_uid in Region._dependency_uids_from_provenance(  # noqa: SLF001
                dict(record.get("provenance", {}))
            ):
                dep = by_uid.get(str(dep_uid))
                if dep is None:
                    raise ValueError(
                        f"Corrupt state: region {uid!r} depends on missing operand {dep_uid!r}."
                    )
                visit(dep)
            visiting.discard(uid)
            placed.add(uid)
            ordered.append(record)

        for record in records:
            visit(record)
        return ordered

    def _restore_active_selection(self, active: Any) -> None:
        if not isinstance(active, dict):
            return
        indices = active.get("atom_indices")
        if isinstance(indices, list) and indices:
            self.active_selection.set(indices, syntax="Indices", skip_digestion=True)
        else:
            self.active_selection.clear(skip_digestion=True)

    def _restore_whole_state(self, whole: Any) -> None:
        if not isinstance(whole, dict):
            return
        representation = whole.get("representation")
        preset = whole.get("preset")
        params = dict(whole.get("params") or {})
        if representation is not None or preset is not None or params:
            self.whole.set_representation(
                representation,
                preset=preset,
                skip_digestion=True,
                **params,
            )
        color_scheme = whole.get("color_scheme")
        if isinstance(color_scheme, str) and color_scheme:
            self.whole.set_color_scheme(color_scheme, skip_digestion=True)
        if whole.get("visible") is False:
            self.whole.hide(skip_digestion=True)
        base_layer = self._decode_color_layer(whole.get("color_layer"))
        if base_layer:
            self._atom_color_layers["whole"] = base_layer

    def _restore_region_v2(self, record: dict) -> None:
        tag = record.get("tag")
        atom_indices = record.get("atom_indices")
        if not tag or not isinstance(atom_indices, list) or len(atom_indices) == 0:
            return
        provenance = dict(record.get("provenance") or {"kind": "imported", "state_version": 1})
        region = Region(
            self,
            tag,
            record.get("selection") if isinstance(record.get("selection"), str) else "all",
            atom_indices=[int(i) for i in atom_indices],
            uid=str(record["uid"]) if record.get("uid") is not None else None,
            provenance=provenance,
        )
        if record.get("order") is not None:
            region.order = int(record["order"])
        self._regions[tag] = region

        representation = record.get("representation")
        preset = record.get("preset")
        params = dict(record.get("params") or {})
        has_visual = representation is not None or preset is not None or bool(params)
        if has_visual:
            region._send_create(include_visual=False)  # noqa: SLF001
            region.set_representation(
                representation,
                preset=preset,
                skip_digestion=True,
                **params,
            )
        else:
            region._send_create()  # noqa: SLF001

        # mode is restored after the recipe/operands exist (topological order
        # guarantees it); it validates against the re-evaluability of the recipe.
        mode = record.get("mode")
        if mode == "dynamic":
            try:
                region.mode = "dynamic"
            except ValueError:
                pass  # a recipe that is no longer re-evaluable stays static

        if record.get("hidden"):
            region.hide(skip_digestion=True)

        color_layer = self._decode_color_layer(record.get("color_layer"))
        if color_layer:
            self._atom_color_layers[tag] = color_layer

    @staticmethod
    def _decode_color_layer(raw: Any) -> dict:
        if not isinstance(raw, dict):
            return {}
        return {int(index): int(color) for index, color in raw.items()}


StateMixin.__module__ = "molsysviewer.viewer"
for _name, _value in StateMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception as exc:
            emit_suppressed_exception(
                "StateMixin.__module_assignment__",
                exc,
                context={"callable": _name},
            )
