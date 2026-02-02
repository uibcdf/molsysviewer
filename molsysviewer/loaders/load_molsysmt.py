# molsysviewer/loaders/load_molsysmt.py

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import molsysmt as msm
import numpy as np
import math

from .._private.digestion import digest

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..viewer import MolSysView


def ensure_view(view: "MolSysView" | None = None) -> "MolSysView":
    if view is None:
        from ..viewer import MolSysView
        view = MolSysView()
    return view


@digest()
def load_from_molsysmt(
    molecular_system: Any,
    *,
    selection: str | Any = "all",
    structure_indices: str | Any = "all",
    syntax: str = "MolSysMT",
    label: str | None = None,
    view: "MolSysView | None" = None,
    skip_digestion: bool = False,
) -> "MolSysView":
    """Internal backend for `MolSysView.load(...)`.

    - Convert `molecular_system` into `molsysmt.MolSys`.
    - Initialize the atom mask.
    - Use the native path (MolSys payload → Mol*).
    """

    view = ensure_view(view)

    # Store the digested inputs on the viewer instance.
    view.molecular_system = molecular_system
    view.selection = selection
    view.structure_indices = structure_indices

    # Convert to MolSys and create the atom mask.
    view._molsys = msm.convert(
        molecular_system,
        to_form="molsysmt.MolSys",
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=True,
    )

    try:
        n_atoms = int(view._molsys.topology.get_n_atoms())
    except Exception:
        if hasattr(view._molsys, "get"):
            n_atoms = int(view._molsys.get(element="atom", n_atoms=True))  # type: ignore[call-arg]
        else:
            n_atoms = int(msm.get(view._molsys, element="atom", n_atoms=True, skip_digestion=True))
    n_structures: int | None = None
    try:
        n_structures = int(view._molsys.structures.get_n_structures())
    except Exception:
        n_structures = None
    view.atom_mask = np.ones(n_atoms, dtype=bool)

    viewer_json = view._molsys.to_form("molsysmt.ViewerJSON")

    payload = _serialize_molsys_payload(viewer_json)
    if payload is None:
        raise ValueError("Unable to serialize MolSysMT viewer payload")
    if n_structures is None:
        n_structures = len(payload.get("structures") or [])
    multiple_structures = n_structures > 1

    view._send(
        {
            "op": "load_molsys_payload",
            "payload": payload,
            "label": label,
            "multiple_structures": multiple_structures,
        }
    )

    return view


def _serialize_molsys_payload(viewer_json: Any) -> dict[str, Any] | None:
    """Convert MolSysMT ViewerJSON (new schema) into the MolSysPayload expected by the JS layer."""
    # Accept ViewerJSON object or plain dict
    data: dict[str, Any]
    if hasattr(viewer_json, "to_dict"):
        data = viewer_json.to_dict()
    else:
        data = dict(viewer_json)

    atoms_block = data.get("atoms") or {}
    bonds_block = data.get("bonds") or {}
    structures = data.get("structures") or []

    atom_ids = atoms_block.get("atom_id") or []
    n_atoms = len(atom_ids)
    if n_atoms == 0 or not structures:
        return None

    def _column(values, fallback, cast):
        if values is None:
            return [fallback(i) for i in range(n_atoms)]
        try:
            array = np.asarray(values)
        except Exception:
            return [fallback(i) for i in range(n_atoms)]
        if array.ndim == 0 or array.shape[0] != n_atoms:
            return [fallback(i) for i in range(n_atoms)]
        out: list[Any] = []
        for i, v in enumerate(array.tolist()):
            try:
                val = cast(v)
                if isinstance(val, float) and not math.isfinite(val):
                    val = fallback(i)
            except Exception:
                val = fallback(i)
            out.append(val)
        return out

    atom_id = _column(atom_ids, lambda i: i + 1, int)
    atom_name = _column(atoms_block.get("atom_name"), lambda i: f"A{i+1}", str)
    residue_id = _column(atoms_block.get("group_id"), lambda _i: 1, int)
    residue_name = _column(atoms_block.get("group_name"), lambda _i: "RES", str)
    chain_id = _column(atoms_block.get("chain_id"), lambda _i: "A", str)
    entity_id = _column(atoms_block.get("entity_id"), lambda _i: "1", str)
    element_symbol = _column(atoms_block.get("element_symbol"), lambda _i: "C", str)
    formal_charge = _column(atoms_block.get("formal_charge"), lambda _i: 0, int)

    structures_payload = _extract_structures(structures, n_atoms)
    if not structures_payload:
        return None

    bonds_payload = _normalize_bonds(bonds_block)

    payload: dict[str, Any] = {
        "atoms": {
            "atom_id": atom_id,
            "atom_name": atom_name,
            "residue_id": residue_id,
            "residue_name": residue_name,
            "chain_id": chain_id,
            "entity_id": entity_id,
            "element_symbol": element_symbol,
            "formal_charge": formal_charge,
        },
        "structures": structures_payload,
    }
    if bonds_payload is not None:
        payload["bonds"] = bonds_payload

    return payload


