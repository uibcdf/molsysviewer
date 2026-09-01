from __future__ import annotations

from smonitor import signal

from .._private.argdigest import digest


from contextlib import nullcontext
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .._private.smonitor.warnings import StateStructureDiffersWarning, warn
from .._private.smonitor_emit import emit_suppressed_exception
from ..regions import Region
from ..shapes._registry import register_shape_layer

STATE_VERSION = 2


def _structure_identity(molsys) -> dict | None:
    """What a state document records about the system it was written from.

    Two fields, and the split is the whole design. `n_atoms` decides whether the
    document's atom indices can address anything at all; the fingerprint decides whether
    they address what they were written for.

    The fingerprint is **topological, never conformational**: it is taken over atom
    names in order, so a state saved at frame 0 loads onto frame 500 of the same
    trajectory, which is exactly the portability the document promises. Measured at
    0.90 ms for 4,369 atoms -- cheaper than asking for three separate counts, because it
    is one call rather than three, each paying its own digestion.
    """

    if molsys is None:
        return None
    import hashlib

    import molsysmt as msm

    names = msm.get(molsys, element="atom", atom_name=True, skip_digestion=True)
    digest = hashlib.sha256("\n".join(map(str, names)).encode("utf-8")).hexdigest()
    return {"n_atoms": len(names), "fingerprint": f"sha256:{digest}"}



