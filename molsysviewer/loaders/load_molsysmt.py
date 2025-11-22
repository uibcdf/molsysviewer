# molsysviewer/loaders/load_molsysmt.py

from __future__ import annotations

import logging
from typing import Any

import molsysmt as msm
import numpy as np

logger = logging.getLogger(__name__)


def load_from_molsysmt(
    view: Any,
    *,
    molecular_system: Any,
    selection: str | Any = "all",
    structure_indices: str | Any = "all",
    syntax: str = "MolSysMT",
    label: str | None = None,
) -> None:
    """Backend interno para MolSysView.load(...).

    - Convierte cualquier `molecular_system` a MolSysMT.MolSys.
    - Inicializa la máscara de átomos.
    - Intenta el camino nativo (payload MolSysMT → Mol*).
    - Si falla, hace fallback a PDB string.
    """

    # Guardar en el estado del viewer
    view.molecular_system = molecular_system
    view.selection = selection
    view.structure_indices = structure_indices

    # Convertir a MolSys y crear máscara
    view._molsys = msm.convert(
        molecular_system,
        to_form="molsysmt.MolSys",
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
    )
    n_atoms = msm.get(view._molsys, element="atom", n_atoms=True)
    view.atom_mask = np.ones(n_atoms, dtype=bool)

    # Intentar camino nativo MolSysMT -> payload Mol* (vía ViewerJSON)
    try:
        payload = _serialize_molsys_payload(view._molsys)
    except Exception as exc:  # pragma: no cover - defensive, MolSysMT internals
        logger.debug("MolSys payload serialization failed: %s", exc, exc_info=True)
        payload = None

    if payload is not None:
        # Enviar payload al frontend
        _load_molsys_payload(view, payload, label=label)
        return

    # Fallback: PDB string
    pdb_string = msm.convert(view._molsys, to_form="string:pdb")
    view._send(
        {
            "op": "load_structure_from_string",
            "format": "pdb",
            "data": pdb_string,
            "label": label,
        }
    )


# ---------------------------------------------------------------------------
#  Infraestructura de serialización MolSysMT -> payload para Mol*
# ---------------------------------------------------------------------------

def _serialize_molsys_payload(molsys: Any) -> dict[str, Any] | None:
    """Convierte un MolSysMT.MolSys en el payload esperado por el frontend usando ViewerJSON."""
    viewer_json = _molsys_to_viewer_json(molsys)
    if viewer_json is None:
        return None
    return _viewer_json_to_payload(viewer_json)


def _first_available(candidates: list[Any | None]) -> Any | None:
    for candidate in candidates:
        if candidate is not None:
            return candidate
    return None


def _prepare_atom_field(values: Any | None, length: int, fallback) -> list[Any]:
    if values is None:
        return [fallback(i) for i in range(length)]
    array = np.asarray(values)
    if array.shape[0] != length:
        return [fallback(i) for i in range(length)]
    return array.tolist()


def _molsys_to_viewer_json(molsys: Any) -> dict[str, Any] | None:
    try:
        viewer = msm.convert(molsys, to_form="molsysmt.ViewerJSON")
    except Exception:  # pragma: no cover - defensive
        logger.debug("MolSys payload: convert to ViewerJSON failed", exc_info=True)
        return None

    if hasattr(viewer, "to_dict"):
        try:
            return viewer.to_dict()
        except Exception:  # pragma: no cover
            logger.debug("MolSys payload: ViewerJSON.to_dict() failed", exc_info=True)
            return None

    if isinstance(viewer, dict):
        return viewer

    logger.debug("MolSys payload: unexpected ViewerJSON type %s", type(viewer))
    return None


