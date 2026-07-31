# molsysviewer/loaders/load_molsysmt.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import molsysmt as msm
import numpy as np
import math
from smonitor.integrations import emit_from_catalog

from .._pyunitwizard import puw
from .._private.arg_digestion import digest
from .._private.smonitor import CATALOG, PACKAGE_ROOT, META

from .._private import scale_budget
from .._private.scale_budget import check_structure_scale

if TYPE_CHECKING:
    from ..viewer import MolSysView

_NM_TO_ANGSTROM = puw.conversion_factor("nm", "angstroms")


def _is_all_selector(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value == "all")


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

    # Keep original <-> loaded-system mapping only as reference/provenance.
    # Runtime state and all frontend payloads use the converted `_molsys`
    # index space directly. The two axes are independent: a mapper exists only
    # when that specific axis is a real subset.
    view._atom_index_mapper = None
    view._structure_index_mapper = None
    from ..viewer.index_mapper import IndexMapper
    if not _is_all_selector(selection):
        view._atom_index_mapper = IndexMapper(
            molecular_system,
            selection=selection,
            structure_indices="all",
            syntax=syntax,
            build_atoms=True,
            build_structures=False,
        )
    if not _is_all_selector(structure_indices):
        view._structure_index_mapper = IndexMapper(
            molecular_system,
            selection="all",
            structure_indices=structure_indices,
            syntax=syntax,
            build_atoms=False,
            build_structures=True,
        )
    view._current_structure_index = 0

    # Convert to MolSys and create the atom mask.
    view._molsys = msm.convert(
        molecular_system,
        to_form="molsysmt.MolSys",
        selection=selection,
        structure_indices=structure_indices,
        syntax=syntax,
        skip_digestion=True,
    )

    n_atoms = int(view._molsys.get_n_atoms())
    n_structures: int | None = None
    try:
        # `Structures.n_structures` is an attribute, not a getter. The previous
        # `get_n_structures()` call always raised and was swallowed here, so this
        # value silently stayed None and was only recovered later by counting the
        # serialized payload.
        n_structures = int(view._molsys.structures.n_structures)
    except Exception:
        n_structures = None
    view.atom_mask = np.ones(n_atoms, dtype=bool)

    # 1.0 materializes every selected structure, so a load large enough to
    # exhaust the browser tab must say so with numbers and a way forward rather
    # than dying silently. Warning only: the caller's machine may hold it.
    if n_structures:
        check_structure_scale(
            n_atoms,
            n_structures,
            budget_bytes=scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES,
        )

    viewer_json = view._molsys.to_form("molsysmt.ViewerJSON")

    # Extract hierarchy indices from MolSysMT to enrich the payload
    def _safe_get_atom_attribute(**kwargs):
        try:
            return msm.get(view._molsys, element="atom", skip_digestion=True, **kwargs)
        except Exception:
            return None

    molecule_indices = _safe_get_atom_attribute(molecule_index=True)
    component_indices = _safe_get_atom_attribute(component_index=True)
    molecule_names = _safe_get_atom_attribute(molecule_name=True)
    component_names = _safe_get_atom_attribute(component_name=True)
    group_types = _safe_get_atom_attribute(group_type=True)

    payload = _serialize_molsys_payload(
        viewer_json,
        molecule_indices=molecule_indices,
        component_indices=component_indices,
        molecule_names=molecule_names,
        component_names=component_names,
        group_types=group_types,
    )
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


