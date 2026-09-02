from __future__ import annotations

import math
import warnings
from typing import Any, Dict, Optional

from smonitor import signal

from ._private.argdigest import digest
from .viewer.utils import quantity_value_in_unit
from . import pyunitwizard as puw
from .scene_history import records_scene_history


_NM_TO_ANGSTROM = puw.conversion_factor("nm", "angstroms")


def _extract_shape_points_nm(options: dict, op: str) -> list[list[float]]:
    """Return a flat list of 3D points (in nm) extracted from any shape message."""
    def _flat(seq):
        out = []
        for item in seq or []:
            if isinstance(item, (list, tuple)) and len(item) == 3:
                try:
                    out.append([float(item[0]), float(item[1]), float(item[2])])
                except (TypeError, ValueError):
                    pass
        return out

    if op == "add_sphere":
        c = options.get("center")
        if isinstance(c, (list, tuple)) and len(c) == 3:
            return [[float(c[0]), float(c[1]), float(c[2])]]
        return []

    if op in ("add_pocket_blob", "add_pocket_surface", "add_channel_tube",
              "add_pharmacophore_features", "add_anisotropy_ellipsoids",
              "add_displacement_vectors"):
        # alpha spheres: two sub-arrays (alpha_spheres and atom_spheres)
        if op == "add_pocket_blob":
            pts = []
            alpha = options.get("alpha_spheres") or {}
            pts += _flat(alpha.get("centers"))
            atom = options.get("atom_spheres") or {}
            pts += _flat(atom.get("centers"))
            return pts if pts else _flat(options.get("centers"))
        return _flat(options.get("centers"))

    if op == "add_alpha_sphere_set":
        pts = []
        alpha = options.get("alpha_spheres") or {}
        pts += _flat(alpha.get("centers"))
        atom = options.get("atom_spheres") or {}
        pts += _flat(atom.get("centers"))
        return pts

    if op == "add_network_links":
        pts = []
        for pair in options.get("coordinate_pairs") or []:
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                for endpoint in pair[:2]:
                    if isinstance(endpoint, (list, tuple)) and len(endpoint) == 3:
                        try:
                            pts.append([float(endpoint[0]), float(endpoint[1]), float(endpoint[2])])
                        except (TypeError, ValueError):
                            pass
        # fall back to atom-pair midpoints — no coordinate data available without atoms
        return pts

    if op == "add_tetrahedra":
        pts = []
        for quad in options.get("tetra_coords") or options.get("tetraCoords") or []:
            # quad is a list of 4 vertices, each [x,y,z]
            for v in quad:
                if isinstance(v, (list, tuple)) and len(v) == 3:
                    try:
                        pts.append([float(v[0]), float(v[1]), float(v[2])])
                    except (TypeError, ValueError):
                        pass
        return pts

    if op == "add_triangle_faces":
        pts = []
        for tri in options.get("vertices") or []:
            for v in tri:
                if isinstance(v, (list, tuple)) and len(v) == 3:
                    try:
                        pts.append([float(v[0]), float(v[1]), float(v[2])])
                    except (TypeError, ValueError):
                        pass
        return pts

    return []


def _bounding_sphere_nm(points: list[list[float]]) -> tuple[list[float], float]:
    """Return (centroid, radius) in nm for a list of 3D points."""
    n = len(points)
    if n == 0:
        return [0.0, 0.0, 0.0], 4.0
    cx = sum(p[0] for p in points) / n
    cy = sum(p[1] for p in points) / n
    cz = sum(p[2] for p in points) / n
    radius = max(
        math.sqrt((p[0] - cx) ** 2 + (p[1] - cy) ** 2 + (p[2] - cz) ** 2)
        for p in points
    )
    return [cx, cy, cz], max(radius, 0.1)  # at least 0.1 nm


class LayerHandle:
    """Base wrapper for non-structural scene handles addressed by tag."""

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
        current_owner = getattr(view, "_current_scene_owner", None)
        self._owner = current_owner() if callable(current_owner) else None
        self._active = True
        self._hidden = False
        self.broken = False
        self.broken_reason: str | None = None

    @property
    def owner(self) -> str | None:
        """Creator attribution captured when this object was created."""
        return self._owner

    @property
    def shapes(self) -> Dict[str, "Shape"]:
        return {
            item.tag: item
            for item in getattr(self._view, "_scene_objects", {}).values()  # noqa: SLF001
            if isinstance(item, Shape) and getattr(item, "layer_tag", None) == self.tag
        }

    @property
    def annotations(self) -> Dict[str, "Annotation"]:
        return {
            item.tag: item
            for item in getattr(self._view, "_scene_objects", {}).values()  # noqa: SLF001
            if isinstance(item, Annotation) and getattr(item, "layer_tag", None) == self.tag
        }

    @property
    def measurements(self) -> Dict[str, "Measurement"]:
        return {
            item.tag: item
            for item in getattr(self._view, "_scene_objects", {}).values()  # noqa: SLF001
            if isinstance(item, Measurement) and getattr(item, "layer_tag", None) == self.tag
        }

    @property
    def regions(self) -> Dict[str, Any]:
        """Regions that belong to this layer (Contract B3, Phase 9)."""
        return {
            item.tag: item
            for item in getattr(self._view, "_regions", {}).values()  # noqa: SLF001
            if getattr(item, "layer", None) == self.tag and getattr(item, "_active", False)
        }

    @property
    def members(self) -> Dict[tuple[str, str], Any]:
        members: Dict[tuple[str, str], Any] = {}
        for kind, values in (
            ("shape", self.shapes),
            ("annotation", self.annotations),
            ("measurement", self.measurements),
            ("region", self.regions),
        ):
            members.update({(kind, tag): obj for tag, obj in values.items()})
        return members

    def _send(self, op: str, **payload: Any) -> None:
        if not self._active:
            return
        msg = {"op": op, "tag": self.tag, **payload}
        if op in {"show_layer", "hide_layer", "delete_layer", "set_layer_tag"}:
            msg.setdefault("kind", "layer")
        self._view._send(msg)  # noqa: SLF001

    def _send_create(self) -> None:
        self._send("create_layer", kind=self.kind, meta=self.meta)

    @records_scene_history
    @signal(tags=["visibility", "layer"])
    @digest()
    def show(self, skip_digestion: bool = False) -> None:
        """Show this layer (all contained visuals)."""
        self._hidden = False
        self._send("show_layer")

    @records_scene_history
    @signal(tags=["visibility", "layer"])
    @digest()
    def hide(self, skip_digestion: bool = False) -> None:
        """Hide this layer (all contained visuals)."""
        self._hidden = True
        self._send("hide_layer")

    @records_scene_history
    @signal(
        tags=["layer"],
        extra_factory=lambda args, kwargs: {"new_tag": kwargs.get("new_tag", args[1] if len(args) > 1 else None)},
    )
    @digest()
    def delete(self, skip_digestion: bool = False) -> None:
        """Remove this layer and its visuals."""
        if not self._active:
            return
        self._view._send({"op": "delete_layer", "tag": self.tag, "kind": "layer"})  # noqa: SLF001
        self._active = False
        self._view._unregister_layer(self.tag)  # noqa: SLF001

    @records_scene_history
    @signal(tags=["layer"])
    @digest()
    def set_tag(self, new_tag: str, skip_digestion: bool = False) -> None:
        """Change this layer's tag (and update the registry)."""
        if not self._active or new_tag == self.tag:
            return
        if hasattr(self._view, "_assert_nonstructural_tag_available"):
            new_tag = self._view._assert_nonstructural_tag_available(new_tag, current_tag=self.tag)  # noqa: SLF001
        old_tag = self.tag
        self._view._send({"op": "set_layer_tag", "tag": old_tag, "new_tag": new_tag, "kind": "layer"})  # noqa: SLF001
        self.tag = new_tag
        self._view._reregister_layer(old_tag, new_tag, self)  # noqa: SLF001


