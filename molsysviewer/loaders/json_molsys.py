"""Portable JSON payload serialization directly from a materialized MolSys."""

from __future__ import annotations

from typing import Any

import numpy as np

from .._pyunitwizard import puw
from .array_native_molsys import serialize_static_molsys_payload


def _finite_array(
    values: Any,
    *,
    unit: str,
    shape: tuple[int, ...],
    name: str,
) -> np.ndarray:
    array = np.asarray(puw.get_value(values, to_unit=unit), dtype=np.float64)
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}; received {array.shape}.")
    if not bool(np.isfinite(array).all()):
        raise ValueError(f"{name} must contain only finite values.")
    return array


def serialize_json_molsys(molsys: Any) -> dict[str, Any]:
    """Build the frontend's portable payload without a ViewerJSON intermediate."""

    n_atoms = int(molsys.get_n_atoms())
    structures = molsys.structures
    n_structures = int(structures.n_structures)
    if n_atoms <= 0:
        raise ValueError("JSON MolSys payload requires at least one atom.")
    if n_structures <= 0 or structures.coordinates is None:
        raise ValueError("JSON MolSys payload requires structural coordinates.")

    coordinates = _finite_array(
        structures.coordinates,
        unit="angstroms",
        shape=(n_structures, n_atoms, 3),
        name="coordinates",
    )
    box = None
    if structures.box is not None:
        box = _finite_array(
            structures.box,
            unit="angstroms",
            shape=(n_structures, 3, 3),
            name="box",
        )
    time = None
    if structures.time is not None:
        time = _finite_array(
            structures.time,
            unit="ps",
            shape=(n_structures,),
            name="time",
        )

    structure_records: list[dict[str, Any]] = []
    for index in range(n_structures):
        record: dict[str, Any] = {"coordinates": coordinates[index].tolist()}
        if box is not None:
            record["box"] = box[index].tolist()
        if time is not None:
            record["time"] = float(time[index])
        structure_records.append(record)

    return {
        **serialize_static_molsys_payload(molsys, n_atoms),
        "structures": structure_records,
    }


def build_json_molsys_message(
    molsys: Any,
    *,
    label: str | None,
) -> dict[str, Any]:
    """Build the complete existing `load_molsys_payload` wire message."""

    return {
        "op": "load_molsys_payload",
        "payload": serialize_json_molsys(molsys),
        "label": label,
        "multiple_structures": int(molsys.structures.n_structures) > 1,
    }