def _viewer_json_to_payload(viewer_json: dict[str, Any]) -> dict[str, Any] | None:
    atoms_block = viewer_json.get("atoms") or {}
    atom_ids = atoms_block.get("atom_id")
    n_atoms = len(atom_ids) if atom_ids is not None else 0
    if n_atoms == 0:
        return None

    atom_names = _prepare_atom_field(atoms_block.get("atom_name"), n_atoms, lambda i: f"A{i + 1}")
    residue_ids = _prepare_atom_field(
        _first_available(
            [
                atoms_block.get("residue_id"),
                atoms_block.get("group_id"),
                atoms_block.get("group_ig"),  # typo fallback in schema
                atoms_block.get("component_id"),
            ]
        ),
        n_atoms,
        lambda _i: 1,
    )
    residue_names = _prepare_atom_field(
        _first_available(
            [
                atoms_block.get("residue_name"),
                atoms_block.get("group_name"),
                atoms_block.get("component_name"),
            ]
        ),
        n_atoms,
        lambda _i: "RES",
    )
    chain_ids = _prepare_atom_field(atoms_block.get("chain_id"), n_atoms, lambda _i: "A")
    entity_ids = _prepare_atom_field(
        _first_available([atoms_block.get("entity_id"), atoms_block.get("molecule_id")]),
        n_atoms,
        lambda _i: "1",
    )
    element_symbols = _prepare_atom_field(
        _first_available([atoms_block.get("element_symbol"), atoms_block.get("atom_type")]),
        n_atoms,
        lambda _i: "C",
    )
    formal_charges = _prepare_atom_field(atoms_block.get("formal_charge"), n_atoms, lambda _i: 0)

    coordinates_payload = _extract_frames(viewer_json.get("frames") or viewer_json.get("coordinates"), n_atoms)
    if not coordinates_payload:
        return None

    bonds_payload = _normalize_bonds(viewer_json.get("bonds"))

    payload: dict[str, Any] = {
        "atoms": {
            "atom_id": _prepare_atom_field(atom_ids, n_atoms, lambda i: i + 1),
            "atom_name": atom_names,
            "residue_id": residue_ids,
            "residue_name": residue_names,
            "chain_id": chain_ids,
            "entity_id": entity_ids,
            "element_symbol": element_symbols,
            "formal_charge": formal_charges,
        },
        "coordinates": coordinates_payload,
    }
    if bonds_payload is not None:
        payload["bonds"] = bonds_payload

    return payload


def _extract_frames(frames: Any, n_atoms: int) -> list[dict[str, Any]]:
    if not isinstance(frames, list):
        return []

    payload_frames: list[dict[str, Any]] = []
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            continue

        positions = _positions_to_angstroms(frame.get("positions"), n_atoms)
        if positions is None:
            continue

        frame_payload: dict[str, Any] = {
            "positions": positions,
            "time": frame.get("time", index),
        }

        cell = _cell_to_angstroms(frame.get("cell"))
        if cell is not None:
            frame_payload["cell"] = cell

        payload_frames.append(frame_payload)

    return payload_frames


def _positions_to_angstroms(positions: Any, n_atoms: int) -> list[list[float]] | None:
    try:
        array = np.asarray(positions, dtype=float)
    except Exception:  # pragma: no cover - runtime guard
        logger.debug("MolSys payload: unable to convert positions to ndarray", exc_info=True)
        return None

    if array.shape != (n_atoms, 3):
        return None

    # ViewerJSON usa nanómetros; el viewer espera Å.
    return (array * 10.0).tolist()


def _cell_to_angstroms(cell: Any) -> dict[str, float] | None:
    if not isinstance(cell, dict):
        return None
    try:
        a = float(cell["a"]) * 10.0
        b = float(cell["b"]) * 10.0
        c = float(cell["c"]) * 10.0
        alpha = float(cell["alpha"])
        beta = float(cell["beta"])
        gamma = float(cell["gamma"])
    except Exception:
        logger.debug("MolSys payload: invalid cell in ViewerJSON", exc_info=True)
        return None
    return {
        "a": a,
        "b": b,
        "c": c,
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
    }


def _normalize_bonds(bonds: Any) -> dict[str, Any] | None:
    if not isinstance(bonds, dict):
        return None

    index_a = bonds.get("indexA")
    index_b = bonds.get("indexB")
    if index_a is None or index_b is None:
        return None

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
            order_array = np.asarray(order, dtype=int).ravel()
        except Exception:
            order_array = None

    payload = {
        "indexA": array_a.tolist(),
        "indexB": array_b.tolist(),
    }
    if order_array is not None and order_array.shape == array_a.shape:
        payload["order"] = order_array.tolist()

    return payload


def _load_molsys_payload(
    view: Any,
    payload: dict[str, Any],
    *,
    label: str | None = None,
) -> None:
    """Enviar un payload ya construido al frontend."""
    view._send(
        {
            "op": "load_molsys_payload",
            "payload": payload,
            "label": label,
        }
    )