def _extract_structures(structures: Any, n_atoms: int) -> list[dict[str, Any]]:
    if not isinstance(structures, list):
        return []

    payload_frames: list[dict[str, Any]] = []
    for index, structure in enumerate(structures):
        if not isinstance(structure, dict):
            continue

        coords = _positions_to_angstroms(structure.get("coordinates"), n_atoms)
        if coords is None:
            continue

        frame_payload: dict[str, Any] = {
            "coordinates": coords,
            "time": structure.get("time", index),
        }

        # Box information is optional; omit if invalid to avoid Mol* issues
        box = _box_vectors(structure.get("box"))
        if box is not None:
            frame_payload["box"] = box

        payload_frames.append(frame_payload)

    return payload_frames


def _positions_to_angstroms(positions: Any, n_atoms: int) -> list[list[float]] | None:
    try:
        array = np.asarray(positions, dtype=float)
    except Exception:  # pragma: no cover - runtime guard
        logger.debug("MolSys payload: unable to convert coordinates to ndarray", exc_info=True)
        return None

    if array.shape != (n_atoms, 3):
        return None

    array = array * 10.0
    if not np.isfinite(array).all():
        return None
    return array.tolist()


def _box_vectors(box: Any) -> list[list[float]] | None:
    """Convert ViewerJSON box vectors (nm) to Å for Mol*."""
    if not isinstance(box, dict):
        return None

    try:
        v0 = np.asarray(box["v0"], dtype=float)
        v1 = np.asarray(box["v1"], dtype=float)
        v2 = np.asarray(box["v2"], dtype=float)
    except Exception:
        logger.debug("MolSys payload: invalid box vectors in ViewerJSON", exc_info=True)
        return None

    if v0.shape != (3,) or v1.shape != (3,) or v2.shape != (3,):
        return None

    vectors = np.vstack([v0, v1, v2]) * 10.0  # nm -> Å

    norms = np.linalg.norm(vectors, axis=1)
    if np.any(norms < 1e-6):
        return None
    volume = np.dot(vectors[0], np.cross(vectors[1], vectors[2]))
    if abs(volume) < 1e-6:
        return None

    return vectors.tolist()


def _normalize_bonds(bonds: Any) -> dict[str, Any] | None:
    if not isinstance(bonds, dict):
        return None

    # Prefer explicit indexA/indexB if present
    index_a = bonds.get("indexA")
    index_b = bonds.get("indexB")

    if index_a is None or index_b is None:
        # Fallback to atom_pairs [[a,b], ...]
        pairs = bonds.get("atom_pairs")
        if not isinstance(pairs, list) or len(pairs) == 0:
            return None
        try:
            array = np.asarray(pairs, dtype=int)
        except Exception:
            logger.debug("MolSys payload: invalid bond pairs", exc_info=True)
            return None
        if array.ndim != 2 or array.shape[1] != 2:
            return None
        index_a = array[:, 0]
        index_b = array[:, 1]
    try:
        array_a = np.asarray(index_a, dtype=int).ravel()
        array_b = np.asarray(index_b, dtype=int).ravel()
    except Exception:
        logger.debug("MolSys payload: invalid bond indices", exc_info=True)
        return None

    if array_a.shape != array_b.shape or array_a.ndim != 1:
        return None

    order = bonds.get("order")
    order_array = None
    if order is not None:
        try:
            oa = np.asarray(order, dtype=int).ravel()
            if oa.shape == array_a.shape:
                order_array = oa.tolist()
        except Exception:
            order_array = None

    payload = {
        "indexA": array_a.tolist(),
        "indexB": array_b.tolist(),
    }
    if order_array is not None:
        payload["order"] = order_array

    return payload
