from __future__ import annotations

from typing import Any

import numpy as np
import molsysmt as msm
from smonitor import signal

from ._private.arg_digestion import digest
from ._private.smonitor_emit import emit_suppressed_exception
from .layers import Layer, Measurement
from . import pyunitwizard as puw

_MEASUREMENT_POLICIES = {"atom", "centroid", "representative_atom"}
_NM_TO_ANGSTROM = puw.conversion_factor("nm", "angstroms")

_REPRESENTATIVE_DEFAULTS = {
    "protein": "CA",
    "nucleic": "P",
    "lipid": "P",
    "other": "",
}


class MeasurementsManager:
    """Measurement manager bound to a MolSysView."""

    def __init__(self, view: Any) -> None:
        self._view = view
        self._endpoint_policy_default = "centroid"
        self._representative_atoms = dict(_REPRESENTATIVE_DEFAULTS)

    def __getitem__(self, tag: str) -> Layer:
        layer = self.get(tag, skip_digestion=True)
        if layer is None:
            raise KeyError(tag)
        return layer

    def add(self, kind: str, *selections: Any, **kwargs: Any) -> Layer:
        """Create a measurement of explicit *kind*."""
        methods = {
            "distance": self.add_distance,
            "angle": self.add_angle,
            "dihedral": self.add_dihedral,
        }
        try:
            method = methods[str(kind).strip().lower()]
        except KeyError as exc:
            raise ValueError(f"Unsupported measurement kind {kind!r}; choose from {sorted(methods)}.") from exc
        return method(*selections, **kwargs)

    def _ensure_layer(self, tag: str, *, layer_tag: str | None = None) -> Layer:
        tag = self._view._tag_managers["measurement"].validate(tag)  # noqa: SLF001
        resolved_layer_tag = str(layer_tag).strip() if layer_tag is not None else tag
        self._view._ensure_layer_group(resolved_layer_tag, kind="measurement")  # noqa: SLF001
        measurement = Measurement(self._view, tag, layer_tag=resolved_layer_tag, meta={})
        self._view._scene_objects[("measurement", tag)] = measurement  # noqa: SLF001
        return measurement

    def _measurement_layer(self, tag: str) -> Layer | None:
        layer = self._view._scene_objects.get(("measurement", tag))  # noqa: SLF001
        if layer is None or getattr(layer, "kind", None) != "measurement":
            return None
        return layer

    def _require_measurement_layer(self, tag: str) -> Layer:
        layer = self._measurement_layer(tag)
        if layer is None:
            raise ValueError(f"No measurement layer found for tag {tag!r}.")
        return layer

    def _resolve_endpoint_atom_indices(self, arg: Any) -> list[int]:
        """Resolve an endpoint argument to a list of atom indices.

        Accepts a MolSysMT selection string or any iterable of integer indices.
        """
        if isinstance(arg, str):
            if self._view._molsys is None:  # noqa: SLF001
                raise ValueError("No molecular system loaded. Load a system before adding measurements.")
            return [
                int(i)
                for i in msm.select(
                    self._view._molsys,  # noqa: SLF001
                    selection=arg,
                    syntax="MolSysMT",
                    skip_digestion=True,
                )
            ]
        return list(arg)

    def _normalize_endpoint_policy(self, endpoint_policy: str | None) -> str:
        policy = self._endpoint_policy_default if endpoint_policy is None else str(endpoint_policy).strip().lower()
        if policy not in _MEASUREMENT_POLICIES:
            raise ValueError(f"Unsupported measurement endpoint policy {endpoint_policy!r}. Allowed: {sorted(_MEASUREMENT_POLICIES)}")
        return policy

    def _normalize_representative_target(self, target: str) -> str:
        key = str(target).strip().lower()
        if key not in self._representative_atoms:
            raise ValueError(f"Unsupported representative-atom target {target!r}. Allowed: {sorted(self._representative_atoms)}")
        return key

    def _atom_metadata_for_pick(self, atom_indices: list[int]) -> dict[str, list[Any]]:
        if self._view._molsys is None:  # noqa: SLF001
            return {"atom_name": [], "group_name": [], "group_type": []}
        try:
            values = msm.get(
                self._view._molsys,  # noqa: SLF001
                element="atom",
                selection=atom_indices,
                output_type="dictionary",
                atom_name=True,
                group_name=True,
                group_type=True,
                skip_digestion=True,
            )
        except Exception as exc:
            emit_suppressed_exception(
                "MeasurementsManager._atom_metadata_for_pick",
                exc,
                context={"atom_indices": repr(atom_indices)},
            )
            return {"atom_name": [], "group_name": [], "group_type": []}
        atom_names = list(values.get("atom_name", []) or [])
        group_names = list(values.get("group_name", []) or [])
        group_types = list(values.get("group_type", []) or [])
        return {"atom_name": atom_names, "group_name": group_names, "group_type": group_types}

    def _representative_category_for_pick(
        self,
        atom_indices: list[int],
        atom_names: list[str],
        group_types: list[str],
    ) -> str:
        normalized_group_types = {str(group_type).strip().lower() for group_type in group_types if str(group_type).strip()}
        if "amino acid" in normalized_group_types:
            return "protein"
        if "nucleotide" in normalized_group_types:
            return "nucleic"
        if "lipid" in normalized_group_types:
            return "lipid"
        atom_name_set = {str(name).strip().upper() for name in atom_names}
        if "CA" in atom_name_set:
            return "protein"
        if "P" in atom_name_set:
            return "nucleic" if len(atom_indices) <= 1 else "lipid"
        return "other"

    def _resolve_endpoint_metadata(
        self,
        picks_atom_indices: list[list[int]],
        endpoint_policy: str,
    ) -> tuple[list[str], list[str], list[list[int]]]:
        endpoint_kinds: list[str] = []
        endpoint_labels: list[str] = []
        endpoint_atom_indices: list[list[int]] = []
        for pick in picks_atom_indices:
            clean_pick = [int(item) for item in pick]
            if len(clean_pick) == 0:
                endpoint_kinds.append("atom")
                endpoint_labels.append("atom")
                endpoint_atom_indices.append([])
                continue
            if len(clean_pick) == 1:
                metadata = self._atom_metadata_for_pick(clean_pick)
                atom_name = str(metadata["atom_name"][0]).strip() if metadata["atom_name"] else "atom"
                endpoint_kinds.append("atom")
                endpoint_labels.append(atom_name or "atom")
                endpoint_atom_indices.append([clean_pick[0]])
                continue
            if endpoint_policy == "centroid":
                endpoint_kinds.append("centroid")
                endpoint_labels.append("centroid")
                endpoint_atom_indices.append([])
                continue
            metadata = self._atom_metadata_for_pick(clean_pick)
            atom_names = [str(item).strip() for item in metadata["atom_name"]]
            group_types = [str(item).strip() for item in metadata["group_type"]]
            category = self._representative_category_for_pick(clean_pick, atom_names, group_types)
            preferred = self._representative_atoms.get(category, "") or self._representative_atoms.get("other", "")
            preferred = str(preferred).strip()
            chosen_index = clean_pick[0]
            chosen_label = atom_names[0] if atom_names else preferred or "representative_atom"
            if preferred:
                for atom_index, atom_name in zip(clean_pick, atom_names):
                    if atom_name.upper() == preferred.upper():
                        chosen_index = atom_index
                        chosen_label = atom_name
                        break
            endpoint_kinds.append("representative_atom")
            endpoint_labels.append(chosen_label or preferred or "representative_atom")
            endpoint_atom_indices.append([chosen_index])
        return endpoint_kinds, endpoint_labels, endpoint_atom_indices

    def _build_measurement_message(
        self,
        op: str,
        picks_atom_indices: list[list[int]],
        tag: str,
        *,
        layer_tag: str | None = None,
        endpoint_policy: str | None = None,
        value: float | None = None,
        value_series: list[float] | None = None,
        style: dict | None = None,
    ) -> dict:
        policy = self._normalize_endpoint_policy(endpoint_policy)
        endpoint_kinds, endpoint_labels, endpoint_atom_indices = self._resolve_endpoint_metadata(picks_atom_indices, policy)
        options: dict = {
            "tag": tag,
            "layer_tag": layer_tag or tag,
            "picks_atom_indices": picks_atom_indices,
            "endpoint_kinds": endpoint_kinds,
            "endpoint_policy": policy,
            "endpoint_labels": endpoint_labels,
            "endpoint_atom_indices": endpoint_atom_indices,
        }
        if value is not None:
            options["value"] = float(value)
        if value_series is not None:
            options["value_series"] = [float(item) for item in value_series]
        if style:
            options["style"] = dict(style)
        return {
            "op": op,
            "tag": tag,
            "options": options,
        }

    def _record_measurement(
        self,
        op: str,
        picks_atom_indices: list[list[int]],
        tag: str,
        *,
        layer_tag: str | None = None,
        endpoint_policy: str | None = None,
        value: float | None = None,
        value_series: list[float] | None = None,
        style: dict | None = None,
    ) -> Layer:
        layer = self._ensure_layer(tag, layer_tag=layer_tag)
        msg = self._build_measurement_message(
            op,
            picks_atom_indices,
            tag,
            layer_tag=getattr(layer, "layer_tag", tag),
            endpoint_policy=endpoint_policy,
            value=value,
            value_series=value_series,
            style=style,
        )
        self._view._record_measurement_message(msg)  # noqa: SLF001
        self._view._last_measurement_created_event = {  # noqa: SLF001
            "event": "interaction_measurement_created",
            "action": {
                "add_distance_measurement": "distance",
                "add_angle_measurement": "angle",
                "add_dihedral_measurement": "dihedral",
            }[op],
            "picked_count": len(picks_atom_indices),
            "picks_atom_indices": [list(item) for item in picks_atom_indices],
            "endpoint_kinds": msg["options"]["endpoint_kinds"],
            "endpoint_policy": msg["options"]["endpoint_policy"],
            "endpoint_labels": msg["options"]["endpoint_labels"],
            "endpoint_atom_indices": msg["options"]["endpoint_atom_indices"],
            "tag": tag,
        }
        return layer

    def _endpoint_positions_nm(self, pick: list[int], ea_indices: list[int], policy: str) -> "np.ndarray | None":
        molsys = self._view._molsys  # noqa: SLF001
        if molsys is None:
            return None
        try:
            if policy == "centroid" and len(pick) > 1:
                atoms = pick
            elif ea_indices:
                atoms = [ea_indices[0]]
            elif pick:
                atoms = [pick[0]]
            else:
                return None
            result = msm.get(molsys, element="atom", selection=atoms, output_type="dictionary", coordinates=True, skip_digestion=True)
            coords = result.get("coordinates")
            if coords is None:
                return None
            arr = np.asarray(coords, dtype=float)
            if arr.ndim == 2:
                arr = arr[np.newaxis, :, :]
            if arr.ndim != 3 or arr.shape[-1] != 3:
                return None
            return arr.mean(axis=1)
        except Exception as exc:
            emit_suppressed_exception(
                "MeasurementsManager._endpoint_positions_nm",
                exc,
                context={"pick": repr(pick), "endpoint_atom_indices": repr(ea_indices), "policy": policy},
            )
            return None

    def _compute_measurement_series(
        self,
        op: str,
        picks_atom_indices: list[list[int]],
        endpoint_atom_indices: list[list[int]],
        endpoint_policy: str,
    ) -> "np.ndarray | None":
        positions = []
        for i, pick in enumerate(picks_atom_indices):
            ea = endpoint_atom_indices[i] if i < len(endpoint_atom_indices) else []
            pos = self._endpoint_positions_nm(pick, ea, endpoint_policy)
            if pos is None:
                return None
            positions.append(pos)

        try:
            frame_count = min(pos.shape[0] for pos in positions)
            if frame_count == 0:
                return None
            positions = [pos[:frame_count] for pos in positions]
            if op == "add_distance_measurement" and len(positions) == 2:
                return np.linalg.norm(positions[1] - positions[0], axis=1) * _NM_TO_ANGSTROM  # nm -> Å
            if op == "add_angle_measurement" and len(positions) == 3:
                v1 = positions[0] - positions[1]
                v2 = positions[2] - positions[1]
                n1 = np.linalg.norm(v1, axis=1)
                n2 = np.linalg.norm(v2, axis=1)
                denom = n1 * n2
                if np.any(denom == 0):
                    return None
                cosines = np.einsum("ij,ij->i", v1, v2) / denom
                return np.degrees(np.arccos(np.clip(cosines, -1.0, 1.0)))
            if op == "add_dihedral_measurement" and len(positions) == 4:
                values = []
                for p0, p1, p2, p3 in zip(*positions):
                    b1 = p1 - p0
                    b2 = p2 - p1
                    b3 = p3 - p2
                    n1 = np.cross(b1, b2)
                    n2 = np.cross(b2, b3)
                    nn1, nn2 = np.linalg.norm(n1), np.linalg.norm(n2)
                    if nn1 == 0 or nn2 == 0:
                        return None
                    n1 /= nn1
                    n2 /= nn2
                    m1 = np.cross(n1, b2 / (np.linalg.norm(b2) or 1))
                    x = np.dot(n1, n2)
                    y = np.dot(m1, n2)
                    values.append(float(np.degrees(np.arctan2(y, x))))
                return np.asarray(values, dtype=float)
        except Exception as exc:
            emit_suppressed_exception(
                "MeasurementsManager._compute_measurement_series",
                exc,
                context={"op": op, "endpoint_policy": endpoint_policy},
            )
            return None
        return None

    def _compute_measurement_value(
        self,
        op: str,
        picks_atom_indices: list[list[int]],
        endpoint_atom_indices: list[list[int]],
        endpoint_policy: str,
    ) -> float | None:
        series = self._compute_measurement_series(op, picks_atom_indices, endpoint_atom_indices, endpoint_policy)
        if series is None or len(series) == 0:
            return None
        return float(series[0])

    def _active_series_index(self, series_length: int) -> int:
        if series_length <= 1:
            return 0
        index = int(getattr(self._view, "_current_structure_index", 0))
        return min(max(index, 0), series_length - 1)

    def _send_measurement(
        self,
        op: str,
        picks_atom_indices: list[list[int]],
        tag: str,
        *,
        layer_tag: str | None = None,
        endpoint_policy: str | None = None,
        value: float | None = None,
        value_series: list[float] | None = None,
        style: dict | None = None,
    ) -> Layer:
        if value is None and value_series is None:
            policy = self._normalize_endpoint_policy(endpoint_policy)
            _, _, ea_indices = self._resolve_endpoint_metadata(picks_atom_indices, policy)
            series = self._compute_measurement_series(op, picks_atom_indices, ea_indices, policy)
            if series is not None and len(series) > 0:
                value = float(series[0])
                value_series = [float(item) for item in series]
        layer = self._record_measurement(
            op,
            picks_atom_indices,
            tag,
            layer_tag=layer_tag,
            endpoint_policy=endpoint_policy,
            value=value,
            value_series=value_series,
            style=style,
        )
        self._view._send(
            self._build_measurement_message(
                op,
                picks_atom_indices,
                tag,
                layer_tag=getattr(layer, "layer_tag", tag),
                endpoint_policy=endpoint_policy,
                value=value,
                value_series=value_series,
                style=style,
            )
        )  # noqa: SLF001
        return layer

    def _sync_frontend_settings(self) -> None:
        self._view._send(  # noqa: SLF001
            {
                "op": "set_measurement_settings",
                "options": {
                    "endpoint_policy_default": self._endpoint_policy_default,
                    "representative_atoms": dict(self._representative_atoms),
                },
            }
        )

    def _register_interactive_measurement(self, event: dict, *, tag: str | None = None) -> Layer:
        action = event.get("action")
        picks = event.get("picks_atom_indices") or []
        if not isinstance(picks, list) or len(picks) == 0:
            raise ValueError("Interactive measurement event does not contain valid picks.")

        layer_tag = tag or event.get("tag") or self._view._next_measurement_tag()  # noqa: SLF001
        if not isinstance(layer_tag, str) or layer_tag.strip() == "":
            raise ValueError("Interactive measurement tag must be a non-empty string.")
        layer_tag = layer_tag.strip()
        event_policy = event.get("endpoint_policy")
        raw_value = event.get("value")
        event_value: float | None = float(raw_value) if raw_value is not None else None

        if action == "distance" and len(picks) == 2:
            layer = self._record_measurement(
                "add_distance_measurement",
                [list(picks[0]), list(picks[1])],
                layer_tag,
                endpoint_policy=event_policy,
                value=event_value,
            )
        elif action == "angle" and len(picks) == 3:
            layer = self._record_measurement(
                "add_angle_measurement",
                [list(picks[0]), list(picks[1]), list(picks[2])],
                layer_tag,
                endpoint_policy=event_policy,
                value=event_value,
            )
        elif action == "dihedral" and len(picks) == 4:
            layer = self._record_measurement(
                "add_dihedral_measurement",
                [list(picks[0]), list(picks[1]), list(picks[2]), list(picks[3])],
                layer_tag,
                endpoint_policy=event_policy,
                value=event_value,
            )
        else:
            raise ValueError("Stored interactive measurement is incomplete or unsupported.")

        event["tag"] = layer_tag
        if "endpoint_kinds" not in event:
            event["endpoint_kinds"], _, _ = self._resolve_endpoint_metadata(
                [list(item) for item in picks],
                self._normalize_endpoint_policy(event.get("endpoint_policy")),
            )
        if "endpoint_policy" not in event:
            event["endpoint_policy"] = self._endpoint_policy_default
        if "endpoint_labels" not in event:
            _, event["endpoint_labels"], event["endpoint_atom_indices"] = self._resolve_endpoint_metadata(
                [list(item) for item in picks],
                self._normalize_endpoint_policy(event.get("endpoint_policy")),
            )
        if "endpoint_atom_indices" not in event:
            _, _, event["endpoint_atom_indices"] = self._resolve_endpoint_metadata(
                [list(item) for item in picks],
                self._normalize_endpoint_policy(event.get("endpoint_policy")),
            )
        self._view._last_measurement_created_event = dict(event)  # noqa: SLF001
        return layer

    def records(self) -> list[dict]:
        return [dict(record) for record in self._view._measurement_history]  # noqa: SLF001

    def count(self) -> int:
        return len(self._view._measurement_history)  # noqa: SLF001

    @signal(tags=["measurement"])
    @digest()
    def tags(self, skip_digestion: bool = False) -> list[str]:
        return [tag for kind, tag in self._view._scene_objects if kind == "measurement"]  # noqa: SLF001

    @signal(tags=["measurement"])
    @digest()
    def contains(self, tag: str, skip_digestion: bool = False) -> bool:
        return self._measurement_layer(tag) is not None

    @signal(tags=["measurement"])
    @digest()
    def get(self, tag: str, skip_digestion: bool = False) -> Layer | None:
        return self._measurement_layer(tag)

    def info(self, tag: str | None = None) -> list[dict]:
        items: list[dict] = []
        for record in self._view._measurement_history:  # noqa: SLF001
            layer_tag = record.get("tag")
            if tag is not None and layer_tag != tag:
                continue
            op = record.get("op")
            kind = {
                "add_distance_measurement": "distance",
                "add_angle_measurement": "angle",
                "add_dihedral_measurement": "dihedral",
            }.get(op, "measurement")
            picks = record.get("options", {}).get("picks_atom_indices", [])
            endpoint_kinds = record.get("options", {}).get("endpoint_kinds", [])
            endpoint_policy = record.get("options", {}).get("endpoint_policy", self._endpoint_policy_default)
            endpoint_labels = record.get("options", {}).get("endpoint_labels", [])
            endpoint_atom_indices = record.get("options", {}).get("endpoint_atom_indices", [])
            options = record.get("options") if isinstance(record.get("options"), dict) else {}
            raw_series = options.get("value_series")
            raw_value = options.get("value")
            if isinstance(raw_series, list) and len(raw_series) > 0:
                active_index = self._active_series_index(len(raw_series))
                raw_value = raw_series[active_index]
            if raw_value is not None:
                v = float(raw_value)
                unit = "angstrom" if kind == "distance" else "degrees"
                stored_value = puw.standardize(puw.quantity(v, unit))
            else:
                stored_value = None
            layer = self._view._scene_objects.get(("measurement", layer_tag))  # noqa: SLF001
            items.append(
                {
                    "kind": kind,
                    "tag": layer_tag,
                    "layer_tag": getattr(layer, "layer_tag", layer_tag),
                    "n_picks": len(picks) if isinstance(picks, list) else 0,
                    "picks_atom_indices": [list(item) for item in picks] if isinstance(picks, list) else [],
                    "endpoint_kinds": list(endpoint_kinds) if isinstance(endpoint_kinds, list) else [],
                    "endpoint_policy": endpoint_policy if isinstance(endpoint_policy, str) else self._endpoint_policy_default,
                    "endpoint_labels": list(endpoint_labels) if isinstance(endpoint_labels, list) else [],
                    "endpoint_atom_indices": [list(item) for item in endpoint_atom_indices] if isinstance(endpoint_atom_indices, list) else [],
                    "value": stored_value,
                    "visible": False if layer is None else not getattr(layer, "_hidden", False),
                    "active": False if layer is None else bool(getattr(layer, "_active", False)),
                }
            )
        return items

    def series(self, tag: str):
        """Return the stored or recomputed measurement time series for *tag*."""
        record = next((item for item in self._view._measurement_history if item.get("tag") == tag), None)  # noqa: SLF001
        if record is None:
            raise ValueError(f"No measurement layer found for tag {tag!r}.")
        op = record.get("op")
        kind = {
            "add_distance_measurement": "distance",
            "add_angle_measurement": "angle",
            "add_dihedral_measurement": "dihedral",
        }.get(op, "measurement")
        unit = "angstrom" if kind == "distance" else "degrees"
        options = record.get("options") if isinstance(record.get("options"), dict) else {}
        raw_series = options.get("value_series")
        if isinstance(raw_series, list) and len(raw_series) > 0:
            return puw.standardize(puw.quantity([float(item) for item in raw_series], unit))
        raw_value = options.get("value")
        if raw_value is not None:
            return puw.standardize(puw.quantity([float(raw_value)], unit))

        picks = options.get("picks_atom_indices")
        endpoint_atom_indices = options.get("endpoint_atom_indices")
        endpoint_policy = options.get("endpoint_policy", self._endpoint_policy_default)
        if not isinstance(picks, list) or not isinstance(endpoint_atom_indices, list) or not isinstance(endpoint_policy, str):
            return None
        series = self._compute_measurement_series(op, picks, endpoint_atom_indices, endpoint_policy)
        if series is None or len(series) == 0:
            return None
        return puw.standardize(puw.quantity([float(item) for item in series], unit))

    @signal(tags=["measurement"])
    @digest()
    def settings(self, skip_digestion: bool = False) -> dict[str, Any]:
        return {
            "endpoint_policy_default": self._endpoint_policy_default,
            "representative_atoms": dict(self._representative_atoms),
        }

    @signal(tags=["measurement"])
    @digest()
    def set_endpoint_policy(self, endpoint_policy: str, *, skip_digestion: bool = False) -> None:
        self._endpoint_policy_default = self._normalize_endpoint_policy(endpoint_policy)
        self._sync_frontend_settings()

    @signal(tags=["measurement"])
    @digest()
    def set_representative_atom(self, target: str, atom_name: str, *, skip_digestion: bool = False) -> None:
        normalized_target = self._normalize_representative_target(target)
        value = str(atom_name).strip()
        self._representative_atoms[normalized_target] = value
        self._sync_frontend_settings()

    @signal(tags=["measurement", "visibility"])
    @digest()
    def show(self, tag: str, skip_digestion: bool = False) -> Layer:
        layer = self._require_measurement_layer(tag)
        layer.show(skip_digestion=True)
        return layer

    @signal(tags=["measurement", "visibility"])
    @digest()
    def hide(self, tag: str, skip_digestion: bool = False) -> Layer:
        layer = self._require_measurement_layer(tag)
        layer.hide(skip_digestion=True)
        return layer

    @signal(tags=["measurement"])
    @digest()
    def delete(self, tag: str, skip_digestion: bool = False) -> None:
        layer = self._require_measurement_layer(tag)
        layer.delete(skip_digestion=True)

    @signal(tags=["measurement"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False) -> None:
        """Remove all measurements, or only the one identified by *tag*."""
        if tag is not None:
            self.delete(tag, skip_digestion=True)
            return
        for measurement_tag in self.tags(skip_digestion=True):
            self._require_measurement_layer(measurement_tag).delete(skip_digestion=True)

    @signal(tags=["measurement"])
    @digest()
    def set_tag(self, tag: str, new_tag: str, skip_digestion: bool = False) -> Layer:
        layer = self._require_measurement_layer(tag)
        layer.set_tag(new_tag, skip_digestion=True)
        return layer

    @signal(tags=["measurement"])
    @digest()
    def set_layer_tag(self, tag: str, new_layer_tag: str, skip_digestion: bool = False) -> Layer:
        layer = self._require_measurement_layer(tag)
        layer.set_layer_tag(new_layer_tag, skip_digestion=True)
        return layer

    @signal(tags=["measurement"])
    @digest()
    def add_distance(
        self,
        selection_a: Any = None,
        selection_b: Any = None,
        *,
        atom_indices_a: Any = None,
        atom_indices_b: Any = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        endpoint_policy: str | None = None,
        measurement_style: dict | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        import warnings
        if atom_indices_a is not None:
            warnings.warn("atom_indices_a is deprecated; use selection_a instead.", DeprecationWarning, stacklevel=2)
            if selection_a is None:
                selection_a = atom_indices_a
        if atom_indices_b is not None:
            warnings.warn("atom_indices_b is deprecated; use selection_b instead.", DeprecationWarning, stacklevel=2)
            if selection_b is None:
                selection_b = atom_indices_b
        if selection_a is None or selection_b is None:
            raise ValueError("selection_a and selection_b are required.")
        object_tag = tag or self._view._next_measurement_tag()  # noqa: SLF001
        return self._send_measurement(
            "add_distance_measurement",
            [self._resolve_endpoint_atom_indices(selection_a), self._resolve_endpoint_atom_indices(selection_b)],
            object_tag,
            layer_tag=layer_tag,
            endpoint_policy=endpoint_policy,
            style=measurement_style,
        )

    @signal(tags=["measurement"])
    @digest()
    def add_angle(
        self,
        selection_a: Any = None,
        selection_b: Any = None,
        selection_c: Any = None,
        *,
        atom_indices_a: Any = None,
        atom_indices_b: Any = None,
        atom_indices_c: Any = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        endpoint_policy: str | None = None,
        measurement_style: dict | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        import warnings
        if atom_indices_a is not None:
            warnings.warn("atom_indices_a is deprecated; use selection_a instead.", DeprecationWarning, stacklevel=2)
            if selection_a is None:
                selection_a = atom_indices_a
        if atom_indices_b is not None:
            warnings.warn("atom_indices_b is deprecated; use selection_b instead.", DeprecationWarning, stacklevel=2)
            if selection_b is None:
                selection_b = atom_indices_b
        if atom_indices_c is not None:
            warnings.warn("atom_indices_c is deprecated; use selection_c instead.", DeprecationWarning, stacklevel=2)
            if selection_c is None:
                selection_c = atom_indices_c
        if selection_a is None or selection_b is None or selection_c is None:
            raise ValueError("selection_a, selection_b, and selection_c are required.")
        object_tag = tag or self._view._next_measurement_tag()  # noqa: SLF001
        return self._send_measurement(
            "add_angle_measurement",
            [
                self._resolve_endpoint_atom_indices(selection_a),
                self._resolve_endpoint_atom_indices(selection_b),
                self._resolve_endpoint_atom_indices(selection_c),
            ],
            object_tag,
            layer_tag=layer_tag,
            endpoint_policy=endpoint_policy,
            style=measurement_style,
        )

    @signal(tags=["measurement"])
    @digest()
    def add_dihedral(
        self,
        selection_a: Any = None,
        selection_b: Any = None,
        selection_c: Any = None,
        selection_d: Any = None,
        *,
        atom_indices_a: Any = None,
        atom_indices_b: Any = None,
        atom_indices_c: Any = None,
        atom_indices_d: Any = None,
        tag: str | None = None,
        layer_tag: str | None = None,
        endpoint_policy: str | None = None,
        measurement_style: dict | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        import warnings
        if atom_indices_a is not None:
            warnings.warn("atom_indices_a is deprecated; use selection_a instead.", DeprecationWarning, stacklevel=2)
            if selection_a is None:
                selection_a = atom_indices_a
        if atom_indices_b is not None:
            warnings.warn("atom_indices_b is deprecated; use selection_b instead.", DeprecationWarning, stacklevel=2)
            if selection_b is None:
                selection_b = atom_indices_b
        if atom_indices_c is not None:
            warnings.warn("atom_indices_c is deprecated; use selection_c instead.", DeprecationWarning, stacklevel=2)
            if selection_c is None:
                selection_c = atom_indices_c
        if atom_indices_d is not None:
            warnings.warn("atom_indices_d is deprecated; use selection_d instead.", DeprecationWarning, stacklevel=2)
            if selection_d is None:
                selection_d = atom_indices_d
        if selection_a is None or selection_b is None or selection_c is None or selection_d is None:
            raise ValueError("selection_a, selection_b, selection_c, and selection_d are required.")
        object_tag = tag or self._view._next_measurement_tag()  # noqa: SLF001
        return self._send_measurement(
            "add_dihedral_measurement",
            [
                self._resolve_endpoint_atom_indices(selection_a),
                self._resolve_endpoint_atom_indices(selection_b),
                self._resolve_endpoint_atom_indices(selection_c),
                self._resolve_endpoint_atom_indices(selection_d),
            ],
            object_tag,
            layer_tag=layer_tag,
            endpoint_policy=endpoint_policy,
            style=measurement_style,
        )


__all__ = ["MeasurementsManager"]
