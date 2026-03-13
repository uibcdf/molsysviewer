from __future__ import annotations

from typing import Any

from smonitor import signal

from ._private.arg_digestion import digest
from .layers import Layer


class MeasurementsManager:
    """Measurement manager bound to a MolSysView."""

    def __init__(self, view: Any) -> None:
        self._view = view

    def _ensure_layer(self, tag: str) -> Layer:
        if tag not in self._view._layers:  # noqa: SLF001
            self._view._layers[tag] = Layer(self._view, tag, kind="measurement", meta={})  # noqa: SLF001
        else:
            self._view._layers[tag].kind = "measurement"  # noqa: SLF001
        return self._view._layers[tag]  # noqa: SLF001

    def _send_measurement(self, op: str, picks_atom_indices: list[list[int]], tag: str) -> Layer:
        layer = self._ensure_layer(tag)
        self._view._send(  # noqa: SLF001
            {
                "op": op,
                "tag": tag,
                "options": {
                    "tag": tag,
                    "picks_atom_indices": picks_atom_indices,
                },
            }
        )
        return layer

    def records(self) -> list[dict]:
        return [dict(record) for record in self._view._measurement_history]  # noqa: SLF001

    def count(self) -> int:
        return len(self._view._measurement_history)  # noqa: SLF001

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
            layer = self._view._layers.get(layer_tag)  # noqa: SLF001
            items.append(
                {
                    "kind": kind,
                    "tag": layer_tag,
                    "n_picks": len(picks) if isinstance(picks, list) else 0,
                    "picks_atom_indices": [list(item) for item in picks] if isinstance(picks, list) else [],
                    "visible": False if layer is None else not getattr(layer, "_hidden", False),
                    "active": False if layer is None else bool(getattr(layer, "_active", False)),
                }
            )
        return items

    @signal(tags=["measurement"])
    @digest()
    def add_distance(
        self,
        atom_indices_a: Any,
        atom_indices_b: Any,
        *,
        tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        layer_tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        return self._send_measurement("add_distance_measurement", [list(atom_indices_a), list(atom_indices_b)], layer_tag)

    @signal(tags=["measurement"])
    @digest()
    def add_angle(
        self,
        atom_indices_a: Any,
        atom_indices_b: Any,
        atom_indices_c: Any,
        *,
        tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        layer_tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        return self._send_measurement(
            "add_angle_measurement",
            [list(atom_indices_a), list(atom_indices_b), list(atom_indices_c)],
            layer_tag,
        )

    @signal(tags=["measurement"])
    @digest()
    def add_dihedral(
        self,
        atom_indices_a: Any,
        atom_indices_b: Any,
        atom_indices_c: Any,
        atom_indices_d: Any,
        *,
        tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        layer_tag = tag or self._view._next_layer_tag()  # noqa: SLF001
        return self._send_measurement(
            "add_dihedral_measurement",
            [list(atom_indices_a), list(atom_indices_b), list(atom_indices_c), list(atom_indices_d)],
            layer_tag,
        )

    @signal(tags=["measurement", "selection"])
    @digest()
    def persist_last_measurement(
        self,
        *,
        tag: str | None = None,
        skip_digestion: bool = False,
    ) -> Layer:
        event = self._view.get_last_measurement_created_event()
        if event is None:
            raise ValueError("No interactive measurement stored. Create a measurement before persisting it.")

        action = event.get("action")
        picks = event.get("picks_atom_indices") or []
        if not isinstance(picks, list) or len(picks) == 0:
            raise ValueError("Stored interactive measurement does not contain valid picks.")

        layer_tag = tag or self._view._next_layer_tag()  # noqa: SLF001

        if action == "distance" and len(picks) == 2:
            return self.add_distance(picks[0], picks[1], tag=layer_tag, skip_digestion=True)
        if action == "angle" and len(picks) == 3:
            return self.add_angle(picks[0], picks[1], picks[2], tag=layer_tag, skip_digestion=True)
        if action == "dihedral" and len(picks) == 4:
            return self.add_dihedral(picks[0], picks[1], picks[2], picks[3], tag=layer_tag, skip_digestion=True)

        raise ValueError("Stored interactive measurement is incomplete or unsupported.")


__all__ = ["MeasurementsManager"]