class SceneObject(LayerHandle):
    """First-slice retrievable non-structural object.

    For now it still shares the same operational tag used by the current
    frontend bridge, but it also carries an explicit `layer_tag` field so the
    public model can evolve toward distinct object identity vs grouping.
    """

    def __init__(
        self,
        view: Any,
        tag: str,
        *,
        kind: str,
        layer_tag: str | None = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(view, tag, kind=kind, meta=meta)
        self.layer_tag = layer_tag or tag

    def _sync_group_layer_hidden_state(self) -> None:
        if hasattr(self._view, "_sync_layer_group_hidden_state"):
            self._view._sync_layer_group_hidden_state(self.layer_tag)  # noqa: SLF001

    def _send(self, op: str, **payload: Any) -> None:
        if op in {"show_layer", "hide_layer", "delete_layer", "set_layer_tag"}:
            payload["kind"] = self.kind
        super()._send(op, **payload)

    @records_scene_history
    def show(self, skip_digestion: bool = False) -> None:
        super().show(skip_digestion=True)
        self._sync_group_layer_hidden_state()

    @records_scene_history
    def hide(self, skip_digestion: bool = False) -> None:
        super().hide(skip_digestion=True)
        self._sync_group_layer_hidden_state()

    @records_scene_history
    def set_tag(self, new_tag: str, skip_digestion: bool = False) -> None:
        if not self._active or new_tag == self.tag:
            return
        if hasattr(self._view, "_assert_scene_object_tag_available"):
            new_tag = self._view._assert_scene_object_tag_available(new_tag, current_tag=self.tag)  # noqa: SLF001
        old_tag = self.tag
        old_layer_tag = self.layer_tag
        self._view._send({"op": "set_layer_tag", "tag": old_tag, "new_tag": new_tag, "kind": self.kind})  # noqa: SLF001
        self.tag = new_tag
        self._view._reregister_scene_object(old_tag, new_tag, self)  # noqa: SLF001
        if old_layer_tag == old_tag:
            if hasattr(self._view, "_move_or_rename_layer_group_for_object_tag_change"):
                self._view._move_or_rename_layer_group_for_object_tag_change(old_tag, new_tag, self)  # noqa: SLF001
            self.layer_tag = new_tag

    @records_scene_history
    def set_layer_tag(self, new_layer_tag: str, skip_digestion: bool = False) -> None:
        if not self._active:
            return
        if hasattr(self._view, "_set_scene_object_layer_tag"):
            self._view._set_scene_object_layer_tag(self, new_layer_tag)  # noqa: SLF001

    @records_scene_history
    def delete(self, skip_digestion: bool = False) -> None:
        if not self._active:
            return
        self._view._send({"op": "delete_layer", "tag": self.tag, "kind": self.kind})  # noqa: SLF001
        self._active = False
        if hasattr(self._view, "_unregister_scene_object"):
            self._view._unregister_scene_object(self.kind, self.tag)  # noqa: SLF001
        self._sync_group_layer_hidden_state()


class Layer(LayerHandle):
    """Pure Python grouping layer for scene objects."""

    def __init__(
        self,
        view: Any,
        tag: str,
        *,
        kind: str | None = None,
        meta: Optional[Dict[str, Any]] = None,
        provenance: str = "auto",
    ) -> None:
        super().__init__(view, tag, kind=kind, meta=meta)
        if provenance not in {"auto", "user"}:
            raise ValueError("Layer provenance must be 'auto' or 'user'.")
        self.provenance = provenance

    def _promote_to_user(self) -> None:
        self.provenance = "user"

    def _send_create(self) -> None:
        self._sync_summary_runtime()

    def _sync_summary_runtime(self) -> None:
        sync = getattr(self._view, "_sync_layer_summaries_runtime", None)
        if callable(sync):
            sync()

    @records_scene_history
    def set_tag(self, new_tag: str, skip_digestion: bool = False) -> None:
        members = list(self.members.values())
        if len(members) == 1:
            member = members[0]
            if getattr(member, "tag", None) == self.tag and getattr(member, "layer_tag", None) == self.tag:
                member.set_tag(new_tag, skip_digestion=True)
                return
        super().set_tag(new_tag, skip_digestion=True)
        for member in members:
            if hasattr(member, "layer_tag"):
                member.layer_tag = self.tag
            else:
                # A region tracks membership by the layer tag string; keep it in
                # step with the rename so it is not orphaned.
                member._layer = self.tag  # noqa: SLF001
        region_sync = getattr(self._view, "_sync_region_summaries_runtime", None)
        if callable(region_sync):
            region_sync()
        scene_sync = getattr(self._view, "_sync_scene_object_summaries_for_message", None)
        if callable(scene_sync):
            # Renaming changes both membership channels. Republish every domain
            # so the Layers panel's join cannot retain the old tag.
            scene_sync({"op": "set_layer_tag", "kind": "layer"})
        else:
            self._sync_summary_runtime()

    @staticmethod
    def _member_has_nothing_to_render(member: Any) -> bool:
        # A region without its own representation (Contract A) has nothing to
        # show or hide; toggling it directly would warn, so a bulk layer op
        # tracks its state quietly instead.
        has_own_visual = getattr(member, "_has_own_visual", None)
        return callable(has_own_visual) and not has_own_visual()

    @records_scene_history
    def show(self, skip_digestion: bool = False) -> None:
        self._hidden = False
        for member in list(self.members.values()):
            if self._member_has_nothing_to_render(member):
                member._hidden = False  # noqa: SLF001
                continue
            member.show(skip_digestion=True)
        self._sync_summary_runtime()

    @records_scene_history
    def hide(self, skip_digestion: bool = False) -> None:
        self._hidden = True
        for member in list(self.members.values()):
            if self._member_has_nothing_to_render(member):
                member._hidden = True  # noqa: SLF001
                continue
            member.hide(skip_digestion=True)
        self._sync_summary_runtime()

    @records_scene_history
    def delete(self, skip_digestion: bool = False) -> None:
        if not self._active:
            return
        for member in list(self.members.values()):
            member.delete(skip_digestion=True)
        self._active = False
        if hasattr(self._view, "_unregister_layer"):
            self._view._unregister_layer(self.tag)  # noqa: SLF001

    @records_scene_history
    def ungroup(self, skip_digestion: bool = False) -> None:
        """Dissolve this user group without deleting any member."""
        if not self._active:
            return
        for member in list(self.members.values()):
            if hasattr(member, "layer_tag"):
                if member.tag != self.tag:
                    member.set_layer_tag(member.tag, skip_digestion=True)
            else:
                member.remove_from_layer(skip_digestion=True)

        # A same-tag scene object cannot move to a differently named degenerate
        # layer. Keep its backing layer, but demote it so the UI no longer treats
        # it as a user-created group.
        if self.members:
            self.provenance = "auto"
            self._hidden = all(getattr(member, "_hidden", False) for member in self.members.values())
            self._sync_summary_runtime()
            return
        self._active = False
        self._view._unregister_layer(self.tag)  # noqa: SLF001

    @records_scene_history
    def attach(self, obj: "SceneObject") -> None:
        """Move *obj* into this layer (top-down membership management).

        Equivalent to ``obj.set_layer_tag(self.tag)`` but expressed from the
        layer's point of view.  If *obj* was the sole member of its previous
        layer and that layer shared the same tag as the object, the old layer
        is automatically cleaned up.

        Parameters
        ----------
        obj
            A :class:`Shape`, :class:`Annotation`, or :class:`Measurement`
            instance to bring into this layer.
        """
        if not isinstance(obj, SceneObject):
            raise TypeError(f"Expected a SceneObject (Shape/Annotation/Measurement), got {type(obj).__name__!r}.")
        if not self._active:
            raise ValueError(f"Layer {self.tag!r} is no longer active.")
        obj.set_layer_tag(self.tag)

    def info(self) -> list[dict]:
        """Return a summary of all objects in this layer."""
        rows = []
        for (_kind, tag), obj in self.members.items():
            kind = getattr(obj, "kind", "unknown")
            rows.append({
                "kind": kind,
                "tag": tag,
                "visible": not getattr(obj, "_hidden", False),
                "type": getattr(obj, "shape_type", getattr(obj, "meta", {}).get("kind", kind)),
            })
        return rows

    @records_scene_history
    def detach(self, obj: "SceneObject") -> None:
        """Detach *obj* from this layer, making it its own independent layer.

        Equivalent to ``obj.set_layer_tag(obj.tag)``.  A new layer group is
        automatically created for the object, and this layer is cleaned up if
        it becomes empty as a result.

        Parameters
        ----------
        obj
            A :class:`Shape`, :class:`Annotation`, or :class:`Measurement`
            that is currently a member of this layer.
        """
        if not isinstance(obj, SceneObject):
            raise TypeError(f"Expected a SceneObject (Shape/Annotation/Measurement), got {type(obj).__name__!r}.")
        if getattr(obj, "layer_tag", None) != self.tag:
            raise ValueError(f"Object {obj.tag!r} is not a member of layer {self.tag!r}.")
        obj.set_layer_tag(obj.tag)


class LayersManager(dict[str, Layer]):
    """Live registry and public manager for scene grouping layers."""

    def __init__(self, view: Any) -> None:
        super().__init__()
        self._view = view

    @records_scene_history
    @signal(tags=["layer"])
    @digest()
    def add(
        self,
        tag: str,
        *,
        kind: str | None = None,
        meta: dict[str, Any] | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        normalized = self._view._tag_managers["layer"].validate(tag)  # noqa: SLF001
        layer = Layer(
            self._view,
            normalized,
            kind=kind,
            meta=dict(meta or {}),
            provenance="user",
        )
        self[normalized] = layer
        layer._send_create()  # noqa: SLF001
        return layer

    @signal(tags=["layer", "query"])
    @digest()
    def tags(self, skip_digestion: bool = False) -> list[str]:
        return list(self.keys())

    @signal(tags=["layer", "query"])
    @digest()
    def count(self, skip_digestion: bool = False) -> int:
        return len(self)

    @signal(tags=["layer", "query"])
    @digest()
    def contains(self, tag: str, skip_digestion: bool = False) -> bool:
        return tag in self

    @signal(tags=["layer", "query"])
    @digest()
    def get(self, tag: str, default=None, skip_digestion: bool = False):
        return super().get(tag, default)

    @signal(tags=["layer", "query"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        result = self.info(skip_digestion=True)
        return result if isinstance(result, list) else [result]

    @signal(tags=["layer", "query"])
    @digest()
    def info(self, tag: str | None = None, skip_digestion: bool = False):
        def summarize(layer: Layer) -> dict[str, Any]:
            return {
                "tag": layer.tag,
                "owner": layer.owner,
                "meta": dict(layer.meta),
                "provenance": layer.provenance,
                "visible": not layer._hidden,  # noqa: SLF001
                "n_members": len(layer.members),
            }

        if tag is not None:
            layer = super().get(tag)
            if layer is None:
                raise ValueError(f"No layer found for tag {tag!r}.")
            return summarize(layer)
        return [summarize(layer) for layer in self.values()]

    @records_scene_history
    @signal(tags=["layer"])
    @digest()
    def delete(self, tag: str, skip_digestion: bool = False) -> None:
        layer = super().get(tag)
        if layer is None:
            raise KeyError(tag)
        layer.delete(skip_digestion=True)

    @records_scene_history
    @signal(tags=["layer"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False) -> None:
        if tag is not None:
            self.delete(tag, skip_digestion=True)
            return
        for layer_tag in list(self.keys()):
            self.delete(layer_tag, skip_digestion=True)

    @records_scene_history
    @signal(tags=["layer"])
    @digest()
    def set_tag(self, tag: str, new_tag: str, skip_digestion: bool = False) -> Layer:
        layer = super().get(tag)
        if layer is None:
            raise KeyError(tag)
        layer.set_tag(new_tag, skip_digestion=True)
        return layer

    @records_scene_history
    @signal(tags=["visibility", "layer"])
    @digest()
    def show(self, tag: str, skip_digestion: bool = False) -> Layer:
        layer = super().get(tag)
        if layer is None:
            raise KeyError(tag)
        layer.show(skip_digestion=True)
        return layer

    @records_scene_history
    @signal(tags=["visibility", "layer"])
    @digest()
    def hide(self, tag: str, skip_digestion: bool = False) -> Layer:
        layer = super().get(tag)
        if layer is None:
            raise KeyError(tag)
        layer.hide(skip_digestion=True)
        return layer


class Shape(SceneObject):
    def __init__(self, view: Any, tag: str, *, layer_tag: str | None = None, meta: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(view, tag, kind="shape", layer_tag=layer_tag, meta=meta)

    def _sync_summary_runtime(self) -> None:
        sync = getattr(self._view, "_sync_shape_summaries_runtime", None)
        if callable(sync):
            sync()

    def _replace_shape_and_refresh_runtime(self, next_msg: dict, *, runtime_msg: dict | None = None) -> None:
        if hasattr(self._view, "_replace_shape_message"):
            self._view._replace_shape_message(self.tag, next_msg)  # noqa: SLF001
        if hasattr(self._view, "_send_runtime_only"):
            self._view._send_runtime_only({"op": "delete_layer", "tag": self.tag, "kind": self.kind})  # noqa: SLF001
            payload = dict(runtime_msg or next_msg)
            options = payload.get("options")
            if isinstance(options, dict):
                options = dict(options)
            else:
                options = {}
            options["tag"] = self.tag
            options["layer_tag"] = self.layer_tag
            payload["options"] = options
            self._view._send_runtime_only(payload)  # noqa: SLF001
            if getattr(self, "_hidden", False):
                self._view._send_runtime_only({"op": "hide_layer", "tag": self.tag, "kind": self.kind})  # noqa: SLF001
        self._sync_summary_runtime()

    def _require_shape_message(self) -> dict:
        getter = getattr(self._view, "_get_shape_message", None)
        if not callable(getter):
            raise ValueError("Shape mutation requires a viewer with shape history support.")
        msg = getter(self.tag)
        if not isinstance(msg, dict):
            raise ValueError(f"No replayable shape message found for tag {self.tag!r}.")
        return msg

    def _apply_sphere_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_sphere":
            raise NotImplementedError("Rich shape mutators are currently implemented only for spheres.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        next_msg = {"op": "add_sphere", "options": next_options}
        if hasattr(self._view, "_replace_shape_message"):
            self._view._replace_shape_message(self.tag, next_msg)  # noqa: SLF001
        if hasattr(self._view, "_send_runtime_only"):
            self._view._send_runtime_only({"op": "update_sphere", "tag": self.tag, "options": next_options})  # noqa: SLF001
            if getattr(self, "_hidden", False):
                self._view._send_runtime_only({"op": "hide_layer", "tag": self.tag, "kind": self.kind})  # noqa: SLF001
        self._sync_summary_runtime()

    @staticmethod
    def _normalize_to_count(values, count: int, cast) -> list[Any]:
        if count <= 0:
            raise ValueError("Shape update requires at least one geometric element.")
        if isinstance(values, (str, bytes)):
            return [cast(values)] * count
        try:
            seq = list(values)
        except TypeError:
            return [cast(values)] * count
        if len(seq) not in (1, count):
            raise ValueError(f"Expected 1 or {count} values, got {len(seq)}")
        if len(seq) == 1:
            return [cast(seq[0])] * count
        return [cast(v) for v in seq]

    def _shape_element_count(self, options: dict, *keys: str) -> int:
        for key in keys:
            values = options.get(key)
            if isinstance(values, list):
                return len(values)
        raise ValueError(f"Shape {self.tag!r} does not expose the requested editable payload.")

    def _apply_links_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_network_links":
            raise NotImplementedError("This mutator is currently implemented only for link shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_network_links", "options": next_options})

    def _apply_triangle_faces_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_triangle_faces":
            raise NotImplementedError("This mutator is currently implemented only for triangle-face shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_triangle_faces", "options": next_options})

    def _apply_channel_tube_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_channel_tube":
            raise NotImplementedError("This mutator is currently implemented only for channel-tube shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_channel_tube", "options": next_options})

    def _apply_tetrahedra_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_tetrahedra":
            raise NotImplementedError("This mutator is currently implemented only for tetrahedra shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_tetrahedra", "options": next_options})

    def _apply_anisotropy_ellipsoid_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_anisotropy_ellipsoids":
            raise NotImplementedError("This mutator is currently implemented only for anisotropy-ellipsoid shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_anisotropy_ellipsoids", "options": next_options})

    def _apply_pharmacophore_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_pharmacophore_features":
            raise NotImplementedError("This mutator is currently implemented only for pharmacophore shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_pharmacophore_features", "options": next_options})

    def _apply_displacement_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_displacement_vectors":
            raise NotImplementedError("This mutator is currently implemented only for displacement-vector shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_displacement_vectors", "options": next_options})

    def _apply_pocket_blob_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_pocket_blob":
            raise NotImplementedError("This mutator is currently implemented only for pocket-blob shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_pocket_blob", "options": next_options})

    def _apply_pocket_surface_update(self, **updates: Any) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != "add_pocket_surface":
            raise NotImplementedError("This mutator is currently implemented only for pocket-surface shapes.")
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        next_options.update(updates)
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": "add_pocket_surface", "options": next_options})

    def _apply_pocket_centers_update(self, op: str, centers) -> None:
        msg = self._require_shape_message()
        if msg.get("op") != op:
            raise NotImplementedError(
                f"_apply_pocket_centers_update called with op {op!r} but shape has op {msg.get('op')!r}."
            )
        options = msg.get("options")
        if not isinstance(options, dict):
            options = {}
        next_options = dict(options)
        alpha = dict(next_options.get("alpha_spheres") or {})
        alpha["centers"] = centers
        next_options["alpha_spheres"] = alpha
        next_options["tag"] = self.tag
        next_options["layer_tag"] = self.layer_tag
        self._replace_shape_and_refresh_runtime({"op": op, "options": next_options})

    def get_center(self):
        msg = self._require_shape_message()
        options = msg.get("options")
        center = options.get("center") if isinstance(options, dict) else None
        if not isinstance(center, list) or len(center) != 3:
            raise ValueError(f"Shape {self.tag!r} does not expose a geometric center.")
        return puw.standardize(puw.quantity(list(center), "angstroms"))

    def get_coordinates(self):
        """Return the geometric coordinates in the configured standard length unit.

        The return value depends on the shape type:

        - **sphere** — center as a ``(3,)`` array.
        - **channel tube / pharmacophore / anisotropy ellipsoids /
          displacement vectors** — center path as a ``(n, 3)`` array.
        - **network links** — coordinate pairs as a ``(n, 2, 3)`` array.
        - **triangle faces** — vertex triples as a ``(n, 3, 3)`` array.
        - **tetrahedra** — vertex quads as a ``(n, 4, 3)`` array.
        - **pocket blob / pocket surface / alpha sphere set** — alpha-sphere
          centers as a ``(n, 3)`` array.
        """
        msg = self._require_shape_message()
        op = msg.get("op", "")
        options = msg.get("options") if isinstance(msg.get("options"), dict) else {}

        if op == "add_sphere":
            center = options.get("center")
            if not isinstance(center, list) or len(center) != 3:
                raise ValueError(f"Shape {self.tag!r} has no geometric center.")
            return puw.standardize(puw.quantity(center, "angstroms"))

        if op in ("add_channel_tube", "add_pharmacophore_features",
                  "add_displacement_vectors", "add_anisotropy_ellipsoids"):
            centers = options.get("centers")
            if not isinstance(centers, list) or len(centers) == 0:
                raise ValueError(f"Shape {self.tag!r} has no centers data.")
            return puw.standardize(puw.quantity(centers, "angstroms"))

        if op == "add_network_links":
            pairs = options.get("coordinate_pairs")
            if isinstance(pairs, list) and len(pairs) > 0:
                return puw.standardize(puw.quantity(pairs, "angstroms"))
            raise ValueError(
                f"Shape {self.tag!r} is a link shape with atom-pair-only data; "
                "no explicit coordinates are stored."
            )

        if op in ("add_pocket_blob", "add_pocket_surface", "add_alpha_sphere_set"):
            alpha = options.get("alpha_spheres") or {}
            centers = alpha.get("centers")
            if isinstance(centers, list) and len(centers) > 0:
                return puw.standardize(puw.quantity(centers, "angstroms"))
            raise ValueError(f"Shape {self.tag!r} has no alpha-sphere centers.")

        if op == "add_triangle_faces":
            vertices = options.get("vertices")
            if not isinstance(vertices, list) or len(vertices) == 0:
                raise ValueError(f"Shape {self.tag!r} has no vertex data.")
            return puw.standardize(puw.quantity(vertices, "angstroms"))

        if op == "add_tetrahedra":
            coords = options.get("tetra_coords") or options.get("tetraCoords")
            if not isinstance(coords, list) or len(coords) == 0:
                raise ValueError(f"Shape {self.tag!r} has no tetrahedra coordinate data.")
            return puw.standardize(puw.quantity(coords, "angstroms"))

        raise NotImplementedError(
            f"get_coordinates is not implemented for shape op {op!r}."
        )

    @records_scene_history
    def set_coordinates(self, coordinates) -> None:
        """Replace the geometric coordinates of this shape.

        Accepts a ``puw`` quantity or a plain array in angstroms with the same layout
        as returned by :meth:`get_coordinates`.

        Shape-type mapping
        ------------------
        - **sphere** — new center ``(3,)``.
        - **channel tube / pharmacophore / anisotropy ellipsoids /
          displacement vectors** — new centers ``(n, 3)``.
        - **network links** — new coordinate pairs ``(n, 2, 3)``.
        - **triangle faces** — new vertex triples ``(n, 3, 3)``.
        - **tetrahedra** — new vertex quads ``(n, 4, 3)``.
        """
        msg = self._require_shape_message()
        op = msg.get("op", "")

        coords_a = puw.get_value(coordinates, to_unit="angstroms")
        if hasattr(coords_a, "tolist"):
            coords_a = coords_a.tolist()

        if op == "add_sphere":
            self._apply_sphere_update(center=list(coords_a))
            return

        if op == "add_channel_tube":
            self._apply_channel_tube_update(centers=coords_a)
            return

        if op in ("add_pharmacophore_features",):
            self._apply_pharmacophore_update(centers=coords_a)
            return

        if op == "add_displacement_vectors":
            self._apply_displacement_update(centers=coords_a)
            return

        if op == "add_anisotropy_ellipsoids":
            self._apply_anisotropy_ellipsoid_update(centers=coords_a)
            return

        if op == "add_network_links":
            self._apply_links_update(coordinate_pairs=coords_a)
            return

        if op == "add_triangle_faces":
            self._apply_triangle_faces_update(vertices=coords_a)
            return

        if op == "add_tetrahedra":
            self._apply_tetrahedra_update(tetra_coords=coords_a)
            return

        if op in ("add_pocket_blob", "add_pocket_surface", "add_alpha_sphere_set"):
            self._apply_pocket_centers_update(op=op, centers=coords_a)
            return

        raise NotImplementedError(
            f"set_coordinates is not implemented for shape op {op!r}."
        )

    @records_scene_history
    def set_center(self, center, skip_digestion: bool = False) -> None:
        self._apply_sphere_update(center=list(puw.get_value(center, to_unit="angstroms")))

    @records_scene_history
    def set_radius(self, radius, skip_digestion: bool = False) -> None:
        self._apply_sphere_update(radius=float(puw.get_value(radius, to_unit="angstroms")))

    @records_scene_history
    def set_color(self, color, skip_digestion: bool = False) -> None:
        from .colors import normalize_color
        self._apply_sphere_update(color=normalize_color(color))

    @records_scene_history
    def set_alpha(self, alpha: float, skip_digestion: bool = False) -> None:
        msg = self._require_shape_message()
        op = msg.get("op")
        options = msg.get("options") if isinstance(msg.get("options"), dict) else {}
        if op == "add_sphere":
            self._apply_sphere_update(alpha=float(alpha))
            return
        if op == "add_network_links":
            self._apply_links_update(alpha=float(alpha))
            return
        if op == "add_channel_tube":
            self._apply_channel_tube_update(alpha=float(alpha))
            return
        if op == "add_tetrahedra":
            self._apply_tetrahedra_update(alphas=float(alpha))
            return
        if op == "add_anisotropy_ellipsoids":
            self._apply_anisotropy_ellipsoid_update(alpha=float(alpha))
            return
        if op == "add_pharmacophore_features":
            count = self._shape_element_count(options, "centers", "kinds", "radii", "alphas")
            self._apply_pharmacophore_update(alphas=self._normalize_to_count(alpha, count, float))
            return
        if op == "add_pocket_blob":
            self._apply_pocket_blob_update(alpha=float(alpha))
            return
        if op == "add_pocket_surface":
            self._apply_pocket_surface_update(alpha=float(alpha))
            return
        if op == "add_triangle_faces":
            self._apply_triangle_faces_update(alpha=float(alpha))
            return
        raise NotImplementedError(f"set_alpha is not implemented for shape op {op!r}.")

    @records_scene_history
    def set_colors(self, colors, skip_digestion: bool = False) -> None:
        from .colors import normalize_color
        msg = self._require_shape_message()
        op = msg.get("op")
        options = msg.get("options") if isinstance(msg.get("options"), dict) else {}

        def _cast_color(v):
            return normalize_color(v)

        if op == "add_network_links":
            count = self._shape_element_count(options, "atom_pairs", "coordinate_pairs", "colors")
            self._apply_links_update(
                color_by="link",
                color_mode="link",
                colors=self._normalize_to_count(colors, count, _cast_color),
            )
            return
        if op == "add_channel_tube":
            count = self._shape_element_count(options, "centers", "radii", "colors")
            self._apply_channel_tube_update(
                color_by="segment",
                color_mode="segment",
                colors=self._normalize_to_count(colors, count, _cast_color),
            )
            return
        if op == "add_tetrahedra":
            count = self._shape_element_count(options, "tetra_coords", "tetraCoords", "atom_quads", "atomQuads", "colors")
            self._apply_tetrahedra_update(colors=self._normalize_to_count(colors, count, _cast_color))
            return
        if op == "add_anisotropy_ellipsoids":
            count = self._shape_element_count(options, "centers", "atom_indices", "colors")
            self._apply_anisotropy_ellipsoid_update(
                color_by="fixed",
                color_mode="fixed",
                colors=self._normalize_to_count(colors, count, _cast_color),
            )
            return
        if op == "add_pharmacophore_features":
            count = self._shape_element_count(options, "centers", "kinds", "colors")
            self._apply_pharmacophore_update(colors=self._normalize_to_count(colors, count, _cast_color))
            return
        if op == "add_triangle_faces":
            count = self._shape_element_count(options, "vertices", "atom_triplets", "atomTriplets", "colors")
            self._apply_triangle_faces_update(colors=self._normalize_to_count(colors, count, _cast_color))
            return
        raise NotImplementedError(f"set_colors is not implemented for shape op {op!r}.")

    @records_scene_history
    def set_radii(self, radii, skip_digestion: bool = False) -> None:
        msg = self._require_shape_message()
        op = msg.get("op")
        options = msg.get("options") if isinstance(msg.get("options"), dict) else {}
        normalized = None
        if op == "add_network_links":
            count = self._shape_element_count(options, "atom_pairs", "coordinate_pairs", "radii")
            normalized = self._normalize_to_count(
                puw.get_value(radii, to_unit="angstroms"),
                count,
                float,
            )
            self._apply_links_update(radii=normalized)
            return
        if op == "add_channel_tube":
            count = self._shape_element_count(options, "centers", "radii")
            normalized = self._normalize_to_count(
                puw.get_value(radii, to_unit="angstroms"),
                count,
                float,
            )
            self._apply_channel_tube_update(radii=normalized)
            return
        if op == "add_pharmacophore_features":
            count = self._shape_element_count(options, "centers", "kinds", "radii")
            normalized = self._normalize_to_count(
                puw.get_value(radii, to_unit="angstroms"),
                count,
                float,
            )
            self._apply_pharmacophore_update(radii=normalized)
            return
        if op == "add_pocket_blob":
            count = self._shape_element_count(options, "centers", "radii")
            normalized = self._normalize_to_count(
                puw.get_value(radii, to_unit="angstroms"),
                count,
                float,
            )
            self._apply_pocket_blob_update(radii=normalized)
            return
        raise NotImplementedError(f"set_radii is not implemented for shape op {op!r}.")

    @records_scene_history
    def set_radius_scale(self, radius_scale: float, skip_digestion: bool = False) -> None:
        msg = self._require_shape_message()
        op = msg.get("op")
        if op == "add_displacement_vectors":
            self._apply_displacement_update(radius_scale=float(radius_scale))
            return
        if op == "add_pocket_blob":
            self._apply_pocket_blob_update(radius_scale=float(radius_scale))
            return
        raise NotImplementedError(f"set_radius_scale is not implemented for shape op {op!r}.")

    @records_scene_history
    def set_length_scale(self, length_scale: float, skip_digestion: bool = False) -> None:
        msg = self._require_shape_message()
        op = msg.get("op")
        if op != "add_displacement_vectors":
            raise NotImplementedError(f"set_length_scale is not implemented for shape op {op!r}.")
        self._apply_displacement_update(length_scale=float(length_scale))

    def focus(
        self,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "0.5 nanometers",
    ) -> None:
        """Center the camera on this shape.

        Extracts all geometric coordinates from the shape message, computes
        the bounding sphere (centroid + radius), and sends a ``zoom_to_position``
        op to the frontend. Works for all shape types.

        Parameters
        ----------
        duration_ms
            Camera transition duration in milliseconds.
        extra_radius
            Extra padding added to the bounding radius (nm, default 0.5).
        """
        if duration_ms is not None:
            duration = duration_ms
        msg = self._require_shape_message()
        op = msg.get("op", "")
        options = msg.get("options") if isinstance(msg.get("options"), dict) else {}
        points = _extract_shape_points_nm(options, op)
        if not points:
            warnings.warn(
                f"Attempted to focus camera on empty shape {self.tag!r}; focusing on scene center instead.",
                UserWarning,
                stacklevel=2,
            )
        center_nm, radius_nm = _bounding_sphere_nm(points)
        radius_nm = max(radius_nm + quantity_value_in_unit(extra_radius, "nanometers"), 0.5)
        # Convert nm → Å (scene coordinates match atomic coordinates which are in Å)
        center_ang = [v * _NM_TO_ANGSTROM for v in center_nm]
        radius_ang = radius_nm * _NM_TO_ANGSTROM
        self._view._send({  # noqa: SLF001
            "op": "zoom_to_position",
            "center": center_ang,
            "radius": radius_ang,
            "duration_ms": int(quantity_value_in_unit(duration, "milliseconds")),
        })


