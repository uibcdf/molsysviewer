"""Prepare independent inputs for the public load operation, before scene mutation.

Scientific conversion/addition belongs to MolSysMT. This module owns Viewer
input intent, compact source correspondence and composition preconditions.
"""

from numbers import Integral
from uuid import uuid4

import molsysmt as msm
import numpy as np

from .._pyunitwizard import puw
from .load_molsysmt import _prepare_molsysmt_load


def _per_source_selectors(value, count, name):
    if isinstance(value, (list, tuple, np.ndarray)):
        if any(isinstance(item, (str, list, tuple, np.ndarray, range)) for item in value):
            if len(value) != count:
                raise ValueError(f"{name} must contain one selector per source.")
            return list(value)
    return [value] * count


def _index_selector(value, name):
    if value is None or isinstance(value, str) and value == "all":
        return "all"
    values = [value] if isinstance(value, Integral) else list(value)
    if not values or any(
        isinstance(i, (bool, np.bool_)) or not isinstance(i, Integral) or i < 0 or i > np.iinfo(np.int64).max
        for i in values
    ):
        raise ValueError(f"{name} must contain nonnegative integer indices.")
    return np.asarray(values, dtype=np.int64)


def _index_runs(indices, offset=0):
    """Encode ordered source/current index pairs as [source, current, length] runs."""
    if isinstance(indices, range) and indices.step == 1:
        return [[indices.start, int(offset), len(indices)]] if indices else []
    runs = []
    for current, source in enumerate(indices, start=offset):
        source = int(source)
        if runs and runs[-1][0] + runs[-1][2] == source and runs[-1][1] + runs[-1][2] == current:
            runs[-1][2] += 1
        else:
            runs.append([source, int(current), 1])
    return runs


def _origin(source):
    form = msm.get_form(source)
    reference = source if isinstance(source, str) and "\n" not in source and len(source) <= 2048 else None
    if isinstance(source, (list, tuple)):
        return {"form": form, "items": [_origin(item) for item in source]}
    return {"form": form, "reference": reference}


def _load_record(molsys, *, index=0, offset=0, label=None, origin=None, atoms=None, structures=None):
    count = int(molsys.get_n_atoms())
    frames = int(molsys.structures.n_structures)
    return {
        "index": int(index),
        "label": label.strip() if isinstance(label, str) and label.strip() else None,
        "n_atoms": count,
        "start": int(offset),
        "stop": int(offset) + count,
        "source_id": uuid4().hex,
        "origin": origin or {"form": "molsysmt.MolSys", "reference": None},
        "atom_map": {"encoding": "runs", "runs": _index_runs(range(count) if atoms is None else atoms, offset)},
        "structure_map": {"encoding": "runs", "runs": _index_runs(range(frames) if structures is None else structures)},
        "region_tag": None,
        "region_uid": None,
    }


def _validate_renderable(molsys):
    count = int(molsys.get_n_atoms())
    frames = int(molsys.structures.n_structures)
    quantity = molsys.structures.coordinates
    if count <= 0 or frames <= 0 or quantity is None:
        raise ValueError("Loading requires a nonempty atom selection with structural coordinates.")
    values = np.asarray(puw.get_value(quantity, to_unit="nm"))
    if values.shape != (frames, count, 3) or not np.isfinite(values).all():
        raise ValueError("Loaded coordinates must be finite and cover every selected atom and structure.")
    for name, unit, shape in (("box", "nm", (frames, 3, 3)), ("time", "ps", (frames,))):
        quantity = getattr(molsys.structures, name)
        if quantity is not None:
            values = np.asarray(puw.get_value(quantity, to_unit=unit))
            if values.shape != shape or not np.isfinite(values).all():
                raise ValueError(f"Loaded {name} must be finite and cover every selected structure.")


def _prepare_source(source, *, selection, structure_indices, syntax, label, index, offset):
    from .._private.argdigest.argument.molecular_system import _normalize_paths

    source = _normalize_paths(source)
    if not isinstance(selection, str) and selection is not None:
        selection = _index_selector(selection, "selection")
    structures = _index_selector(structure_indices, "structure_indices")
    if not isinstance(structures, str):
        count = int(msm.get(source, n_structures=True, skip_digestion=True))
        if np.any(structures >= count):
            raise ValueError("structure_indices exceeds the source structure count.")
    prepared = _prepare_molsysmt_load(source, selection=selection, structure_indices=structures, syntax=syntax)
    converted, _, _, _, atom_mapper, structure_mapper = prepared
    _validate_renderable(converted)
    if any(mapper is not None and mapper.degraded for mapper in (atom_mapper, structure_mapper)):
        raise ValueError("Cannot record a source load with degraded index correspondence.")
    atoms = None if atom_mapper is None else atom_mapper.original_atoms
    frames = None if structure_mapper is None else structure_mapper.original_structures
    if atoms is not None and len(atoms) != int(converted.get_n_atoms()):
        raise ValueError("Source atom correspondence does not match the converted system.")
    if frames is not None and len(frames) != int(converted.structures.n_structures):
        raise ValueError("Source structure correspondence does not match the converted system.")
    record = _load_record(
        converted, index=index, offset=offset, label=label, origin=_origin(source), atoms=atoms, structures=frames
    )
    return prepared, record


def _validate_pairing(target, incoming, pairing):
    frames = int(target.structures.n_structures)
    if frames != int(incoming.structures.n_structures):
        raise ValueError(
            "Sources must have the same number of selected structures; static broadcasting is not implicit."
        )
    if frames > 1 and pairing != "by_index":
        raise ValueError("Combining trajectories requires structure_pairing='by_index'.")
    left, right = target.structures.time, incoming.structures.time
    if left is not None and right is not None:
        # Input compatibility, not inferred physical synchronization. Tolerance
        # only permits floating roundoff after explicit unit normalization.
        if not np.allclose(puw.get_value(left, to_unit="ps"), puw.get_value(right, to_unit="ps"), rtol=1e-9, atol=1e-9):
            raise ValueError("Selected source times do not match the destination time axis.")


def _compose_sources(target, prepared_sources, pairing):
    """Build a detached candidate; never pass the active MolSys to mutating add."""
    composing = target is not None or len(prepared_sources) > 1
    if composing and any(getattr(source[0], "interactions", {}) for source in prepared_sources):
        raise ValueError("Adding sources with named interaction analyses requires an explicit analysis-merge policy.")
    systems = [source[0] for source in prepared_sources]
    reference = target if target is not None else systems[0]
    _validate_renderable(reference)
    for system in systems if target is not None else systems[1:]:
        _validate_pairing(reference, system, pairing)
    if target is None:
        candidate, systems = systems[0], systems[1:]
    else:
        candidate = msm.copy(target, skip_digestion=True)
    for system in systems:
        msm.add(candidate, system, keep_ids=True, in_place=True, skip_digestion=True)
    _validate_renderable(candidate)
    # Scene export and history need public atom identities as well as coordinates.
    # Read them on the detached candidate before any active-system mutation.
    from ..viewer.state import _structure_identity

    try:
        _structure_identity(candidate)
    except Exception as error:
        raise ValueError(
            "Prepared molecular system cannot provide the atom identities required for scene state."
        ) from error
    return candidate
