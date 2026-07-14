from __future__ import annotations

from ..layers import Layer, SceneObject


class SceneRegistryMixin:
    _ANNOTATION_SUMMARY_OPS = {"add_label", "update_label"}
    _MEASUREMENT_SUMMARY_OPS = {
        "add_distance_measurement",
        "add_angle_measurement",
        "add_dihedral_measurement",
        "set_measurement_settings",
    }
    _SHAPE_SUMMARY_OPS = {
        "add_sphere",
        "add_network_links",
        "add_alpha_sphere_set",
        "add_pocket_surface",
        "add_pocket_blob",
        "add_scalar_isosurface",
        "add_channel_tube",
        "add_tetrahedra",
        "add_triangle_faces",
        "add_anisotropy_ellipsoids",
        "add_displacement_vectors",
        "add_pharmacophore_features",
        "add_interaction_sites",
        "add_hbonds",
        "add_rings",
        "clear_shapes_by_tag",
    }

    def _annotation_summary_records(self) -> list[dict]:
        records = self.annotations.info(skip_digestion=True)
        return [
            {
                "kind": record.get("kind"),
                "tag": record.get("tag"),
                "layer_tag": record.get("layer_tag"),
                "text": record.get("text"),
                "style": dict(record.get("style") or {}),
                "n_atoms": int(record.get("n_atoms") or 0),
                "atom_indices": list(record.get("atom_indices") or []),
                "anchor": {
                    "type": "atoms",
                    "indices": list(record.get("atom_indices") or []),
                },
                "hidden": not bool(record.get("visible")),
                "broken": bool(record.get("broken")),
                "broken_reason": record.get("broken_reason"),
            }
            for record in records
        ]

    def _measurement_summary_records(self) -> list[dict]:
        from .. import pyunitwizard as puw

        records = []
        for record in self.measurements.info():
            value = record.get("value")
            kind = str(record.get("kind") or "measurement")
            unit = "angstrom" if kind == "distance" else "degree"
            atom_indices = sorted({
                int(index)
                for pick in record.get("picks_atom_indices") or []
                for index in pick
            })
            records.append(
                {
                    "kind": kind,
                    "tag": record.get("tag"),
                    "layer_tag": record.get("layer_tag"),
                    "n_picks": int(record.get("n_picks") or 0),
                    "atom_indices": atom_indices,
                    "value": None if value is None else float(puw.get_value(value, to_unit=unit)),
                    "unit": unit,
                    "endpoint_labels": list(record.get("endpoint_labels") or []),
                    "endpoint_policy": record.get("endpoint_policy"),
                    "hidden": not bool(record.get("visible")),
                    "broken": bool(record.get("broken")),
                    "broken_reason": record.get("broken_reason"),
                }
            )
        return records

    @staticmethod
    def _minmax_downsample(values: list[float], max_points: int = 240) -> tuple[list[float], list[int]]:
        if len(values) <= max_points:
            return list(values), list(range(len(values)))
        import math

        bucket_size = max(1, math.ceil(len(values) / max(1, max_points // 2)))
        sampled: list[tuple[int, float]] = []
        for start in range(0, len(values), bucket_size):
            bucket = values[start:start + bucket_size]
            low = min(range(len(bucket)), key=bucket.__getitem__)
            high = max(range(len(bucket)), key=bucket.__getitem__)
            for offset in sorted({low, high}):
                sampled.append((start + offset, float(bucket[offset])))
        return [value for _, value in sampled], [index for index, _ in sampled]

    def _measurement_series_payload(self, tag: str, request_id: int | None = None) -> dict:
        from .. import pyunitwizard as puw

        info = self.measurements.info(tag)
        if not info:
            raise ValueError(f"No measurement found with tag {tag!r}.")
        record = info[0]
        kind = str(record.get("kind") or "measurement")
        unit = "angstrom" if kind == "distance" else "degree"
        quantity = self.measurements.series(tag)
        values = [] if quantity is None else [
            float(value) for value in puw.get_value(quantity, to_unit=unit)
        ]
        sparkline, sparkline_indices = self._minmax_downsample(values)
        return {
            "op": "measurement_series",
            "tag": tag,
            "request_id": request_id,
            "unit": unit,
            "n_frames": len(values),
            "sparkline": sparkline,
            "sparkline_indices": sparkline_indices,
            "series_index": self.measurements._active_series_index(len(values)) if values else None,  # noqa: SLF001
        }

    def _shape_summary_records(self) -> list[dict]:
        from .. import pyunitwizard as puw

        display = {
            "link": ("Links", "links"),
            "triangle-faces": ("Triangle Faces", "triangle_faces"),
            "channel-tube": ("Channel Tube", "channel_tube"),
            "anisotropy-ellipsoids": ("Anisotropy Ellipsoids", "anisotropy_ellipsoids"),
            "displacement-vectors": ("Displacement Vectors", "displacement_vectors"),
            "pocket-blob": ("Pocket Blob", "pocket_blob"),
            "scalar-isosurface": ("Pocket Blob", "pocket_blob"),
            "pocket-surface": ("Pocket Surface", "pocket_surface"),
            "alpha-sphere-set": ("Alpha Sphere Set", "alpha_sphere_set"),
            "hbonds": ("Hydrogen Bonds", "hbonds"),
            "rings": ("Rings", "rings"),
            "pharmacophore": ("Interaction Sites", "interaction_sites"),
        }

        def labels(kind: str) -> tuple[str, str]:
            return display.get(
                kind,
                (kind.replace("-", " ").replace("_", " ").title(), kind.replace("-", "_")),
            )

        records = []
        for record in self.shapes.info(skip_digestion=True):
            kind = str(record.get("kind") or "shape")
            title, subtitle = labels(kind)
            radius = record.get("radius")
            radius_payload = None if radius is None else {
                "magnitude": float(puw.get_value(radius, to_unit="angstrom")),
                "unit": "angstrom",
            }
            records.append({
                "op": record.get("op"),
                "kind": record.get("kind"),
                "tag": record.get("tag"),
                "layer_tag": record.get("layer_tag"),
                "title": title,
                "subtitle": subtitle,
                "atom_indices": list(record.get("atom_indices") or []),
                "hidden": not bool(record.get("visible")),
                "color": record.get("color"),
                "n_colors": record.get("n_colors"),
                "radius": radius_payload,
                "n_radii": record.get("n_radii"),
                "alpha": record.get("alpha"),
                "radius_scale": record.get("radius_scale"),
                "length_scale": record.get("length_scale"),
                "broken": bool(record.get("broken")),
                "broken_reason": record.get("broken_reason"),
            })
        return records

    def _layer_summary_records(self) -> list[dict]:
        return [
            {
                "tag": record.get("tag"),
                "provenance": record.get("provenance"),
                "hidden": not bool(record.get("visible")),
            }
            for record in self.layers.info(skip_digestion=True)
        ]

    def _sync_annotation_summaries_runtime(self) -> None:
        self._send_runtime_only({
            "op": "set_annotation_summaries",
            "annotations": self._annotation_summary_records(),
            "active_selection_count": len(self.active_selection.atom_indices),
            "system_loaded": self._molsys is not None,
        })

    def _sync_measurement_summaries_runtime(self) -> None:
        settings = self.measurements.settings(skip_digestion=True)
        self._send_runtime_only({
            "op": "set_measurement_summaries",
            "measurements": self._measurement_summary_records(),
            "endpoint_policy_default": settings["endpoint_policy_default"],
            "representative_atoms": settings["representative_atoms"],
            "active_selection_count": len(self.active_selection.group_indices),
            "structure_index": int(self._current_structure_index),
            "system_loaded": self._molsys is not None,
        })

    def _sync_shape_summaries_runtime(self) -> None:
        self._send_runtime_only({
            "op": "set_shape_summaries",
            "shapes": self._shape_summary_records(),
        })

    def _sync_layer_summaries_runtime(self) -> None:
        self._send_runtime_only({
            "op": "set_layer_summaries",
            "layers": self._layer_summary_records(),
        })

    def _sync_scene_object_summaries_for_message(self, msg: dict) -> None:
        op = msg.get("op")
        kind = msg.get("kind")
        if op in {"clear_all", "clear_scene"} or kind == "layer":
            self._sync_annotation_summaries_runtime()
            self._sync_measurement_summaries_runtime()
            self._sync_shape_summaries_runtime()
            self._sync_layer_summaries_runtime()
            return
        if kind == "annotation" or op in self._ANNOTATION_SUMMARY_OPS:
            self._sync_annotation_summaries_runtime()
        elif kind == "measurement" or op in self._MEASUREMENT_SUMMARY_OPS:
            self._sync_measurement_summaries_runtime()
        elif kind == "shape" or op in self._SHAPE_SUMMARY_OPS:
            self._sync_shape_summaries_runtime()

    @staticmethod
    def _scene_object_key(kind: str, tag: str) -> tuple[str, str]:
        return str(kind), str(tag)

    def _get_scene_object(self, kind: str, tag: str) -> SceneObject | None:
        return self._scene_objects.get(self._scene_object_key(kind, tag))

    def _scene_objects_of_kind(self, kind: str):
        for (object_kind, tag), obj in self._scene_objects.items():
            if object_kind == kind:
                yield tag, obj

    def _unregister_layer(self, tag: str) -> None:
        self._layers.pop(tag, None)
        self._sync_layer_summaries_runtime()

    def _reregister_layer(self, old_tag: str, new_tag: str, layer: Layer) -> None:
        if old_tag in self._layers:
            self._layers.pop(old_tag, None)
        self._layers[new_tag] = layer

    def _unregister_scene_object(self, kind: str, tag: str) -> None:
        status = getattr(self, "_shape_render_status", None)
        if isinstance(status, dict):
            status.pop(tag, None)
        obj = self._scene_objects.pop(self._scene_object_key(kind, tag), None)
        if obj is None:
            return
        layer_tag = getattr(obj, "layer_tag", None)
        if isinstance(layer_tag, str):
            layer = self._layers.get(layer_tag)
            if isinstance(layer, Layer) and len(layer.members) == 0 and layer.provenance == "auto":
                self._layers.pop(layer_tag, None)
        self._sync_scene_object_summaries_for_message({"op": "delete_layer", "kind": kind})

    def _reregister_scene_object(self, old_tag: str, new_tag: str, obj: SceneObject) -> None:
        self._scene_objects.pop(self._scene_object_key(obj.kind, old_tag), None)
        self._scene_objects[self._scene_object_key(obj.kind, new_tag)] = obj
        self._sync_scene_object_summaries_for_message({"op": "set_layer_tag", "kind": obj.kind})

    def _sync_layer_group_hidden_state(self, layer_tag: str) -> None:
        layer = self._layers.get(layer_tag)
        if layer is None:
            return
        members = getattr(layer, "members", {})
        if len(members) == 0:
            layer._hidden = False  # noqa: SLF001
            self._sync_layer_summaries_runtime()
            return
        layer._hidden = all(getattr(item, "_hidden", False) for item in members.values())  # noqa: SLF001
        self._sync_layer_summaries_runtime()

    def _update_scene_object_history_layer_tag(self, kind: str, tag: str, layer_tag: str) -> None:
        def rewrite(history: list[dict]) -> list[dict]:
            rewritten: list[dict] = []
            for item in history:
                if self._tag_from_message(item) != tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                else:
                    options = {}
                options["layer_tag"] = layer_tag
                updated["options"] = options
                rewritten.append(updated)
            return rewritten

        if kind == "shape":
            self._shape_history = rewrite(self._shape_history)
        elif kind == "annotation":
            self._annotation_history = rewrite(self._annotation_history)
        elif kind == "measurement":
            self._measurement_history = rewrite(self._measurement_history)

    def _set_scene_object_layer_tag(self, obj: SceneObject, new_layer_tag: str) -> None:
        text = str(new_layer_tag).strip()
        if text == "":
            raise ValueError("Layer tag must be a non-empty string.")
        old_layer_tag = getattr(obj, "layer_tag", None)
        if old_layer_tag == text:
            return
        provenance = "auto" if text == getattr(obj, "tag", None) else "user"
        self._ensure_layer_group(text, kind=getattr(obj, "kind", None), provenance=provenance)
        obj.layer_tag = text
        self._update_scene_object_history_layer_tag(obj.kind, obj.tag, text)
        if isinstance(old_layer_tag, str):
            old_layer = self._layers.get(old_layer_tag)
            if isinstance(old_layer, Layer) and len(old_layer.members) == 0 and old_layer.provenance == "auto":
                self._layers.pop(old_layer_tag, None)
            else:
                self._sync_layer_group_hidden_state(old_layer_tag)
        self._sync_layer_group_hidden_state(text)
        self._sync_scene_object_summaries_for_message({"op": "set_layer_tag", "kind": obj.kind})

    def _cleanup_empty_layer_group(self, layer_tag: str) -> None:
        """Drop a grouping layer left empty (e.g. after a region moved out or
        was deleted), otherwise refresh its aggregate hidden state."""
        layer = self._layers.get(layer_tag)
        if isinstance(layer, Layer) and len(layer.members) == 0 and layer.provenance == "auto":
            self._layers.pop(layer_tag, None)
        else:
            self._sync_layer_group_hidden_state(layer_tag)

    def _ensure_layer_group(
        self,
        layer_tag: str,
        *,
        kind: str | None = None,
        provenance: str = "auto",
    ) -> Layer:
        text = str(layer_tag).strip()
        if text == "":
            raise ValueError("Layer tag must be a non-empty string.")
        layer = self._layers.get(text)
        if layer is None:
            layer = Layer(self, text, kind=kind or "layer", meta={}, provenance=provenance)
            self._layers[text] = layer
            self._sync_layer_summaries_runtime()
        else:
            if kind is not None:
                layer.kind = kind
            if provenance == "user":
                layer._promote_to_user()  # noqa: SLF001
                self._sync_layer_summaries_runtime()
        return layer

    def _move_or_rename_layer_group_for_object_tag_change(self, old_tag: str, new_tag: str, obj: SceneObject) -> None:
        old_layer = self._layers.get(old_tag)
        if isinstance(old_layer, Layer) and len(old_layer.members) == 1 and (obj.kind, obj.tag) in old_layer.members:
            self._layers.pop(old_tag, None)
            old_layer.tag = new_tag
            self._layers[new_tag] = old_layer
            return
        self._ensure_layer_group(new_tag, provenance="user")

    def _assert_nonstructural_tag_available(self, tag: str, *, current_tag: str | None = None) -> str:
        text = str(tag).strip()
        if text == "":
            raise ValueError("Tag must be a non-empty string.")
        if current_tag is not None and text == current_tag:
            return text
        if text in self._layers:
            raise ValueError(f"Non-structural tag {text!r} already exists.")
        return text

    def _assert_scene_object_tag_available(self, tag: str, *, current_tag: str | None = None) -> str:
        text = str(tag).strip()
        if text == "":
            raise ValueError("Tag must be a non-empty string.")
        if current_tag is not None and text == current_tag:
            return text
        return text

__all__ = ["SceneRegistryMixin"]