def _serialize_molsys_payload(
    viewer_json: Any,
    molecule_indices: Any = None,
    component_indices: Any = None,
    molecule_names: Any = None,
    component_names: Any = None,
    group_types: Any = None,
) -> dict[str, Any] | None:
    """Convert MolSysMT ViewerJSON (new schema) into the MolSysPayload expected by the JS layer."""
    # Accept ViewerJSON object or plain dict.
    #
    # `to_dict()` defaults to `copy=True`, which deep-copies the whole nested
    # structure. For a 5,000-structure trajectory that is ~930,000 floats in
    # Python lists and ~2.8 s of the load, measured — 69% of it. The copy buys
    # nothing here: `viewer_json` is a fresh conversion, local to
    # `load_from_molsysmt`, read once and discarded, and everything below builds
    # a brand-new payload (`_column` and `_normalize_bonds` go through
    # `np.asarray(...).tolist()`, `_extract_structures` builds new dicts). We
    # never mutate `data`, and nothing we return aliases it.
    data: dict[str, Any]
    if hasattr(viewer_json, "to_dict"):
        try:
            data = viewer_json.to_dict(copy=False)
        except TypeError:
            # Older ViewerJSON without the `copy` keyword.
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

    def _column(values, fallback, cast, *, dtype=None):
        if values is None:
            return [fallback(i) for i in range(n_atoms)]
        try:
            array = np.asarray(values)
        except Exception:
            return [fallback(i) for i in range(n_atoms)]
        if array.ndim == 0 or array.shape[0] != n_atoms:
            return [fallback(i) for i in range(n_atoms)]

        if dtype is not None:
            try:
                if dtype is int and np.issubdtype(array.dtype, np.floating) and not bool(np.isfinite(array).all()):
                    raise ValueError("integer column contains non-finite values")
                converted = array.astype(dtype, copy=False)
                if np.issubdtype(converted.dtype, np.floating):
                    finite = np.isfinite(converted)
                    if not bool(finite.all()):
                        out = converted.tolist()
                        for i in np.flatnonzero(~finite):
                            out[int(i)] = fallback(int(i))
                        return out
                return converted.tolist()
            except Exception:
                pass

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

    atom_id = _column(atom_ids, lambda i: i + 1, int, dtype=int)
    atom_name = _column(atoms_block.get("atom_name"), lambda i: f"A{i+1}", str, dtype=str)
    # MolSysSuite exposes residues as group_*; the JS/Mol* boundary uses
    # residue_* because these fields are written into mmCIF atom_site columns
    # label_comp_id/auth_comp_id and label_seq_id/auth_seq_id. Keep this
    # translation local to the wire payload; Python APIs and JS interaction
    # events continue to expose group_* vocabulary.
    residue_id = _column(atoms_block.get("group_id"), lambda _i: 1, int, dtype=int)
    residue_name = _column(atoms_block.get("group_name"), lambda _i: "RES", str, dtype=str)
    chain_id = _column(atoms_block.get("chain_id"), lambda _i: "A", str, dtype=str)
    entity_id = _column(atoms_block.get("entity_id"), lambda _i: "1", str, dtype=str)
    element_symbol = _column(atoms_block.get("element_symbol"), lambda _i: "C", str, dtype=str)
    formal_charge = _column(atoms_block.get("formal_charge"), lambda _i: 0, int, dtype=int)

    # Hierarchy metadata from MolSysMT
    mol_id = _column(molecule_indices, lambda _i: 0, int, dtype=int)
    mol_name = _column(molecule_names, lambda _i: "Molecule", str, dtype=str)
    comp_id = _column(component_indices, lambda _i: 0, int, dtype=int)
    comp_name = _column(component_names, lambda _i: "Component", str, dtype=str)
    group_type = _column(group_types, lambda _i: "", str, dtype=str)

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
            "molecule_id": mol_id,
            "molecule_name": mol_name,
            "component_id": comp_id,
            "component_name": comp_name,
            "group_type": group_type,
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
    except Exception as exc:  # pragma: no cover - runtime guard
        emit_from_catalog(
            CATALOG["payload_invalid_coordinates"],
            package_root=PACKAGE_ROOT,
            meta=META,
            extra={"detail": f"unable to convert coordinates to ndarray: {exc}"},
        )
        return None

    if array.shape != (n_atoms, 3):
        return None

    array = array * _NM_TO_ANGSTROM
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
    except Exception as exc:
        emit_from_catalog(
            CATALOG["payload_invalid_box_vectors"],
            package_root=PACKAGE_ROOT,
            meta=META,
            extra={"detail": f"invalid box vectors in ViewerJSON: {exc}"},
        )
        return None

    if v0.shape != (3,) or v1.shape != (3,) or v2.shape != (3,):
        return None

    vectors = np.vstack([v0, v1, v2]) * _NM_TO_ANGSTROM  # nm -> Å

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
        except Exception as exc:
            emit_from_catalog(
                CATALOG["payload_invalid_bond_pairs"],
                package_root=PACKAGE_ROOT,
                meta=META,
                extra={"detail": f"invalid bond pairs: {exc}"},
            )
            return None
        if array.ndim != 2 or array.shape[1] != 2:
            return None
        index_a = array[:, 0]
        index_b = array[:, 1]
    try:
        array_a = np.asarray(index_a, dtype=int).ravel()
        array_b = np.asarray(index_b, dtype=int).ravel()
    except Exception as exc:
        emit_from_catalog(
            CATALOG["payload_invalid_bond_indices"],
            package_root=PACKAGE_ROOT,
            meta=META,
            extra={"detail": f"invalid bond indices: {exc}"},
        )
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

    bond_type = bonds.get("type")
    type_array = None
    if bond_type is not None:
        try:
            ta = np.asarray(bond_type, dtype=str).ravel()
            if ta.shape == array_a.shape:
                type_array = ta.tolist()
        except Exception:
            type_array = None

    payload = {
        "indexA": array_a.tolist(),
        "indexB": array_b.tolist(),
    }
    if order_array is not None:
        payload["order"] = order_array
    if type_array is not None:
        payload["type"] = type_array

    return payload
