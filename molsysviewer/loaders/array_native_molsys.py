"""Array-native serialization for materialized MolSys structural data.

This module deliberately stops before transport. It prepares a small
JSON-compatible metadata payload plus contiguous numeric arrays that an
AnyWidget adapter can send as binary buffers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import molsysmt as msm
import numpy as np

from .._pyunitwizard import puw


ARRAY_NATIVE_PROTOCOL_VERSION = 1


@dataclass(frozen=True)
class ArrayNativeMolSysPayload:
    """Static metadata and ordered binary arrays for one complete MolSys."""

    metadata: dict[str, Any]
    arrays: tuple[np.ndarray, ...]

    @property
    def buffers(self) -> tuple[memoryview, ...]:
        return tuple(memoryview(array).cast("B") for array in self.arrays)


def _column(
    values: Any,
    n_atoms: int,
    *,
    default: Any,
    cast: type,
) -> list[Any]:
    if values is None:
        return [default(index) if callable(default) else default for index in range(n_atoms)]
    array = np.asarray(values, dtype=object)
    if array.ndim != 1 or array.shape[0] != n_atoms:
        return [default(index) if callable(default) else default for index in range(n_atoms)]

    output: list[Any] = []
    for index, value in enumerate(array):
        fallback = default(index) if callable(default) else default
        try:
            if value is None:
                raise ValueError
            converted = cast(value)
            if isinstance(converted, float) and not np.isfinite(converted):
                raise ValueError
            output.append(converted)
        except (TypeError, ValueError, OverflowError):
            output.append(fallback)
    return output


def _atom_attribute(molsys: Any, attribute: str) -> Any:
    try:
        return msm.get(
            molsys,
            element="atom",
            skip_digestion=True,
            **{attribute: True},
        )
    except Exception:
        return None


def serialize_static_molsys_payload(molsys: Any, n_atoms: int) -> dict[str, Any]:
    """Return the canonical JSON-compatible topology shared by both encoders."""
    atoms = {
        "atom_id": _column(_atom_attribute(molsys, "atom_id"), n_atoms, default=lambda i: i + 1, cast=int),
        "atom_name": _column(_atom_attribute(molsys, "atom_name"), n_atoms, default=lambda i: f"A{i + 1}", cast=str),
        "residue_id": _column(_atom_attribute(molsys, "group_id"), n_atoms, default=1, cast=int),
        "residue_name": _column(_atom_attribute(molsys, "group_name"), n_atoms, default="RES", cast=str),
        "chain_id": _column(_atom_attribute(molsys, "chain_id"), n_atoms, default="A", cast=str),
        # `chain_id` and `group_id` are *author* labels, and a bioassembly reuses them:
        # 2BUK's 60 copies all call their chains A-E, so 300 chains arrive under 5 distinct
        # values and 20 700 residues under 345. Mol* groups by the value, so the copies
        # collapsed into one chain's worth of hierarchy and only one could be drawn as
        # cartoon -- while the waters, which are per-atom points needing no hierarchy, all
        # appeared (uibcdf/molsysviewer#64).
        #
        # These two indices are the internal identity mmCIF keeps separate from the author
        # label for exactly this reason. They feed `label_asym_id` and `label_seq_id`; the
        # labels above still feed `auth_*`, which is what a user sees and selects by.
        "chain_index": _column(_atom_attribute(molsys, "chain_index"), n_atoms, default=lambda i: 0, cast=int),
        "residue_index": _column(_atom_attribute(molsys, "group_index"), n_atoms, default=lambda i: 0, cast=int),
        "entity_id": _column(_atom_attribute(molsys, "entity_id"), n_atoms, default="1", cast=str),
        "element_symbol": _column(_atom_attribute(molsys, "atom_type"), n_atoms, default="C", cast=str),
        "formal_charge": _column(_atom_attribute(molsys, "formal_charge"), n_atoms, default=0, cast=int),
        "molecule_id": _column(_atom_attribute(molsys, "molecule_index"), n_atoms, default=0, cast=int),
        "molecule_name": _column(_atom_attribute(molsys, "molecule_name"), n_atoms, default="Molecule", cast=str),
        "component_id": _column(_atom_attribute(molsys, "component_index"), n_atoms, default=0, cast=int),
        "component_name": _column(_atom_attribute(molsys, "component_name"), n_atoms, default="Component", cast=str),
        "group_type": _column(_atom_attribute(molsys, "group_type"), n_atoms, default="", cast=str),
    }

    bonds_frame = molsys.topology.bonds
    if bonds_frame is None or len(bonds_frame) == 0:
        return {"atoms": atoms}

    bonds: dict[str, Any] = {
        "indexA": np.asarray(bonds_frame["atom1_index"], dtype=np.int64).tolist(),
        "indexB": np.asarray(bonds_frame["atom2_index"], dtype=np.int64).tolist(),
    }
    if "bond_order" in bonds_frame:
        bonds["order"] = _column(
            bonds_frame["bond_order"],
            len(bonds_frame),
            default=1,
            cast=int,
        )
    if "bond_type" in bonds_frame:
        bonds["type"] = _column(
            bonds_frame["bond_type"],
            len(bonds_frame),
            default="",
            cast=str,
        )
    return {"atoms": atoms, "bonds": bonds}


def _wire_array(values: Any, *, dtype: str, shape: tuple[int, ...], name: str) -> np.ndarray:
    array = np.ascontiguousarray(values, dtype=np.dtype(dtype))
    if array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}; received {array.shape}.")
    if not bool(np.isfinite(array).all()):
        raise ValueError(f"{name} must contain only finite values.")
    return array


def _descriptor(
    array: np.ndarray,
    *,
    kind: str,
    units: str,
    buffer_index: int,
    layout: str = "structure-major-c",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "dtype": "float32" if array.dtype == np.dtype("<f4") else "float64",
        "shape": list(array.shape),
        "layout": layout,
        "units": units,
        "endianness": "little",
        "buffer_index": buffer_index,
        "byte_length": array.nbytes,
    }


def serialize_array_native_molsys(molsys: Any) -> ArrayNativeMolSysPayload:
    """Prepare a complete materialized MolSys without structural nested lists."""

    n_atoms = int(molsys.get_n_atoms())
    structures = molsys.structures
    n_structures = int(structures.n_structures)
    if n_atoms <= 0:
        raise ValueError("Array-native MolSys payload requires at least one atom.")
    if n_structures <= 0 or structures.coordinates is None:
        raise ValueError("Array-native MolSys payload requires structural coordinates.")

    # Planar per structure: all x, then all y, then all z. Mol* wants separate
    # x/y/z axis arrays, so this layout lets the frontend take zero-copy
    # subarray views instead of de-interleaving every frame in a scalar JS loop.
    # The transpose happens once here, vectorized, instead of atoms*structures*3
    # scalar assignments in the browser.
    coordinates = _wire_array(
        np.asarray(
            puw.get_value(structures.coordinates, to_unit="angstroms")
        ).transpose(0, 2, 1),
        dtype="<f4",
        shape=(n_structures, 3, n_atoms),
        name="coordinates",
    )
    arrays: list[np.ndarray] = [coordinates]
    descriptors = [
        _descriptor(
            coordinates,
            kind="coordinates",
            units="angstrom",
            buffer_index=0,
            layout="structure-planar-c",
        )
    ]

    if structures.box is not None:
        box = _wire_array(
            puw.get_value(structures.box, to_unit="angstroms"),
            dtype="<f4",
            shape=(n_structures, 3, 3),
            name="box",
        )
        descriptors.append(
            _descriptor(box, kind="box", units="angstrom", buffer_index=len(arrays))
        )
        arrays.append(box)

    if structures.time is not None:
        time = _wire_array(
            puw.get_value(structures.time, to_unit="ps"),
            dtype="<f8",
            shape=(n_structures,),
            name="time",
        )
        descriptors.append(
            _descriptor(time, kind="time", units="ps", buffer_index=len(arrays))
        )
        arrays.append(time)

    metadata = {
        "protocol_version": ARRAY_NATIVE_PROTOCOL_VERSION,
        "n_atoms": n_atoms,
        "n_structures": n_structures,
        **serialize_static_molsys_payload(molsys, n_atoms),
        "structural_arrays": descriptors,
    }
    return ArrayNativeMolSysPayload(metadata=metadata, arrays=tuple(arrays))