class Annotation(SceneObject):
    def __init__(self, view: Any, tag: str, *, layer_tag: str | None = None, meta: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(view, tag, kind="annotation", layer_tag=layer_tag, meta=meta)

    def _require_annotation_record(self) -> dict:
        history = getattr(self._view, "_annotation_history", [])
        record = next((r for r in history if r.get("tag") == self.tag), None)
        if record is None:
            raise ValueError(f"No annotation record found for tag {self.tag!r}.")
        return record

    def get_coordinates(self):
        """Return the anchor position in the configured standard length unit.

        The anchor is either the position stored in the annotation record,
        or the centroid of the atom indices evaluated at the current frame.
        """
        import numpy as _np

        record = self._require_annotation_record()
        options = record.get("options") or {}

        position = options.get("position")
        if position is not None:
            if puw.is_quantity(position):
                return puw.standardize(position)
            return puw.standardize(puw.quantity(position, "angstrom"))

        atom_indices = options.get("atom_indices")
        if not isinstance(atom_indices, list) or len(atom_indices) == 0:
            raise ValueError(
                f"Annotation {self.tag!r} has no anchor (no position and no atom_indices)."
            )
        molsys = getattr(self._view, "_molsys", None)
        if molsys is None:
            raise ValueError("No molecular system loaded.")
        frame = getattr(self._view, "_current_structure_index", 0)
        coords = molsys.structures.get_coordinates(
            indices=atom_indices,
            structure_indices=[frame],
            skip_digestion=True,
        )
        # coords shape: (1, n_atoms, 3) in nm — return centroid
        arr = _np.asarray(puw.get_value(coords, to_unit="nm"))
        centroid = arr[0].mean(axis=0).tolist()
        return puw.standardize(puw.quantity(centroid, "nm"))

    def set_coordinates(self, new_pos) -> None:
        """Not supported: annotation anchors are tied to atom indices.

        Use ``view.annotations.set_group_index(tag, group_index)`` to reanchor
        the label to a different atom group.
        """
        raise NotImplementedError(
            f"Annotation {self.tag!r} is atom-anchored. "
            "To move it, use view.annotations.set_group_index(tag, group_index)."
        )


class Measurement(SceneObject):
    def __init__(self, view: Any, tag: str, *, layer_tag: str | None = None, meta: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(view, tag, kind="measurement", layer_tag=layer_tag, meta=meta)

    def get_coordinates(self):
        """Return the 3D positions of the endpoint atoms as a ``puw`` quantity.

        The shape is ``(n_endpoints, 3)`` in the configured standard length unit, where ``n_endpoints`` is 2
        (distance), 3 (angle), or 4 (dihedral).  Positions are resolved from
        the current structure frame.

        Measurements are read-only — endpoints are tied to atoms and cannot be
        moved independently.
        """
        import numpy as _np

        history = getattr(self._view, "_measurement_history", [])
        record = next((r for r in history if r.get("tag") == self.tag), None)
        if record is None:
            raise ValueError(f"No measurement record found for tag {self.tag!r}.")

        options = record.get("options") or {}
        endpoint_indices: list[list[int]] = options.get("endpoint_atom_indices") or []
        flat = [idx for group in endpoint_indices for idx in (group or [])]
        if not flat:
            picks: list[list[int]] = options.get("picks_atom_indices") or []
            flat = [idx for pick in picks for idx in (pick or [])]
        if not flat:
            raise ValueError(f"Measurement {self.tag!r} has no resolvable endpoint atoms.")

        molsys = getattr(self._view, "_molsys", None)
        if molsys is None:
            raise ValueError("No molecular system loaded.")
        frame = getattr(self._view, "_current_structure_index", 0)
        coords = molsys.structures.get_coordinates(
            indices=flat,
            structure_indices=[frame],
            skip_digestion=True,
        )
        # coords shape: (1, n_endpoints, 3) → squeeze to (n_endpoints, 3)
        arr = _np.asarray(puw.get_value(coords, to_unit="nm"))
        return puw.standardize(puw.quantity(arr[0].tolist(), "nm"))

    def focus(
        self,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "0.5 nanometers",
    ) -> None:
        """Center the camera on the atoms involved in this measurement.

        Uses the actual 3D coordinates of the endpoint atoms to compute a tight
        bounding sphere and sends a ``zoom_to_position`` op.  Falls back to
        ``view.zoom()`` if coordinates cannot be retrieved.

        Parameters
        ----------
        duration_ms
            Camera transition duration in milliseconds.
        extra_radius
            Extra padding added to the bounding radius (nm, default 0.5).
        """
        if duration_ms is not None:
            duration = duration_ms
        history = getattr(self._view, "_measurement_history", [])
        record = next((r for r in history if r.get("tag") == self.tag), None)
        if record is None:
            return
        options = record.get("options", {})
        # Prefer resolved endpoint atoms; fall back to raw picks for centroid endpoints.
        endpoint_indices: list[list[int]] = options.get("endpoint_atom_indices") or []
        flat = [idx for group in endpoint_indices for idx in (group or [])]
        if not flat:
            picks: list[list[int]] = options.get("picks_atom_indices") or []
            flat = [idx for pick in picks for idx in (pick or [])]
        if not flat:
            return

        molsys = getattr(self._view, "_molsys", None)
        if molsys is not None:
            try:
                import molsysmt as _msm
                import numpy as _np
                result = _msm.get(
                    molsys,
                    element="atom",
                    selection=flat,
                    output_type="dictionary",
                    coordinates=True,
                    skip_digestion=True,
                )
                coords = result.get("coordinates")
                if coords is not None:
                    # Convert explicitly: `asarray` on a quantity strips the
                    # unit without converting it, so the "in nm" below was an
                    # assumption about the source rather than a guarantee.
                    arr = _np.asarray(puw.get_value(coords, to_unit="nm"))
                    # shape: (n_structures, n_atoms, 3) in nm
                    frame = arr[0]
                    points = [
                        [float(frame[i, 0]), float(frame[i, 1]), float(frame[i, 2])]
                        for i in range(frame.shape[0])
                    ]
                    if points:
                        center_nm, radius_nm = _bounding_sphere_nm(points)
                        radius_nm = max(radius_nm + quantity_value_in_unit(extra_radius, "nanometers"), 0.5)
                        self._view._send({  # noqa: SLF001
                            "op": "zoom_to_position",
                            "center": [v * _NM_TO_ANGSTROM for v in center_nm],
                            "radius": radius_nm * _NM_TO_ANGSTROM,
                            "duration_ms": int(quantity_value_in_unit(duration, "milliseconds")),
                        })
                        return
            except Exception:
                pass
        # Fallback: use the public zoom() path (may zoom out further than ideal)
        self._view.zoom(  # noqa: SLF001
            selection=flat,
            duration_ms=quantity_value_in_unit(duration, "milliseconds"),
            skip_digestion=True,
        )


class Section(SceneObject):
    """A world-space clipping plane applied to all structural representations.

    Access via the objects returned by ``view.scene.add_section()``.

    Coordinates are in nm.  The plane discards everything on the side the
    normal points *towards* when ``invert=False``, or the opposite side when
    ``invert=True``.

    Canvas gizmos
    -------------
    When a section is active the canvas shows two interactive handles:

    * **Centre handle** (cyan circle) — drag to translate the plane along
      its normal.  Left-click and drag in any direction; only the component
      along the normal is applied, so the plane cannot slide off its own axis.

    * **Rim handle** (yellow ↻ square, offset from centre) — drag to rotate
      the normal.  Horizontal drag rotates around the camera's vertical axis;
      vertical drag rotates around the camera's horizontal axis.  Rate: 0.4
      degrees per pixel.

    Both handles use pointer capture so they do not interfere with the
    trackball rotation.  After each drag step the Python attributes
    ``get_point()`` and ``get_normal()`` reflect the current live values.

    Gizmo handles are shown by default.  Use :meth:`disable_drag` /
    :meth:`enable_drag` to hide or re-show them without affecting the plane.
    """

    def __init__(self, view: Any, tag: str, *, meta: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(view, tag, kind="section", layer_tag=None, meta=meta)

    def _require_record(self) -> dict:
        history = getattr(self._view, "_section_history", [])
        record = next((r for r in history if r.get("tag") == self.tag), None)
        if record is None:
            raise ValueError(f"No section record found for tag {self.tag!r}.")
        return record

    def _push_update(self) -> None:
        """Re-send the full section list after an in-place record update."""
        history = getattr(self._view, "_section_history", [])
        self._view._send({"op": "set_sections", "sections": list(history)})  # noqa: SLF001
        sync = getattr(self._view, "_sync_section_summaries_runtime", None)
        if callable(sync):
            sync()

    def get_point(self):
        """Return the plane's anchor point in the configured standard length unit."""
        return puw.standardize(puw.quantity(list(self._require_record()["point"]), "nm"))

    def get_normal(self):
        """Return the plane's normal vector as a plain list ``[nx, ny, nz]``."""
        return list(self._require_record()["normal"])

    def is_inverted(self) -> bool:
        """Return ``True`` if the clipping side is inverted."""
        return bool(self._require_record().get("invert", False))

    @property
    def visible(self) -> bool:
        """Whether this clipping plane currently affects the scene."""
        return not bool(self._require_record().get("hidden", False))

    @records_scene_history
    def set_point(self, point) -> None:
        """Move the plane anchor to *point* (puw quantity or plain ``[x,y,z]`` in nm)."""
        import numpy as _np
        coords_nm = puw.get_value(point, to_unit="nm") if puw.is_quantity(point) else point
        arr = _np.asarray(coords_nm, dtype=float).tolist()
        if len(arr) != 3:
            raise ValueError("point must be a 3-element vector.")
        record = self._require_record()
        record["point"] = arr
        self._push_update()

    @records_scene_history
    def set_normal(self, normal) -> None:
        """Set the plane normal direction (plain list or array, no units required)."""
        import numpy as _np
        arr = _np.asarray(normal, dtype=float)
        norm = float(_np.linalg.norm(arr))
        if norm < 1e-10:
            raise ValueError("normal must be a non-zero vector.")
        record = self._require_record()
        record["normal"] = (arr / norm).tolist()
        self._push_update()

    @records_scene_history
    def set_geometry(self, *, point=None, normal=None, skip_digestion: bool = False) -> None:
        """Update point and normal as one undoable geometry mutation."""
        import numpy as _np

        record = self._require_record()
        if point is not None:
            coords_nm = puw.get_value(point, to_unit="nm") if puw.is_quantity(point) else point
            point_arr = _np.asarray(coords_nm, dtype=float).tolist()
            if len(point_arr) != 3:
                raise ValueError("point must be a 3-element vector.")
            record["point"] = point_arr
        if normal is not None:
            normal_arr = _np.asarray(normal, dtype=float)
            norm = float(_np.linalg.norm(normal_arr))
            if norm < 1e-10:
                raise ValueError("normal must be a non-zero vector.")
            record["normal"] = (normal_arr / norm).tolist()
        self._push_update()

    @records_scene_history
    def set_invert(self, invert: bool) -> None:
        """Flip which side of the plane is clipped."""
        record = self._require_record()
        record["invert"] = bool(invert)
        self._push_update()

    @records_scene_history
    def show(self, skip_digestion: bool = False) -> None:
        """Enable this clipping plane."""
        record = self._require_record()
        if not record.get("hidden", False):
            return
        record["hidden"] = False
        self._hidden = False
        self._push_update()

    @records_scene_history
    def hide(self, skip_digestion: bool = False) -> None:
        """Disable this clipping plane without deleting it."""
        record = self._require_record()
        if record.get("hidden", False):
            return
        record["hidden"] = True
        self._hidden = True
        self._push_update()

    def enable_drag(self) -> None:
        """Show the interactive gizmo handles (centre + rim) for this section.

        Both handles are visible by default.  Call this after a previous
        :meth:`disable_drag` to restore them.
        """
        self._view._send({"op": "set_section_drag", "tag": self.tag, "enabled": True})  # noqa: SLF001

    def disable_drag(self) -> None:
        """Hide the interactive gizmo handles for this section.

        The clipping plane remains active; only the visual handles are hidden.
        Call :meth:`enable_drag` to restore them.
        """
        self._view._send({"op": "set_section_drag", "tag": self.tag, "enabled": False})  # noqa: SLF001

    @records_scene_history
    def delete(self, skip_digestion: bool = False) -> None:
        """Remove this clipping plane."""
        history = getattr(self._view, "_section_history", [])
        new_history = [r for r in history if r.get("tag") != self.tag]
        self._view._section_history = new_history  # noqa: SLF001
        self._view._scene_objects.pop((self.kind, self.tag), None)  # noqa: SLF001
        self._view._send({"op": "set_sections", "sections": new_history})  # noqa: SLF001
        sync = getattr(self._view, "_sync_section_summaries_runtime", None)
        if callable(sync):
            sync()