class StateMixin:
    def _state_owner_context(self, record: dict):
        owner = record.get("owner")
        if isinstance(owner, str) and owner.strip():
            return self.attributed_to(owner)
        return nullcontext()

    @signal(tags=["state", "query"])
    @digest()
    def export_state(self) -> dict:
        """Serialize the current viewer overlay state to a JSON-compatible dict.

        The returned dict (``version: 2``) captures annotations, measurements,
        saved selections, the **regions** with their full recipe, visual and
        colour state, clipping **sections**, and the **whole**'s representation
        and colour. The loaded structure is **not** included. Pass the dict to
        :meth:`import_state` to restore it on any viewer that has the same (or a
        compatible) structure.

        Transient overlay regions (``focus``/``orientation``/``plane``) are
        filtered out: they are not manageable regions and must not survive a
        round-trip as permanent ones.

        Returns
        -------
        dict
            Keys: ``version``, ``active_selection``, ``annotations``, ``layers``,
            ``measurement_settings``, ``measurements``, ``regions``, ``sections``,
            ``selections``, ``shapes``, ``whole``, ``order_high_water_mark``,
            ``uid_high_water_mark``, ``tag_high_water_marks``, ``structure``.

            ``structure`` records the system the document was written from -- its atom
            count and a topological fingerprint -- and is absent when no system is
            loaded. Objects that hold atoms also carry the identity of those atoms
            -- chain id, group id, group name and atom name -- beside their indices,
            which is what lets :meth:`import_state` re-resolve them onto a different
            system. A document without these keys imports cleanly.
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
            provenance = dict(region.provenance)
            record = {
                "uid": region.uid,
                "tag": tag,
                "selection": region.selection if isinstance(region.selection, str) else None,
                "provenance": provenance,
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
            }
            if region.owner is not None:
                record["owner"] = region.owner
            if not (region.mode == "dynamic" and Region._is_reevaluable_provenance(provenance)):  # noqa: SLF001
                # atom_indices is authoritative for static/click-born regions. For
                # dynamic regions it is a runtime frame cache and must be re-derived.
                record["atom_indices"] = list(region.atom_indices)
            regions.append(record)

        annotations = []
        for raw in self.annotations.records():
            record = deepcopy(raw)
            options = dict(record.get("options") or {})
            atom_indices = list(options.pop("atom_indices", []))
            record["options"] = options
            anchor = {"type": "atoms", "indices": atom_indices}
            # Beside the indices, not instead of them: the indices stay the fast path
            # when the document comes back to the same system, and the identities are
            # what makes it survive a different one.
            identity = self._identities_for(atom_indices)
            if identity:
                anchor["identity"] = identity
            record["anchor"] = anchor
            annotation = self.annotations.get(str(record.get("tag")), skip_digestion=True)
            record["hidden"] = bool(getattr(annotation, "_hidden", False))
            if getattr(annotation, "owner", None) is not None:
                record["owner"] = annotation.owner
            record["broken"] = bool(getattr(annotation, "broken", False))
            record["broken_reason"] = getattr(annotation, "broken_reason", None)
            annotations.append(record)

        measurements = []
        for raw in self.measurements.records():
            record = deepcopy(raw)
            measurement = self.measurements.get(str(record.get("tag")), skip_digestion=True)
            record["hidden"] = bool(getattr(measurement, "_hidden", False))
            if measurement.owner is not None:
                record["owner"] = measurement.owner
            record["broken"] = bool(getattr(measurement, "broken", False))
            record["broken_reason"] = getattr(measurement, "broken_reason", None)
            options = dict(record.get("options") or {})
            endpoints = options.get("endpoint_atom_indices")
            if isinstance(endpoints, list):
                identity = [self._identities_for(group or []) for group in endpoints]
                if all(entry is not None for entry in identity):
                    options["endpoint_identity"] = identity
                    record["options"] = options
            measurements.append(record)

        shapes = []
        for raw in self.shapes.records(skip_digestion=True):
            record = deepcopy(raw)
            options = dict(record.get("options") or {})
            tag = options.get("tag") or record.get("tag")
            if not isinstance(tag, str):
                continue
            shape = self.shapes.get(tag, skip_digestion=True)
            if shape is None:
                continue
            record["tag"] = tag
            record["layer_tag"] = shape.layer_tag
            if shape.owner is not None:
                record["owner"] = shape.owner
            record["hidden"] = bool(shape._hidden)  # noqa: SLF001
            shapes.append(record)

        layers = []
        for layer in self.layers.values():
            if layer.provenance != "user":
                continue
            record = {
                "tag": layer.tag,
                "kind": layer.kind,
                "meta": dict(layer.meta),
                "provenance": layer.provenance,
                "hidden": bool(layer._hidden),  # noqa: SLF001
            }
            if layer.owner is not None:
                record["owner"] = layer.owner
            layers.append(record)

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
            # Absent when no system is loaded, and absent from every document written
            # before this key existed. Contract S5's additive-key rule: a reader that
            # does not find it imports cleanly, and must not be told off for it.
            **({"structure": identity} if (identity := self._structure_identity()) else {}),
            "annotations": annotations,
            "measurements": measurements,
            "measurement_settings": self.measurements.settings(skip_digestion=True),
            "shapes": shapes,
            "layers": layers,
            "selections": self._selection_records_with_identity(),
            "regions": regions,
            "sections": deepcopy(self._section_history),
            "whole": whole,
            "active_selection": active,
            # The high-water marks let a region created after a reload keep
            # winning over the ones restored from disk. A counter reset to zero
            # would silently invert the precedence of every overlap.
            "order_high_water_mark": int(self._region_order_counter),
            "uid_high_water_mark": int(self._region_uid_counter),
            "tag_high_water_marks": {
                domain: manager.high_water_mark
                for domain, manager in self._tag_managers.items()
            },
        })

    @signal(tags=["state"])
    @digest()
    def save_state(self, path: str | os.PathLike[str]) -> None:
        """Write the current overlay state to a UTF-8 JSON file atomically.

        This is the file counterpart of :meth:`export_state`. It does not
        include the molecular system, camera, or undo history. Load the same
        (or a compatible) structure before passing the file to
        :meth:`load_state`.
        """
        destination = Path(path)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(self.export_state(), temporary, indent=2, sort_keys=True)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, destination)
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    @signal(tags=["state"])
    @digest()
    def load_state(
        self,
        path: str | os.PathLike[str],
        *,
        clear_first: bool = True,
        on_conflict: str = "raise",
    ) -> None:
        """Load overlay state from JSON onto an already loaded structure.

        The document is parsed before the current scene is changed. State
        validation, conflict handling, and history invalidation are delegated
        to :meth:`import_state`.
        """
        state = json.loads(Path(path).read_text(encoding="utf-8"))
        self.import_state(
            state,
            clear_first=clear_first,
            on_conflict=on_conflict,
        )

    def _color_layer_record(self, owner: str) -> dict:
        layer = self._atom_color_layers.get(owner, {})
        return {str(int(index)): int(color) for index, color in layer.items()}

    @signal(tags=["state"])
    @digest()
    def import_state(
        self,
        state: dict,
        *,
        clear_first: bool = True,
        on_conflict: str = "raise",
    ) -> None:
        """Restore viewer overlay state from a dict produced by :meth:`export_state`.

        Only ``version: 2`` documents are accepted; a ``version: 1`` document
        raises. The structure must already be loaded before calling this method,
        but it need not be the one the document was written from.

        When it is not -- the recorded ``structure`` fingerprint does not match the
        loaded system -- the stored atom indices are not replayed, because an index is
        where an atom sat and not what it is. Instead each object is re-resolved:
        regions by re-evaluating their recipe (Contract R), everything else by looking
        up the atom identities the document carries. Whatever cannot be resolved is
        marked broken rather than restored somewhere plausible, and a
        ``StateStructureDiffersWarning`` names both systems.

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
        reindexing = self._structure_changed(state.get("structure"))
        if reindexing:
            recorded = state.get("structure") or {}
            current = self._structure_identity() or {}
            warn(
                StateStructureDiffersWarning(
                    extra={
                        "saved_atoms": recorded.get("n_atoms"),
                        "current_atoms": current.get("n_atoms"),
                    },
                ),
                stacklevel=3,
            )
        if on_conflict not in {"raise", "skip", "rename"}:
            raise ValueError("on_conflict must be 'raise', 'skip', or 'rename'.")

        region_records = list(state.get("regions", []))
        ordered_records = self._topologically_ordered_regions(region_records)
        if not clear_first and on_conflict == "raise":
            self._preflight_import_conflicts(state)
        order_high_water_mark_before_import = self._region_order_counter
        self._state_reindexing = reindexing
        try:
            with self.history.suspended() as already_suspended:
                self._restore_high_water_marks(state)
                if clear_first:
                    self._clear_state_for_import()
                hidden_layers, layer_tag_map = self._restore_user_layers(
                    state.get("layers", []),
                    on_conflict=on_conflict,
                )
                self._restore_whole_state(state.get("whole"))
                measurement_settings = state.get("measurement_settings")
                if isinstance(measurement_settings, dict):
                    policy = measurement_settings.get("endpoint_policy_default")
                    if isinstance(policy, str):
                        self.measurements.set_endpoint_policy(policy, skip_digestion=True)
                    representative_atoms = measurement_settings.get("representative_atoms")
                    if isinstance(representative_atoms, dict):
                        for target, atom_name in representative_atoms.items():
                            self.measurements.set_representative_atom(
                                str(target), str(atom_name), skip_digestion=True
                            )
                if self._molsys is not None:
                    for record in ordered_records:
                        tag = self._import_tag("region", str(record.get("tag") or ""), on_conflict)
                        if tag is None:
                            continue
                        restored_record = deepcopy(record)
                        restored_record["tag"] = tag
                        restored_record["layer"] = layer_tag_map.get(record.get("layer"), record.get("layer"))
                        self._restore_region_v2(restored_record)
                self._restore_annotations(
                    state.get("annotations", []),
                    on_conflict=on_conflict,
                    layer_tag_map=layer_tag_map,
                )
                self._restore_measurements(
                    state.get("measurements", []),
                    on_conflict=on_conflict,
                    layer_tag_map=layer_tag_map,
                )
                self._restore_shapes(
                    state.get("shapes", []),
                    on_conflict=on_conflict,
                    layer_tag_map=layer_tag_map,
                )
                self._restore_sections(state.get("sections", []), on_conflict=on_conflict)
                for layer_tag in hidden_layers:
                    layer = self.layers.get(layer_tag)
                    if layer is not None:
                        layer.hide(skip_digestion=True)
                self._restore_selections(state.get("selections", []), on_conflict=on_conflict)
                self._restore_active_selection(state.get("active_selection"))
                self._send_resolved_atom_colors(replay=True)
                self._sync_whole_summary_runtime()
                self._region_order_counter = max(
                    order_high_water_mark_before_import,
                    int(state.get("order_high_water_mark", 0)),
                    max(
                        (int(region.order) for region in self._regions.values()),
                        default=0,
                    ),
                )

        finally:
            self._state_reindexing = False

        if not already_suspended:
            self.history.clear()

    def _structure_identity(self) -> dict | None:
        """The system's identity, computed once per system rather than per snapshot.

        `export_state` does not only run when a user saves: `scene_history` checkpoints
        it after every undoable operation. Measured, the fingerprint was 68-82% of the
        whole export -- paid on every click, for a value that changes only when the
        system does.

        The marker pairs object identity with the atom count so that both ways a system
        can change miss the cache: replaced outright (a new object) and grown in place
        (a live edit that adds atoms keeps the object but not the count).
        """
        molsys = self._molsys
        count = getattr(molsys, "get_n_atoms", None)
        if molsys is None or count is None:
            # No system, or a placeholder that cannot answer how many atoms it has.
            # Either way there is nothing to identify, and by Contract S5 a document
            # written without the key imports cleanly, so omitting it is safe.
            return None
        marker = (id(molsys), count())
        cached = getattr(self, "_structure_identity_memo", None)
        if cached is not None and cached[0] == marker:
            return cached[1]
        identity = _structure_identity(molsys)
        self._structure_identity_memo = (marker, identity)
        return identity

    def _selection_records_with_identity(self) -> list[dict]:
        """Saved selections, each carrying what its atoms are as well as where they sat."""
        records = []
        for raw in self.selections.records():
            record = deepcopy(raw)
            identity = self._identities_for(record.get("atom_indices") or [])
            if identity:
                record["identity"] = identity
            records.append(record)
        return records

    def _atom_identities(self) -> list[tuple] | None:
        """Every atom's structural identity, in index order, computed once per system.

        The tuple is ``(chain_id, group_id, group_name, atom_name)`` -- what an atom *is*
        rather than where it sits in an array. It is what lets an object that was picked
        by hand survive a change of system: a region carries a recipe and can be
        re-evaluated, but an annotation on three atoms the user clicked has no recipe to
        re-evaluate, only these tuples.

        Measured at ~7 ms for 4,369 atoms in a single `msm.get`, memoised on the same
        marker as the fingerprint because `export_state` runs on every undoable
        operation and this must not be paid per checkpoint.
        """
        molsys = self._molsys
        count = getattr(molsys, "get_n_atoms", None)
        if molsys is None or count is None:
            return None
        marker = (id(molsys), count())
        cached = getattr(self, "_atom_identities_memo", None)
        if cached is not None and cached[0] == marker:
            return cached[1]
        try:
            import molsysmt as msm

            chain_id, group_id, group_name, atom_name = msm.get(
                molsys, element="atom", chain_id=True, group_id=True,
                group_name=True, atom_name=True, skip_digestion=True,
            )
            identities = [
                (str(c), str(g), str(gn), str(an))
                for c, g, gn, an in zip(chain_id, group_id, group_name, atom_name, strict=True)
            ]
        except Exception:
            # A system that cannot describe its atoms cannot anchor by identity. The
            # document simply carries no identity block, and by Contract S5 that is a
            # document a reader imports without complaint.
            identities = None
        self._atom_identities_memo = (marker, identities)
        return identities

    def _identities_for(self, atom_indices) -> list[list[str]] | None:
        """The identity block an exported object carries beside its atom indices."""
        identities = self._atom_identities()
        if not identities:
            return None
        try:
            return [list(identities[int(i)]) for i in atom_indices]
        except (IndexError, ValueError, TypeError):
            return None

    def _reindex_by_identity(self, recorded_identities) -> list[int] | None:
        """Resolve saved atom identities against the loaded system.

        Returns None when the block is unusable or any atom is unresolvable, because a
        partially resolved anchor is the plausible-wrong this codebase treats as worse
        than a visible failure: an annotation that silently lost two of its three atoms
        still draws, and still looks right. The caller marks the object broken instead.

        An identity that matches more than one atom here is refused for the same reason
        -- picking the first would be a guess wearing the clothes of a resolution.
        """
        if not isinstance(recorded_identities, list) or not recorded_identities:
            return None
        identities = self._atom_identities()
        if not identities:
            return None
        table: dict[tuple, int | None] = {}
        for index, identity in enumerate(identities):
            table[identity] = None if identity in table else index
        resolved = []
        for entry in recorded_identities:
            if not isinstance(entry, (list, tuple)) or len(entry) != 4:
                return None
            index = table.get(tuple(str(field) for field in entry))
            if index is None:
                return None
            resolved.append(index)
        return resolved

    def _structure_changed(self, recorded: Any) -> bool:
        """Whether this document was written from a system other than the loaded one.

        This is a *trigger*, not a gate. An earlier design refused the import outright
        when the atom counts differed, which was both too strict and too weak: too
        strict because loading a state onto a related structure is a capability this
        viewer has and Contract S7 tests, and too weak because it never fired on the
        dangerous case -- a system of the same size whose indices mean different atoms.

        So the question is not "may this be imported" but "may the stored indices be
        trusted". When they may not, restoration re-resolves what carries a recipe
        (Contract R's region expressions, and the anchors that keep theirs) instead of
        replaying indices that address the wrong atoms.

        A document with no ``structure`` key answers no: by Contract S5 it predates the
        key, and its indices were written for whatever is loaded now.
        """
        if not isinstance(recorded, dict):
            return False
        current = self._structure_identity()
        if current is None:
            return False
        return (
            recorded.get("n_atoms") != current["n_atoms"]
            or recorded.get("fingerprint") != current["fingerprint"]
        )

    def _restore_high_water_marks(self, state: dict) -> None:
        self._region_order_counter = max(
            int(state.get("order_high_water_mark", self._region_order_counter)),
            self._region_order_counter,
        )
        self._region_uid_counter = max(
            int(state.get("uid_high_water_mark", self._region_uid_counter)),
            self._region_uid_counter,
        )
        marks = state.get("tag_high_water_marks", {})
        if isinstance(marks, dict):
            for domain, mark in marks.items():
                manager = self._tag_managers.get(str(domain))
                if manager is not None:
                    manager.restore(int(mark))

    def _preflight_import_conflicts(self, state: dict) -> None:
        def tags(records: Any) -> list[str]:
            if not isinstance(records, list):
                return []
            result = []
            for record in records:
                if not isinstance(record, dict):
                    continue
                tag = record.get("tag") or (record.get("options") or {}).get("tag")
                if isinstance(tag, str) and tag:
                    result.append(tag)
            return result

        incoming = {
            "layer": tags(state.get("layers")),
            "region": tags(state.get("regions")),
            "annotation": tags(state.get("annotations")),
            "measurement": tags(state.get("measurements")),
            "shape": tags(state.get("shapes")),
            "section": tags(state.get("sections")),
            "selection": tags(state.get("selections")),
        }
        for domain, incoming_tags in incoming.items():
            manager = self._tag_managers[domain]
            existing = set(manager._existing_tags())  # noqa: SLF001
            if domain == "selection":
                existing.update(self.selections.tags(skip_digestion=True))
            for tag in incoming_tags:
                if tag in existing:
                    raise ValueError(f"Cannot import {domain} tag {tag!r}: it already exists.")

    def _clear_state_for_import(self) -> None:
        self.shapes.clear(skip_digestion=True)
        self.annotations.clear(skip_digestion=True)
        self.measurements.clear(skip_digestion=True)
        self.selections.clear(skip_digestion=True)
        self.scene.clear_sections()
        for tag in list(self._regions):
            self._regions[tag].delete(skip_digestion=True)
        dict.clear(self._layers)
        self._atom_color_layers = {"whole": {}}

    def _restore_user_layers(self, records: Any, *, on_conflict: str) -> tuple[list[str], dict[str, str]]:
        hidden: list[str] = []
        tag_map: dict[str, str] = {}
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict) or not record.get("tag"):
                continue
            tag = self._import_tag("layer", str(record["tag"]), on_conflict)
            if tag is None:
                continue
            tag_map[str(record["tag"])] = tag
            with self._state_owner_context(record):
                layer = self.layers.add(
                    tag,
                    kind=record.get("kind"),
                    meta=dict(record.get("meta") or {}),
                    skip_digestion=True,
                )
            if record.get("hidden"):
                hidden.append(layer.tag)
        return hidden, tag_map

    def _restore_annotations(
        self,
        records: Any,
        *,
        on_conflict: str,
        layer_tag_map: dict[str, str],
    ) -> None:
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict) or record.get("op") != "add_label":
                continue
            original_tag = str(record.get("tag") or "")
            tag = self._import_tag("annotation", original_tag, on_conflict)
            if tag is None:
                continue
            options = dict(record.get("options") or {})
            layer_tag = self._restored_layer_tag(
                options.get("layer_tag"),
                original_object_tag=original_tag,
                layer_tag_map=layer_tag_map,
            )
            anchor = record.get("anchor")
            if isinstance(anchor, dict) and anchor.get("type") == "atoms":
                atom_indices = list(anchor.get("indices") or [])
            else:
                atom_indices = list(options.get("atom_indices") or [])
            unresolved = False
            if getattr(self, "_state_reindexing", False):
                # The indices were written for another system, so they are not evidence
                # of anything here. Either the identities resolve, or the annotation is
                # broken -- restoring it at the old indices would put a label on whatever
                # atoms happen to occupy those slots, which is the failure this whole
                # mechanism exists to prevent.
                resolved = self._reindex_by_identity(
                    anchor.get("identity") if isinstance(anchor, dict) else None
                )
                if resolved is None:
                    unresolved = True
                else:
                    atom_indices = resolved
            missing = self._missing_anchor_indices(atom_indices)
            if not atom_indices or missing or unresolved:
                history_record = deepcopy(record)
                history_options = dict(history_record.get("options") or {})
                history_options["atom_indices"] = atom_indices
                history_record["options"] = history_options
                with self._state_owner_context(record):
                    annotation = self.annotations._ensure_layer(  # noqa: SLF001
                        tag,
                        layer_tag=layer_tag,
                    )
                annotation.broken = True
                annotation.broken_reason = (
                    "Its atoms could not be found in the loaded system."
                    if unresolved
                    else self._broken_anchor_reason(missing, empty=not atom_indices)
                )
                annotation._hidden = bool(record.get("hidden"))  # noqa: SLF001
                self._annotation_history.append(history_record)
                continue
            with self._state_owner_context(record):
                annotation = self.annotations.add(
                    str(options.get("text") or ""),
                    atom_indices=atom_indices,
                    tag=tag,
                    layer_tag=layer_tag,
                    label_style=dict(options.get("style") or {}),
                    skip_digestion=True,
                )
            if record.get("hidden"):
                annotation.hide(skip_digestion=True)

    def _restore_measurements(
        self,
        records: Any,
        *,
        on_conflict: str,
        layer_tag_map: dict[str, str],
    ) -> None:
        kinds = {
            "add_distance_measurement": "distance",
            "add_angle_measurement": "angle",
            "add_dihedral_measurement": "dihedral",
        }
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict) or record.get("op") not in kinds:
                continue
            original_tag = str(record.get("tag") or "")
            tag = self._import_tag("measurement", original_tag, on_conflict)
            if tag is None:
                continue
            options = dict(record.get("options") or {})
            layer_tag = self._restored_layer_tag(
                options.get("layer_tag"),
                original_object_tag=original_tag,
                layer_tag_map=layer_tag_map,
            )
            picks = [list(item) for item in options.get("picks_atom_indices", [])]
            unresolved = False
            if getattr(self, "_state_reindexing", False):
                identity = options.get("endpoint_identity")
                resolved = None
                if isinstance(identity, list) and len(identity) == len(picks):
                    resolved = [self._reindex_by_identity(group) for group in identity]
                    if any(group is None for group in resolved):
                        resolved = None
                if resolved is None:
                    unresolved = True
                else:
                    picks = resolved
                    options["picks_atom_indices"] = picks
                    options["endpoint_atom_indices"] = picks
            missing = self._missing_anchor_indices([index for pick in picks for index in pick])
            if not picks or any(not pick for pick in picks) or missing or unresolved:
                with self._state_owner_context(record):
                    measurement = self.measurements._ensure_layer(  # noqa: SLF001
                        tag,
                        layer_tag=layer_tag,
                    )
                measurement.broken = True
                measurement.broken_reason = (
                    "Its endpoints could not be found in the loaded system."
                    if unresolved
                    else self._broken_anchor_reason(
                        missing,
                        empty=not picks or any(not pick for pick in picks),
                    )
                )
                measurement._hidden = bool(record.get("hidden"))  # noqa: SLF001
                self._measurement_history.append(deepcopy(record))
                continue
            with self._state_owner_context(record):
                measurement = self.measurements.add(
                    kinds[str(record["op"])],
                    *picks,
                    tag=tag,
                    layer_tag=layer_tag,
                    endpoint_policy=options.get("endpoint_policy"),
                    measurement_style=dict(options.get("style") or {}),
                    skip_digestion=True,
                )
            if record.get("hidden"):
                measurement.hide(skip_digestion=True)

    def _restore_shapes(
        self,
        records: Any,
        *,
        on_conflict: str,
        layer_tag_map: dict[str, str],
    ) -> None:
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict) or not str(record.get("op", "")).startswith("add_"):
                continue
            original_tag = str(record.get("tag") or (record.get("options") or {}).get("tag") or "")
            tag = self._import_tag("shape", original_tag, on_conflict)
            if tag is None:
                continue
            msg = deepcopy(record)
            msg.pop("hidden", None)
            msg.pop("layer_tag", None)
            options = dict(msg.get("options") or {})
            options["tag"] = tag
            requested_layer_tag = record.get("layer_tag") or options.get("layer_tag")
            registration_layer_tag = self._restored_layer_tag(
                requested_layer_tag,
                original_object_tag=original_tag,
                layer_tag_map=layer_tag_map,
            )
            options["layer_tag"] = registration_layer_tag or tag
            msg["tag"] = tag
            msg["options"] = options
            with self._state_owner_context(record):
                shape = register_shape_layer(
                    self,
                    tag,
                    layer_tag=registration_layer_tag,
                    meta=options.get("meta"),
                )
            self._send(msg)
            if record.get("hidden"):
                shape.hide(skip_digestion=True)

    def _restore_selections(self, records: Any, *, on_conflict: str) -> None:
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict) or record.get("op") != "save_selection":
                continue
            tag = self._import_tag("selection", str(record.get("tag") or ""), on_conflict)
            if tag is None:
                continue
            atom_indices = list(record.get("atom_indices") or [])
            if getattr(self, "_state_reindexing", False):
                resolved = self._reindex_by_identity(record.get("identity"))
                if resolved is None:
                    # Unlike an annotation or a measurement, a saved selection has no
                    # broken state to fall into -- until now it was restored holding
                    # whatever indices the document carried, out of range or not. Not
                    # restoring it is the honest outcome: an empty tag would claim the
                    # selection survived the change of system, and it did not.
                    continue
                atom_indices = resolved
            self.selections.add(
                tag,
                atom_indices=atom_indices,
                items=list(record.get("items") or []),
                skip_digestion=True,
            )

    def _restore_sections(self, records: Any, *, on_conflict: str) -> None:
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict) or not record.get("tag"):
                continue
            tag = self._import_tag("section", str(record["tag"]), on_conflict)
            if tag is None:
                continue
            with self._state_owner_context(record):
                section = self.scene.add_section(
                    point=list(record.get("point") or []),
                    normal=list(record.get("normal") or []),
                    invert=bool(record.get("invert", False)),
                    tag=tag,
                )
                if record.get("hidden"):
                    section.hide(skip_digestion=True)

    def _import_tag(self, domain: str, tag: str, policy: str) -> str | None:
        manager = self._tag_managers[domain]
        existing = set(manager._existing_tags())  # noqa: SLF001
        if domain == "selection":
            existing.update(self.selections.tags(skip_digestion=True))
        if tag not in existing:
            return tag
        if policy == "skip":
            return None
        if policy == "raise":
            raise ValueError(f"Cannot import {domain} tag {tag!r}: it already exists.")
        suffix = 2
        candidate = f"{tag}_{suffix}"
        while candidate in existing:
            suffix += 1
            candidate = f"{tag}_{suffix}"
        return candidate

    @staticmethod
    def _restored_layer_tag(
        requested_layer_tag: Any,
        *,
        original_object_tag: str,
        layer_tag_map: dict[str, str],
    ) -> str | None:
        """Preserve the distinction between implicit and user-owned layers."""
        if (
            requested_layer_tag == original_object_tag
            and requested_layer_tag not in layer_tag_map
        ):
            return None
        return layer_tag_map.get(requested_layer_tag, requested_layer_tag)

    def _missing_anchor_indices(self, indices: list) -> list[int]:
        n_atoms = int(self._molsys.get_n_atoms()) if self._molsys is not None else 0
        return sorted({int(index) for index in indices if int(index) < 0 or int(index) >= n_atoms})

    @staticmethod
    def _broken_anchor_reason(missing: list[int], *, empty: bool = False) -> str:
        if empty:
            return "Anchor contains no atoms."
        return f"Missing anchor atom indices: {missing}"

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
        if not tag:
            return
        provenance = dict(record.get("provenance") or {"kind": "imported", "state_version": 1})
        if getattr(self, "_state_reindexing", False) and Region._is_reevaluable_provenance(provenance):  # noqa: SLF001
            # Contract R: a region is its recipe, not the atoms the recipe happened to
            # select. The document has carried the expression all along; until now
            # import replayed the indices instead, so a region built on one system
            # arrived on another still holding the first one's atoms -- indices past the
            # end of the system it had just been loaded into. Re-evaluating is what the
            # contract always said this record meant.
            atom_indices = None
        if not isinstance(atom_indices, list):
            if Region._is_reevaluable_provenance(provenance):  # noqa: SLF001
                with self._state_owner_context(record):
                    probe = Region(
                        self,
                        str(tag),
                        record.get("selection") if isinstance(record.get("selection"), str) else "all",
                        atom_indices=[],
                        uid=str(record["uid"]) if record.get("uid") is not None else None,
                        provenance=provenance,
                    )
                atom_indices = self._evaluate_region_provenance(probe) or []
            else:
                return
        if len(atom_indices) == 0:
            return
        with self._state_owner_context(record):
            region = Region(
                self,
                tag,
                record.get("selection") if isinstance(record.get("selection"), str) else "all",
                atom_indices=[int(i) for i in atom_indices],
                uid=str(record["uid"]) if record.get("uid") is not None else None,
                provenance=provenance,
            )
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

        if record.get("order") is not None:
            region.order = int(record["order"])

        layer = record.get("layer")
        if isinstance(layer, str) and layer:
            region._set_layer_membership(layer)  # noqa: SLF001

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
