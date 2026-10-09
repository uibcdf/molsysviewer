"""Native scientific interaction workflows, backed by MolSysMT.

Analyses live in ``view.molsys.interactions``; tagged visual sets reference them.
Only the visible structure is projected during live playback.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

import molsysmt as msm
import numpy as np
from depdigest import dep_digest
from smonitor import signal

from ._private.argdigest import digest
from ._private.exceptions import ArgumentError
from ._private.exceptions.interaction_analysis_error import InteractionAnalysisError
from ._private.interaction_families import FAMILIES, segments
from ._private.interaction_query_modes import QUERY_MODES
from ._pyunitwizard import puw
from .layers import SceneObject, _bounding_sphere_nm
from .scene_history import records_scene_history


def _to_plain(value):
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return _to_plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def _indices(values, size, argument, *, unique=True):
    """Validate local integer indices without lossy coercion or dense axes."""
    if isinstance(values, (bool, np.bool_)) or (
        isinstance(values, (list, tuple)) and any(isinstance(value, (bool, np.bool_)) for value in values)
    ):
        raise ArgumentError(argument, value=values)
    array = np.asarray(values)
    if array.size == 0 and array.ndim == 1:
        array = np.empty(0, dtype=np.int64)
    if array.ndim == 0:
        array = array.reshape(1)
    if array.ndim != 1 or array.dtype.kind not in "iu":
        raise ArgumentError(argument, value=values)
    if np.any(array < 0) or np.any(array >= size):
        raise ArgumentError(argument, value=values)
    if not unique:
        return array.astype(np.int64, copy=False)
    return np.fromiter(dict.fromkeys(array.tolist()), dtype=np.int64)


def _is_all(value):
    return isinstance(value, str) and value == "all"


def _require_provider():
    if not _provider_available():
        raise InteractionAnalysisError(reason="backend_required")


def _provider_available():
    return callable(getattr(getattr(msm, "Interactions", None), "between_selections", None)) and callable(
        getattr(getattr(msm, "h5msm", None), "read_layers", None)
    )


_FRAME_OCCURRENCE_LIMIT = 50000
_FRAME_BYTE_LIMIT = 8 * 1024 * 1024
_INSPECTION_BYTE_LIMIT = 512 * 1024
_DETAIL_ATOM_LIMIT = 4096
_DETAIL_PARTICIPANT_LIMIT = 64
_PROJECTION_BATCH_OCCURRENCES = 128
_PROJECTION_BATCH_ATOMS = 16384


def _projection_batches(result, data):
    """Decode bounded batches of selected occurrences, preserving row identity."""
    batch = []
    batch_atoms = 0
    for local, occurrence in enumerate(data["occurrence_indices"]):
        relation_index = int(data["relation_indices"][local])
        begin, end = result.relation_participant_offsets[relation_index : relation_index + 2]
        atom_count = int(result.participant_atom_offsets[end] - result.participant_atom_offsets[begin])
        item = None
        if end - begin <= _DETAIL_PARTICIPANT_LIMIT and atom_count <= _DETAIL_ATOM_LIMIT:
            relation = result.relation(relation_index)
            participants = relation["participants"]
            kind = relation["interaction_type"]
            pairs = segments(kind, participants)
            compound = any(len(p["atom_indices"]) != 1 for p in participants)
            if pairs is not None and (not compound or kind in {"ionic_contact", "pi_pi", "cation_pi"}):
                item = (local, occurrence, participants, kind, pairs, compound)
        retained_atoms = atom_count if item is not None else 0
        if batch and (
            len(batch) >= _PROJECTION_BATCH_OCCURRENCES or batch_atoms + retained_atoms > _PROJECTION_BATCH_ATOMS
        ):
            yield batch
            batch = []
            batch_atoms = 0
        batch.append(item)
        batch_atoms += retained_atoms
    if batch:
        yield batch


def _scope_summary(result):
    """Describe evaluated atom axes without expanding implicit all selections."""
    universe_count = (
        result.n_atoms if result.evaluation_universe_indices is None else len(result.evaluation_universe_indices)
    )
    atom_count = (
        (universe_count if result.evaluation_mode == "internal" else result.n_atoms)
        if result.evaluation_atom_indices is None
        else len(result.evaluation_atom_indices)
    )
    return {
        "mode": result.evaluation_mode,
        "atom_count": atom_count,
        "atom_count_b": None if result.evaluation_atom_indices_b is None else len(result.evaluation_atom_indices_b),
        "universe_count": universe_count,
    }


def _materialization_fits(query, result):
    """Conservative bound for the provider's current whole-selection codec.

    A public occurrence-page codec will remove the need for this fallback.
    No selected occurrence positions or private provider indexes are inspected.
    """
    count = query.n_interactions
    if count > _FRAME_OCCURRENCE_LIMIT:
        return False
    max_participants = int(np.max(np.diff(result.relation_participant_offsets), initial=0))
    evidence_width = max((len(label) for label in result.evidence_labels), default=0) * 4
    # Occurrence ids/structures/relations, evidence, measures, image offsets
    # and the maximum participant images per occurrence. Include copy overhead.
    row_bytes = 32 + evidence_width + 8 * len(result.measurements) + 12 * max_participants
    return count * row_bytes * 2 <= _FRAME_BYTE_LIMIT


def _analysis_signature(result):
    """Hash a complete public result with bounded numeric buffers.

    This identifies saved data, not their correspondence to a molecular system.
    Little-endian column bytes and sorted metadata make it machine independent.
    No dense pair matrix, full dictionary copy or per-occurrence JSON is built.
    Evidence dictionaries are canonicalized: H5MSM may remove unused labels
    and renumber codes without changing any observation's evidence.
    """
    metadata = {
        key: getattr(result, key)
        for key in (
            "n_atoms",
            "n_structures",
            "source_n_atoms",
            "source_n_structures",
            "evaluation_mode",
            "relation_types",
            "participant_roles",
            "evidence_labels",
            "measure_units",
            "method",
            "parameters",
            "source_id",
            "software",
        )
    }
    used = np.zeros(len(result.evidence_labels), dtype=bool)
    for codes in np.nditer(
        result.occurrence_evidence,
        flags=["external_loop", "buffered", "zerosize_ok"],
        op_flags=["readonly"],
        buffersize=65536,
    ):
        used[codes] = True
    labels = sorted(label for index, label in enumerate(result.evidence_labels) if used[index])
    label_codes = {label: index for index, label in enumerate(labels)}
    evidence_codes = np.asarray([label_codes.get(label, 0) for label in result.evidence_labels], dtype=np.int64)
    metadata["evidence_labels"] = labels
    hashed = hashlib.sha256(b"molsysviewer.interaction-signature.v1\0")
    hashed.update(json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    columns = {
        key: getattr(result, key)
        for key in (
            "evaluated_structure_indices",
            "atom_source_indices",
            "structure_source_indices",
            "evaluation_atom_indices",
            "evaluation_atom_indices_b",
            "evaluation_universe_indices",
            "relation_participant_offsets",
            "participant_atom_offsets",
            "participant_atoms",
            "occurrence_structures",
            "occurrence_relations",
            "occurrence_evidence",
            "occurrence_image_offsets",
            "image_vectors",
        )
    }
    columns.update({f"measurement:{name}": values for name, values in result.measurements.items()})
    for key, values in sorted(columns.items()):
        hashed.update(key.encode("utf-8") + b"\0")
        if values is None:
            hashed.update(b"null\0")
            continue
        array = np.asarray(values)
        dtype = array.dtype.newbyteorder("<")
        hashed.update(json.dumps([dtype.str, array.shape]).encode("ascii") + b"\0")
        for chunk in np.nditer(
            array,
            flags=["external_loop", "buffered", "zerosize_ok"],
            op_flags=["readonly"],
            op_dtypes=[dtype],
            order="C",
            buffersize=65536,
        ):
            if key == "occurrence_evidence":
                chunk = evidence_codes[chunk].astype(dtype, copy=False)
            hashed.update(chunk.tobytes(order="C"))
    return "sha256:" + hashed.hexdigest()


class _InteractionFamily:
    """Bind public scientific operations to one view and its named analyses."""

    def __init__(self, manager):
        self._manager = manager

    def _run(self, kind, function, arguments):
        options = dict(arguments)
        options.pop("self")
        options.pop("skip_digestion")
        return self._manager._calculate(kind, function=function, **options)


class _HBondsFamily(_InteractionFamily):
    """Named hbonds calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_hbonds(
        self,
        *,
        name: str,
        selection="all",
        selection_2=None,
        structure_indices="current",
        chemical_state="reference",
        method="baker_hubbard",
        distance_threshold=None,
        angle_threshold=None,
        selection_mode="internal",
        pbc=False,
        assume_complete_connectivity=False,
        syntax="MolSysMT",
        donor_hydrogen_pairs=None,
        acceptor_atom_indices=None,
        max_matches=100000,
        heavy_mode="auto",
        profile=None,
        skip_digestion=False,
    ):
        """Calculate ``hbonds.get_hbonds`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("hbond", "get_hbonds", locals())

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_buch_hbonds(
        self,
        *,
        name: str,
        selection="all",
        structure_indices="current",
        selection_2=None,
        distance_threshold="2.3 angstroms",
        pbc=False,
        syntax="MolSysMT",
        skip_digestion=False,
    ):
        """Calculate ``hbonds.get_buch_hbonds`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("hbond", "get_buch_hbonds", locals())

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_luzard_chandler_hbonds(
        self,
        *,
        name: str,
        selection="all",
        structure_indices="current",
        selection_2=None,
        distance_threshold="3.5 angstroms",
        angle_threshold="30 degrees",
        pbc=False,
        syntax="MolSysMT",
        skip_digestion=False,
    ):
        """Calculate ``hbonds.get_luzard_chandler_hbonds`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("hbond", "get_luzard_chandler_hbonds", locals())


class _DisulfidesFamily(_InteractionFamily):
    """Named disulfides calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_disulfide_candidates(
        self,
        *,
        name: str,
        selection="all",
        structure_indices="current",
        max_bond_length=None,
        group_names=None,
        pbc=False,
        syntax="MolSysMT",
        sorted=True,
        skip_digestion=False,
    ):
        """Calculate ``disulfides.get_disulfide_candidates`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("disulfide_candidate", "get_disulfide_candidates", locals())


class _IonicFamily(_InteractionFamily):
    """Named ionic calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_ionic_interactions(
        self,
        *,
        name: str,
        distance_threshold,
        selection="all",
        selection_2=None,
        structure_indices="current",
        chemical_state="reference",
        method="minimum_distance",
        selection_mode="internal",
        pbc=False,
        assume_complete_connectivity=False,
        syntax="MolSysMT",
        heavy_mode="auto",
        skip_digestion=False,
    ):
        """Calculate ``ionic.get_ionic_interactions`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("ionic_contact", "get_ionic_interactions", locals())


class _PiPiFamily(_InteractionFamily):
    """Named pi_pi calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_pi_pi_interactions(
        self,
        *,
        name: str,
        distance_threshold=None,
        angle_threshold=None,
        offset_threshold=None,
        planarity_threshold=None,
        selection="all",
        selection_2=None,
        structure_indices="current",
        chemical_state="reference",
        method="centroid_angle_offset",
        selection_mode="internal",
        pbc=False,
        assume_complete_connectivity=False,
        syntax="MolSysMT",
        geometry="both",
        max_cyclic_block_size=256,
        max_matches=100000,
        heavy_mode="auto",
        profile=None,
        skip_digestion=False,
    ):
        """Calculate ``pi_pi.get_pi_pi_interactions`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("pi_pi", "get_pi_pi_interactions", locals())


class _CationPiFamily(_InteractionFamily):
    """Named cation_pi calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_cation_pi_interactions(
        self,
        *,
        name: str,
        distance_threshold=None,
        angle_threshold=None,
        offset_threshold=None,
        planarity_threshold=None,
        selection="all",
        selection_2=None,
        structure_indices="current",
        chemical_state="reference",
        method="centroid_distance_angle",
        selection_mode="internal",
        pbc=False,
        assume_complete_connectivity=False,
        syntax="MolSysMT",
        max_cyclic_block_size=256,
        max_matches=100000,
        heavy_mode="auto",
        profile=None,
        skip_digestion=False,
    ):
        """Calculate ``cation_pi.get_cation_pi_interactions`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("cation_pi", "get_cation_pi_interactions", locals())


class _HalogenBondsFamily(_InteractionFamily):
    """Named halogen_bonds calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_halogen_bonds(
        self,
        *,
        name: str,
        selection="all",
        selection_2=None,
        structure_indices="current",
        chemical_state="reference",
        method="distance_two_angles",
        distance_threshold=None,
        donor_angle_range=None,
        acceptor_angle_range=None,
        selection_mode="internal",
        pbc=False,
        assume_complete_connectivity=False,
        syntax="MolSysMT",
        max_matches=100000,
        heavy_mode="auto",
        profile=None,
        skip_digestion=False,
    ):
        """Calculate ``halogen_bonds.get_halogen_bonds`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("halogen_bond", "get_halogen_bonds", locals())


class _HydrophobicFamily(_InteractionFamily):
    """Named hydrophobic calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_hydrophobic_interactions(
        self,
        *,
        name: str,
        selection="all",
        selection_2=None,
        structure_indices="current",
        chemical_state="reference",
        method="atom_pair_distance",
        distance_threshold=None,
        selection_mode="internal",
        pbc=False,
        assume_complete_connectivity=False,
        syntax="MolSysMT",
        max_matches=100000,
        heavy_mode="auto",
        profile=None,
        skip_digestion=False,
    ):
        """Calculate ``hydrophobic.get_hydrophobic_interactions`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("hydrophobic_contact", "get_hydrophobic_interactions", locals())


class _MetalCoordinationFamily(_InteractionFamily):
    """Named metal_coordination calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_metal_coordination(
        self,
        *,
        name: str,
        selection="all",
        selection_2=None,
        structure_indices="current",
        chemical_state="reference",
        method="metal_ligand_distance",
        distance_threshold=None,
        selection_mode="internal",
        pbc=False,
        assume_complete_connectivity=False,
        syntax="MolSysMT",
        max_matches=100000,
        heavy_mode="auto",
        profile=None,
        skip_digestion=False,
    ):
        """Calculate ``metal_coordination.get_metal_coordination`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("metal_coordination_candidate", "get_metal_coordination", locals())


class _WaterBridgesFamily(_InteractionFamily):
    """Named water_bridges calculations on the molecular system of the view."""

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "calculation"])
    @digest()
    def get_water_bridges(
        self,
        *,
        name: str,
        selection="all",
        selection_2=None,
        structure_indices="current",
        chemical_state="reference",
        method="hbond_water_path",
        distance_threshold=None,
        angle_threshold=None,
        selection_mode="internal",
        pbc=False,
        assume_complete_connectivity=False,
        syntax="MolSysMT",
        hbond_method="baker_hubbard",
        hbond_profile=None,
        max_matches=100000,
        heavy_mode="auto",
        profile=None,
        order=1,
        skip_digestion=False,
    ):
        """Calculate ``water_bridges.get_water_bridges`` and store its named analysis.

        Uses the view's system and, by default, its visible structure.
        Scientific defaults and validation belong to MolSysMT. The
        result is returned and attached to ``view.molsys.interactions``;
        call ``view.interactions.add(name)`` to create a visual set.
        Existing names are never overwritten. No topology is changed.
        """
        return self._run("water_bridge", "get_water_bridges", locals())


class ScientificInteractionsManager:
    """Manage named scientific analyses on the current molecular system.

    Calculation is synchronous and never triggered by playback. Its default
    is the visible structure; explicit indices or ``"all"`` request more.
    Independent attachment declares correspondence with ``assume_aligned``.
    Attached analyses are treated as immutable snapshots; direct array edits
    are outside the viewer's invalidation contract.
    """

    def __init__(self, view: Any):
        self._view = view
        self._system_revision = 0
        self._signature_cache = {}
        self._projection_revision = 0
        self.hbonds = _HBondsFamily(self)
        self.disulfides = _DisulfidesFamily(self)
        self.ionic = _IonicFamily(self)
        self.pi_pi = _PiPiFamily(self)
        self.cation_pi = _CationPiFamily(self)
        self.halogen_bonds = _HalogenBondsFamily(self)
        self.hydrophobic = _HydrophobicFamily(self)
        self.metal_coordination = _MetalCoordinationFamily(self)
        self.water_bridges = _WaterBridgesFamily(self)

    def _system(self):
        molsys = self._view.molsys
        if molsys is None:
            raise InteractionAnalysisError(reason="system_required")
        _require_provider()
        return molsys

    def _collection(self):
        if self._view.molsys is None:
            return {}
        collection = getattr(self._view.molsys, "interactions", {})
        if collection:
            _require_provider()
        return collection

    def _new_name(self, name, molsys):
        if not isinstance(name, str) or not name.strip():
            raise ArgumentError("name", value=name)
        name = name.strip()
        if name in molsys.interactions:
            raise InteractionAnalysisError(reason="name_conflict", extra={"name": name})
        return name

    def _structures(self, values, molsys):
        if values is None or _is_all(values):
            return None
        if isinstance(values, str) and values == "current":
            values = self._view.player.index
        return _indices(values, molsys.structures.n_structures, "structure_indices")

    def _atoms(self, selection, molsys, syntax):
        if _is_all(selection):
            return None
        if isinstance(selection, str):
            selection = msm.select(molsys, selection=selection, syntax=syntax)
        return _indices(selection, molsys.get_n_atoms(), "selection")

    def _publish(self, result, name, molsys, revision):
        if self._view.molsys is not molsys or revision != self._system_revision:
            raise InteractionAnalysisError(reason="stale_calculation")
        name = self._new_name(name, molsys)
        # The public setter validates full results and axis dimensions before
        # replacing its read-only named collection. Never mutate private data.
        molsys.interactions = {**molsys.interactions, name: result}
        return result

    def _check_pbc(self, molsys, structures, pbc):
        if not pbc:
            return
        boxes = msm.get(
            molsys, element="system", box=True, structure_indices="all" if structures is None else structures
        )
        if boxes is None:
            raise InteractionAnalysisError(reason="pbc_box_required")
        boxes = np.asarray(puw.get_value(boxes, to_unit="nm"), dtype=float)
        if (
            boxes.ndim != 3
            or boxes.shape[1:] != (3, 3)
            or not np.isfinite(boxes).all()
            or np.any(np.abs(np.linalg.det(boxes)) <= np.finfo(float).eps)
        ):
            raise InteractionAnalysisError(reason="pbc_box_required")

    @signal(tags=["interaction", "query"])
    @digest()
    def analyses(self, skip_digestion: bool = False) -> list[dict]:
        """Return compact metadata, without expanding occurrences or coverage."""
        return [
            {
                "name": name,
                "interaction_types": sorted(set(result.relation_types)),
                "method": result.method,
                "parameters": deepcopy(result.parameters),
                "measure_units": dict(result.measure_units),
                "software": dict(result.software),
                "source_id": result.source_id,
                "n_atoms": result.n_atoms,
                "n_structures": result.n_structures,
                "n_evaluated_structures": len(result.evaluated_structure_indices),
                "n_occurrences": result.n_interactions,
                "n_relations": len(result.relation_types),
                "evaluation_mode": result.evaluation_mode,
                "numeric_nbytes": result.numeric_nbytes,
            }
            for name, result in self._collection().items()
        ]

    @signal(tags=["interaction", "query"])
    @digest()
    def calculation_families(self, skip_digestion=False):
        """List supported calculation families advertised by this provider.

        Availability of a family does not certify its chemistry or optional
        engine for a particular system. Those checks belong to the detector.
        """
        if not _provider_available():
            return []
        advertised = set(getattr(msm.interactions, "__all__", ()))
        return [
            {"kind": kind, "label": label, "default_parameters": deepcopy(defaults)}
            for kind, (family, _, label, defaults) in FAMILIES.items()
            if family in advertised
        ]

    def _calculate(
        self,
        kind,
        *,
        function,
        name,
        selection="all",
        selection_2=None,
        structure_indices="current",
        pbc=False,
        syntax="MolSysMT",
        **parameters,
    ):
        """Coordinate axes and atomic attachment behind explicit family wrappers."""
        molsys = self._system()
        revision = self._system_revision
        name = self._new_name(name, molsys)
        if kind not in {item["kind"] for item in self.calculation_families(skip_digestion=True)}:
            raise ArgumentError("kind", value=kind, message="Unsupported calculation family for this provider.")
        if not isinstance(parameters, dict):
            raise ArgumentError("parameters", value=parameters)
        parameters = dict(parameters)
        family = FAMILIES[kind][0]
        detector = getattr(getattr(msm.interactions, family), function, None)
        if not callable(detector):
            raise InteractionAnalysisError(reason="backend_required")
        owned = {
            "molecular_system",
            "molecular_system_2",
            "selection",
            "selection_2",
            "structure_indices",
            "structure_indices_2",
            "output_type",
            "pbc",
            "syntax",
            "skip_digestion",
        }
        accepted = set(inspect.signature(detector).parameters) - owned
        if set(parameters) - accepted:
            raise ArgumentError(
                "parameters", value=parameters, message="Unknown parameters or attempted axis/output override."
            )
        structures = self._structures(structure_indices, molsys)
        self._check_pbc(molsys, structures, pbc)
        atoms = self._atoms(selection, molsys, syntax)
        options = {
            "selection": "all" if atoms is None else atoms,
            "structure_indices": "all" if structures is None else structures,
            "pbc": pbc,
            "syntax": "MolSysMT",
            "output_type": "molsysmt.Interactions",
        }
        if selection_2 is not None:
            if "selection_2" not in inspect.signature(detector).parameters:
                raise ArgumentError("selection_2", value=selection_2)
            atoms_b = self._atoms(selection_2, molsys, syntax)
            options["selection_2"] = "all" if atoms_b is None else atoms_b
        options.update(parameters)
        result = detector(molsys, **options)
        return self._publish(result, name, molsys, revision)

    @signal(tags=["interaction", "query"])
    @digest()
    def get_analysis(self, name: str, skip_digestion: bool = False):
        """Get a complete scientific result; missing names raise KeyError."""
        return self._collection()[name]

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "query"])
    @digest()
    def query(
        self,
        analysis_name: str,
        *,
        selection="all",
        selection_2=None,
        mode="involving_selection",
        exclusive=False,
        structure_indices="all",
        interaction_types=None,
        syntax="MolSysMT",
        skip_digestion=False,
    ):
        """Query sparse occurrences by atom sets and local structure indices.

        ``involving_selection`` retains any participating atom in the set;
        ``within_selection`` requires every participating atom;
        ``across_selection_boundary`` requires atoms inside and outside.
        ``between_selections`` requires disjoint sets A/B; exclusive confines all atoms
        to their union. Hydrogen and all atoms in grouped participants count.
        Query views retain provider coverage and original occurrence indices.
        """
        molsys = self._system()
        result = self.get_analysis(analysis_name, skip_digestion=True)
        if (
            not isinstance(mode, str)
            or mode not in QUERY_MODES
            or (mode == "between_selections") != (selection_2 is not None)
            or (exclusive and mode != "between_selections")
        ):
            raise InteractionAnalysisError(reason="invalid_query", extra={"mode": mode})
        structures = self._structures(structure_indices, molsys)
        atoms = self._atoms(selection, molsys, syntax)
        if mode == "between_selections":
            atoms_b = self._atoms(selection_2, molsys, syntax)
            # Two disjoint proper sets are required. An unrestricted all-axis
            # set cannot be disjoint from a nonempty second selection.
            if atoms is None:
                atoms = np.arange(molsys.get_n_atoms(), dtype=np.int64)
            if atoms_b is None:
                atoms_b = np.arange(molsys.get_n_atoms(), dtype=np.int64)
            return result.between_selections(
                atoms, atoms_b, structure_indices=structures, exclusive=exclusive, interaction_types=interaction_types
            )
        return result.query(
            structure_indices=structures, atom_indices=atoms, mode=mode, interaction_types=interaction_types
        )

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "import"])
    @digest()
    def attach(self, result, *, name: str, assume_aligned=False, skip_digestion=False):
        """Attach a complete independent result after an alignment declaration.

        Matching counts and source labels do not authenticate molecular origin.
        The caller declares matching atom/structure order, geometry and boxes.
        Name conflicts and validation errors leave the collection unchanged.
        """
        molsys = self._system()
        if not assume_aligned:
            raise InteractionAnalysisError(reason="alignment_required")
        return self._publish(result, name, molsys, self._system_revision)

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "import"])
    @digest()
    def load(
        self,
        filename,
        *,
        analysis_name: str,
        name=None,
        assume_aligned=False,
        atom_indices=None,
        structure_indices=None,
        skip_digestion=False,
    ):
        """Load one named H5MSM 0.5 analysis without replacing the view's system.

        Both complete-system and interactions-only files are supported. Optional
        indices extract/reorder source axes before attachment; they do not embed
        a subsystem into a larger target. The selected analysis is materialized
        in memory; coordinates remain those of the existing view.
        """
        molsys = self._system()
        if not assume_aligned:
            raise InteractionAnalysisError(reason="alignment_required")
        name = self._new_name(analysis_name if name is None else name, molsys)
        revision = self._system_revision
        loaded = msm.h5msm.read_layers(filename, layers=["interactions"], analysis_names=[analysis_name])
        result = (loaded.get("interactions") or {})[analysis_name]
        if atom_indices is not None or structure_indices is not None:
            # Remapping is a different operation from a query: repeated source
            # structures intentionally become distinct target structures.
            result = result.remap(
                atom_indices="all" if atom_indices is None else atom_indices,
                structure_indices="all" if structure_indices is None else structure_indices,
            )
        return self._publish(result, name, molsys, revision)

    @dep_digest("molsysmt")
    @signal(tags=["interaction", "export"])
    @digest()
    def save(self, filename, *, analysis_names=None, overwrite=False, skip_digestion=False):
        """Write complete named analyses to an interactions-only H5MSM file.

        ``analysis_names=None`` selects every stored analysis. A string selects
        one name; a nonempty list selects names in that order. Atom/structure
        domains remain those of this view; this does not save a scene or subset.
        Existing destinations are refused unless ``overwrite=True``. Provider
        serialization completes in a sibling temporary file before publication.
        """
        destination = Path(filename)
        if not isinstance(overwrite, bool):
            raise ArgumentError("overwrite", value=overwrite)
        names = (
            list(self._collection())
            if analysis_names is None
            else ([analysis_names] if isinstance(analysis_names, str) else list(analysis_names))
        )
        if (
            not names
            or any(not isinstance(name, str) or not name.strip() for name in names)
            or len(set(names)) != len(names)
        ):
            raise ArgumentError("analysis_names", value=analysis_names)
        analyses = {name: self.get_analysis(name, skip_digestion=True) for name in names}
        writer = getattr(getattr(msm, "h5msm", None), "write_layers", None)
        if not callable(writer):
            raise InteractionAnalysisError(reason="backend_required")
        if destination.exists() and not overwrite:
            raise FileExistsError(destination)
        # The provider requires a new filename. Keep it inside a private
        # sibling directory so no other writer can claim the temporary path.
        with tempfile.TemporaryDirectory(dir=destination.parent, prefix=f".{destination.name}.") as workspace:
            temporary = Path(workspace) / "analyses.h5msm"
            writer(str(temporary), interactions=analyses)
            if overwrite:
                os.replace(temporary, destination)
            else:
                # A hard link publishes a complete file without overwriting a
                # destination created by another process while we serialized.
                os.link(temporary, destination)
        return str(destination)

    @signal(tags=["interaction"])
    @digest()
    def delete_analysis(self, name: str, skip_digestion=False):
        """Delete scientific data explicitly, clearing scene undo/redo first."""
        molsys = self._system()
        self.get_analysis(name, skip_digestion=True)
        if any(
            getattr(obj, "analysis_name", None) == name
            for (kind, _), obj in self._view._scene_objects.items()
            if kind == "interaction"
        ):
            raise InteractionAnalysisError(reason="referenced_analysis", extra={"name": name})
        remaining = dict(molsys.interactions)
        del remaining[name]
        self._view.history.clear()
        self._signature_cache.clear()
        molsys.interactions = remaining
        self._view.interactions._project()

    def _system_changed(self):
        self._system_revision += 1
        self._projection_revision += 1
        self._signature_cache.clear()

    def _prepare_system_edit(self, new_molsys, policy):
        if policy == "preserve":
            return
        if policy != "invalidate":
            raise ArgumentError("interactions_policy", value=policy)
        analyses = getattr(new_molsys, "interactions", {})
        if analyses:
            # No frame/change metadata is supplied by the edit primitive.
            # Conservatively invalidate geometry-dependent observations.
            new_molsys.interactions = {
                name: result.invalidate_structures(result.evaluated_structure_indices)
                for name, result in analyses.items()
            }


class InteractionSet(SceneObject):
    """A filtered visual reference to an immutable named scientific analysis."""

    def __init__(self, view, tag, *, analysis_name, filter, layer_tag=None):
        super().__init__(view, tag, kind="interaction", layer_tag=layer_tag)
        self.analysis_name = analysis_name
        self.filter = filter
        self.style = {"color": 0x34D399, "alpha": 0.85, "radius_nm": 0.025, "radius_unit": "nm"}
        self._payload = None
        self._payload_key = None
        self._analysis_token = None
        self.analysis_revision = None

    def _refresh(self):
        self._view.interactions._project()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def show(self, skip_digestion=False):
        super().show(skip_digestion=True)
        self._refresh()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def hide(self, skip_digestion=False):
        super().hide(skip_digestion=True)
        self._refresh()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def delete(self, skip_digestion=False):
        super().delete(skip_digestion=True)
        self._view.interactions._project()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def set_tag(self, new_tag, skip_digestion=False):
        if not self._active or new_tag == self.tag:
            return
        new_tag = self._view._tag_managers["interaction"].validate(new_tag, current_tag=self.tag)
        old_tag = self.tag
        old_layer = self.layer_tag
        self._view._send({"op": "delete_layer", "kind": "interaction", "tag": old_tag})
        self.tag = new_tag
        self._view._reregister_scene_object(old_tag, new_tag, self)
        if old_layer == old_tag:
            self._view._move_or_rename_layer_group_for_object_tag_change(old_tag, new_tag, self)
            self.layer_tag = new_tag
        self._refresh()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def set_layer_tag(self, new_layer_tag, skip_digestion=False):
        super().set_layer_tag(new_layer_tag, skip_digestion=True)
        self._refresh()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def set_filter(
        self,
        *,
        selection="all",
        selection_2=None,
        mode="involving_selection",
        exclusive=False,
        structure_indices="all",
        interaction_types=None,
        syntax="MolSysMT",
        skip_digestion=False,
    ):
        next_filter = self._view.interactions._filter(
            self.analysis_name, selection, selection_2, mode, exclusive, structure_indices, interaction_types, syntax
        )
        self.filter = next_filter
        self._payload_key = None
        self.broken = False
        self._refresh()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def set_color(self, color, skip_digestion=False):
        if isinstance(color, bool) or not isinstance(color, (int, np.integer)):
            raise ArgumentError("color", value=color)
        self.style["color"] = int(color)
        self._refresh()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def set_alpha(self, alpha, skip_digestion=False):
        if not np.isfinite(alpha) or not 0 <= alpha <= 1:
            raise ArgumentError("alpha", value=alpha)
        self.style["alpha"] = float(alpha)
        self._refresh()

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def set_radius(self, radius, skip_digestion=False):
        value = float(puw.get_value(radius, to_unit="nm"))
        if not np.isfinite(value) or value <= 0:
            raise ArgumentError("radius", value=radius)
        self.style["radius_nm"] = value
        self._refresh()

    @signal(tags=["interaction", "camera"])
    @digest()
    def focus(self, skip_digestion=False):
        payload = self._view.interactions._frame(self, self._view.player.index)
        points = [point for link in payload["links"] for point in (link["start"], link["end"])]
        if not points:
            raise ValueError("This frame has no supported interaction positions to focus.")
        center, radius = _bounding_sphere_nm(points)
        self._view._send({"op": "zoom_to_position", "center": [v * 10 for v in center], "radius": (radius + 0.4) * 10})


class InteractionsManager(ScientificInteractionsManager):
    """Native scientific workflows and tagged interaction scene objects."""

    def __getitem__(self, tag):
        result = self.get(tag, skip_digestion=True)
        if result is None:
            raise KeyError(tag)
        return result

    def _objects(self):
        return [obj for (kind, _), obj in self._view._scene_objects.items() if kind == "interaction"]

    def _filter(self, name, selection, selection_2, mode, exclusive, structures, types, syntax):
        molsys = self._system()
        atoms = self._atoms(selection, molsys, syntax)
        atoms_b = None if selection_2 is None else self._atoms(selection_2, molsys, syntax)
        indices = self._structures(structures, molsys)
        result = {
            "selection": "all" if atoms is None else atoms.tolist(),
            "selection_2": "all"
            if selection_2 is not None and atoms_b is None
            else None
            if atoms_b is None
            else atoms_b.tolist(),
            "mode": mode,
            "exclusive": exclusive,
            "structure_indices": "all" if indices is None else indices.tolist(),
            "interaction_types": [types] if isinstance(types, str) else types,
        }
        self.query(name, **result, skip_digestion=True)
        return result

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def add(
        self,
        analysis_name,
        *,
        tag=None,
        selection="all",
        selection_2=None,
        mode="involving_selection",
        exclusive=False,
        structure_indices="all",
        interaction_types=None,
        syntax="MolSysMT",
        layer_tag=None,
        skip_digestion=False,
    ):
        filter = self._filter(
            analysis_name, selection, selection_2, mode, exclusive, structure_indices, interaction_types, syntax
        )
        tags = self._view._tag_managers["interaction"]
        tag = tags.allocate() if tag is None else tags.validate(tag)
        obj = InteractionSet(self._view, tag, analysis_name=analysis_name, filter=filter, layer_tag=layer_tag)
        self._view._ensure_layer_group(obj.layer_tag, kind="interaction", provenance="user" if layer_tag else "auto")
        self._view._scene_objects[("interaction", tag)] = obj
        self._project()
        return obj

    @signal(tags=["interaction", "query"])
    @digest()
    def tags(self, skip_digestion=False):
        return [obj.tag for obj in self._objects()]

    @signal(tags=["interaction", "query"])
    @digest()
    def count(self, skip_digestion=False):
        return len(self._objects())

    @signal(tags=["interaction", "query"])
    @digest()
    def contains(self, tag, skip_digestion=False):
        return self.get(tag, skip_digestion=True) is not None

    @signal(tags=["interaction", "query"])
    @digest()
    def get(self, tag, skip_digestion=False):
        return self._view._scene_objects.get(("interaction", tag))

    @signal(tags=["interaction", "query"])
    @digest()
    def records(self, skip_digestion=False):
        records = []
        for obj in self._objects():
            self._revision(obj)
            records.append(
                {
                    "tag": obj.tag,
                    "analysis_name": obj.analysis_name,
                    "analysis_revision": obj.analysis_revision,
                    "query_revision": "sha256:"
                    + hashlib.sha256(
                        json.dumps([obj.analysis_revision, obj.filter], sort_keys=True).encode("utf-8")
                    ).hexdigest(),
                    "filter": deepcopy(obj.filter),
                    "style": dict(obj.style),
                    "layer_tag": obj.layer_tag,
                    "hidden": obj._hidden,
                    "owner": obj.owner,
                    "broken": obj.broken,
                    "layer_hidden": bool(getattr(self._view.layers.get(obj.layer_tag), "_hidden", False)),
                }
            )
        return records

    @signal(tags=["interaction", "query"])
    @digest()
    def info(self, tag=None, skip_digestion=False):
        items = [
            {
                **record,
                **self._frame(self[record["tag"]], self._view.player.index),
                "projection_revision": self._projection_revision,
            }
            for record in self.records(skip_digestion=True)
        ]
        for item in items:
            item.pop("links", None)
        if tag is not None:
            match = next((item for item in items if item["tag"] == tag), None)
            if match is None:
                raise KeyError(tag)
            return match
        return items

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def delete(self, tag, skip_digestion=False):
        self[tag].delete(skip_digestion=True)

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def clear(self, tag=None, skip_digestion=False):
        for item in self.tags(skip_digestion=True) if tag is None else [tag]:
            self.delete(item, skip_digestion=True)

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def show(self, tag, skip_digestion=False):
        self[tag].show(skip_digestion=True)
        return self[tag]

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def hide(self, tag, skip_digestion=False):
        self[tag].hide(skip_digestion=True)
        return self[tag]

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def show_all(self, skip_digestion=False):
        for obj in self._objects():
            obj.show(skip_digestion=True)

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def hide_all(self, skip_digestion=False):
        for obj in self._objects():
            obj.hide(skip_digestion=True)

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def set_tag(self, tag, new_tag, skip_digestion=False):
        obj = self[tag]
        obj.set_tag(new_tag, skip_digestion=True)
        return obj

    @records_scene_history
    @signal(tags=["interaction"])
    @digest()
    def set_layer_tag(self, tag, new_layer_tag, skip_digestion=False):
        self[tag].set_layer_tag(new_layer_tag, skip_digestion=True)
        return self[tag]

    def _revision(self, obj):
        result = self._collection().get(obj.analysis_name)
        if result is None:
            obj.broken = True
            return None
        token = (id(result), self._system_revision)
        if obj._analysis_token != token:
            cache = self._signature_cache
            if token not in cache:
                cache[token] = _analysis_signature(result)
            obj.analysis_revision = cache[token]
            obj._analysis_token = token
            obj._payload_key = None
        return result

    def _participant_centers(self, groups, frame, coordinates, *, periodic):
        """Use public grouped geometry for one bounded current-frame batch.

        Periodic checks use explicit atom pairs, never a Cartesian distance
        matrix. Centers stay untranslated; each occurrence applies its images.
        The returned cache lasts only for this batch.
        """
        centers = dict.fromkeys(groups)
        valid = [members for members in groups if np.isfinite(coordinates[list(members)]).all()]
        if periodic and valid:
            pairs = [(members[0], atom) for members in valid for atom in members]
            mic = np.asarray(
                puw.get_value(
                    msm.structure.get_distances(
                        self._system(),
                        selection=pairs,
                        pairs=True,
                        structure_indices=[frame],
                        pbc=True,
                        heavy_mode="off",
                    ),
                    to_unit="nm",
                )
            ).reshape(-1)
            intact = []
            offset = 0
            for members in valid:
                direct = np.linalg.norm(coordinates[list(members)] - coordinates[members[0]], axis=1)
                if np.allclose(mic[offset : offset + len(members)], direct, rtol=1e-7, atol=1e-8):
                    intact.append(members)
                offset += len(members)
            valid = intact
        if valid:
            values = np.asarray(
                puw.get_value(
                    msm.structure.get_center(
                        self._system(),
                        selection=[list(members) for members in valid],
                        structure_indices=[frame],
                        heavy_mode="off",
                    ),
                    to_unit="nm",
                )
            ).reshape(len(valid), 3)
            centers.update(zip(valid, values))
        return centers

    def _projection_items(self, result, data, frame):
        """Prepare bounded batches lazily; read coordinates/box at most once."""
        coordinates = None
        box = None
        box_loaded = False
        periodic = data["image_vectors"] is not None
        for batch in _projection_batches(result, data):
            supported = [item for item in batch if item is not None]
            groups = dict.fromkeys(
                tuple(parts[index]["atom_indices"].tolist())
                for _, _, parts, _, pairs, _ in supported
                for index in dict.fromkeys(index for pair in pairs for index in pair)
                if len(parts[index]["atom_indices"]) > 1
            )
            if supported and coordinates is None:
                coordinates = np.asarray(
                    puw.get_value(msm.get(self._system(), coordinates=True, structure_indices=[frame]), to_unit="nm")
                )[0]
            if periodic and supported and not box_loaded:
                raw_box = msm.get(self._system(), box=True, structure_indices=[frame])
                box = None if raw_box is None else np.asarray(puw.get_value(raw_box, to_unit="nm"))[0]
                box_loaded = True
            valid_box = box is not None and np.isfinite(box).all() and abs(np.linalg.det(box)) >= np.finfo(float).eps
            centers = (
                dict.fromkeys(groups)
                if periodic and not valid_box
                else self._participant_centers(groups, frame, coordinates, periodic=periodic)
            )
            for item in batch:
                yield item, centers, coordinates, box

    def _frame(self, obj, frame):
        result = self._revision(obj)
        key = (frame, obj._analysis_token)
        if obj._payload_key == key:
            return obj._payload
        payload = {
            "frame": frame,
            "status": "unevaluated",
            "n_observations": 0,
            "n_supported": 0,
            "n_segments": 0,
            "n_skipped": 0,
            "links": [],
        }
        if result is None or obj.broken:
            payload["status"] = "broken"
        elif obj.filter["structure_indices"] != "all" and frame not in obj.filter["structure_indices"]:
            payload["status"] = "excluded"
        else:
            scope = dict(obj.filter)
            scope["structure_indices"] = [frame]
            query = self.query(obj.analysis_name, **scope, skip_digestion=True)
            if frame in result.evaluated_structure_indices:
                payload["status"] = "evaluated"
                payload["n_observations"] = query.n_interactions
                if not _materialization_fits(query, result):
                    payload["status"] = "render-limit"
                    obj._payload_key, obj._payload = key, payload
                    return payload
                data = query.to_dict()
                projected_bytes = 0
                for item, centers, coordinates, box in self._projection_items(result, data, frame):
                    if item is None:
                        payload["n_skipped"] += 1
                        continue
                    local, occurrence, participants, kind, pairs, compound = item
                    shifts = np.zeros((len(participants), 3))
                    if data["image_vectors"] is not None:
                        begin, end = data["image_offsets"][local : local + 2]
                        images = data["image_vectors"][begin:end]
                        if np.any(images) or compound:
                            if box is None:
                                payload["n_skipped"] += 1
                                continue
                            if not np.isfinite(box).all() or abs(np.linalg.det(box)) < np.finfo(float).eps:
                                payload["n_skipped"] += 1
                                continue
                            shifts = (images - images[0]) @ box
                    anchors = {}
                    for i in {index for pair in pairs for index in pair}:
                        members = participants[i]["atom_indices"]
                        if len(members) == 1:
                            anchors[i] = coordinates[members[0]] + shifts[i]
                            continue
                        member_key = tuple(members.tolist())
                        center = centers[member_key]
                        if center is None:
                            break
                        anchors[i] = center + shifts[i]
                    if len(anchors) != len({index for pair in pairs for index in pair}) or any(
                        not np.isfinite([anchors[a], anchors[b]]).all()
                        or np.linalg.norm(anchors[b] - anchors[a]) < 1e-9
                        for a, b in pairs
                    ):
                        payload["n_skipped"] += 1
                        continue
                    observation = {
                        "occurrence_index": int(occurrence),
                        # Position in this filtered frame query, not in the
                        # rendered links (unsupported geometry may be skipped).
                        "query_offset": int(local),
                        "interaction_type": kind,
                        "participants": [
                            {"role": p["role"], "atom_indices": p["atom_indices"].tolist()} for p in participants
                        ],
                        "measurements": {
                            name: float(values[local]) if np.isfinite(values[local]) else None
                            for name, values in data["measurements"].items()
                        },
                        "measure_units": data["measure_units"],
                    }
                    links = [
                        {
                            **observation,
                            "start": anchors[a].tolist(),
                            "end": anchors[b].tolist(),
                            "segment_index": segment,
                            "geometry": "participant_centroids" if compound else "atom_pair",
                        }
                        for segment, (a, b) in enumerate(pairs)
                    ]
                    projected_bytes += sum(len(json.dumps(link, allow_nan=False).encode("utf-8")) + 2 for link in links)
                    if projected_bytes > _FRAME_BYTE_LIMIT - 1024:
                        payload.update(status="render-limit", links=[], n_supported=0, n_segments=0)
                        obj._payload_key, obj._payload = key, payload
                        return payload
                    payload["links"].extend(links)
                    payload["n_supported"] += 1
                payload["n_segments"] = len(payload["links"])
                if payload["n_skipped"]:
                    payload["status"] = "partial" if payload["links"] else "unsupported"
        if len(json.dumps(payload, allow_nan=False).encode("utf-8")) > _FRAME_BYTE_LIMIT:
            payload.update(status="render-limit", links=[], n_supported=0, n_segments=0)
        obj._payload_key, obj._payload = key, payload
        return payload

    def _summary_message(self):
        analyses = self.analyses(skip_digestion=True)
        for item in analyses:
            item["n_references"] = sum(obj.analysis_name == item["name"] for obj in self._objects())
        return {
            "op": "set_interaction_summaries",
            "interactions": self.info(skip_digestion=True),
            "analyses": analyses,
            "projection_revision": self._projection_revision,
            "frame": self._view.player.index,
            "system_loaded": self._view.molsys is not None,
            "backend_available": _provider_available(),
            "calculation_families": self.calculation_families(skip_digestion=True),
        }

    def _messages(self, frame=None):
        frame = self._view.player.index if frame is None else frame
        return [
            {
                "op": "set_interaction_frame",
                **record,
                **self._frame(self[record["tag"]], frame),
                "coordinate_unit": "nm",
                "projection_revision": self._projection_revision,
            }
            for record in self.records(skip_digestion=True)
        ]

    def _project(self):
        self._projection_revision += 1
        for message in self._messages():
            self._view._send_runtime_only(message)
        self._view._send_runtime_only(self._summary_message())

    def _publish(self, result, name, molsys, revision):
        result = super()._publish(result, name, molsys, revision)
        self._project()
        return result

    @signal(tags=["interaction", "query"])
    @digest()
    def inspect(self, tag, *, structure_index=None, offset=0, limit=50, skip_digestion=False):
        if not isinstance(offset, int) or offset < 0 or not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ValueError("Inspection needs a nonnegative offset and a limit between 1 and 200.")
        obj = self[tag]
        obj._inspected_page = None
        if structure_index is not None and (
            isinstance(structure_index, (bool, np.bool_)) or not isinstance(structure_index, (int, np.integer))
        ):
            raise ArgumentError("structure_index", value=structure_index)
        frame = self._view.player.index if structure_index is None else int(structure_index)
        _indices([frame], self._system().structures.n_structures, "structure_index")
        result = self.get_analysis(obj.analysis_name, skip_digestion=True)
        self._revision(obj)
        observations = []
        scope = dict(obj.filter)
        scope["structure_indices"] = [frame]
        status = (
            "broken"
            if obj.broken
            else (
                "excluded"
                if obj.filter["structure_indices"] != "all" and frame not in obj.filter["structure_indices"]
                else "evaluated"
                if frame in result.evaluated_structure_indices
                else "unevaluated"
            )
        )
        excluded = status in {"excluded", "broken"}
        query = None if excluded else self.query(obj.analysis_name, **scope, skip_digestion=True)
        total = 0 if query is None else query.n_interactions
        pager = None if query is None else getattr(query, "to_page", None)
        limited = query is not None and not callable(pager) and not _materialization_fits(query, result)
        record = next(item for item in self.records(skip_digestion=True) if item["tag"] == tag)
        reply = {
            "tag": tag,
            "analysis_name": obj.analysis_name,
            "analysis_revision": obj.analysis_revision,
            "query_revision": record["query_revision"],
            "frame": frame,
            "status": status,
            "method": result.method,
            "parameters": deepcopy(result.parameters),
            "software": dict(result.software),
            "evaluation_scope": _scope_summary(result),
            "measure_units": dict(result.measure_units),
            "offset": offset,
            "total": total,
            "observations": [],
            "next_offset": None,
            "limit_reason": None,
        }
        metadata_bytes = len(json.dumps(_to_plain(reply), allow_nan=False).encode("utf-8"))
        if metadata_bytes > _INSPECTION_BYTE_LIMIT - 512:
            reply.update(
                status="inspection-limit",
                method=None,
                parameters={},
                software={},
                measure_units={},
                limit_reason="Inspection metadata exceeds 512 KiB; use get_analysis() to read the complete result.",
            )
            return reply
        data = None
        start = offset
        if query is not None and not limited:
            if callable(pager):
                try:
                    data = pager(offset=offset, limit=limit, max_participant_atoms=limit * _DETAIL_ATOM_LIMIT)
                except ValueError as exc:
                    if "max_participant_atoms" not in str(exc):
                        raise
                    limited = True
                start = 0
            else:
                data = query.to_dict()
        page_bytes = 0
        stop = min(len(data["occurrence_indices"]), start + limit) if data is not None else 0
        for local in range(start, stop) if data is not None else ():
            relation_index = int(data["relation_indices"][local])
            begin, end = result.relation_participant_offsets[relation_index : relation_index + 2]
            atom_begin = result.participant_atom_offsets[begin]
            atom_end = result.participant_atom_offsets[end]
            if end - begin > _DETAIL_PARTICIPANT_LIMIT or atom_end - atom_begin > _DETAIL_ATOM_LIMIT:
                limited = True
                break
            relation = result.relation(relation_index)
            images = None
            if data["image_vectors"] is not None:
                begin, end = data["image_offsets"][local : local + 2]
                images = data["image_vectors"][begin:end].tolist()
            observation = {
                "occurrence_index": int(data["occurrence_indices"][local]),
                "relation_index": int(data["relation_indices"][local]),
                "interaction_type": relation["interaction_type"],
                "participants": [
                    {"role": p["role"], "atom_indices": p["atom_indices"].tolist()} for p in relation["participants"]
                ],
                "evidence": data["evidence"][local],
                "image_vectors": images,
                "measurements": {
                    name: float(values[local]) if np.isfinite(values[local]) else None
                    for name, values in data["measurements"].items()
                },
            }
            page_bytes += len(json.dumps(observation, allow_nan=False).encode("utf-8")) + 2
            if page_bytes + metadata_bytes > _INSPECTION_BYTE_LIMIT - 512:
                limited = True
                break
            observations.append(observation)
        reply.update(
            status="inspection-limit" if limited else status,
            observations=[] if limited else observations,
            next_offset=offset + len(observations)
            if not limited and observations and offset + len(observations) < total
            else None,
            limit_reason="Narrow the filter; bounded occurrence materialization is required." if limited else None,
        )
        if not limited:
            # One detached bounded page per visual set. Inspector actions use
            # its scientific identity rather than copying a full-frame column.
            obj._inspected_page = deepcopy(reply)
        return reply

    def _inspect_picked_occurrence(self, tag, identity):
        """Resolve a graphical pick through one bounded, identity-checked page.

        The offset is a lookup hint within the current filtered frame. It never
        substitutes for the occurrence ID and both analysis/query revisions.
        """
        from collections.abc import Mapping

        if not isinstance(identity, Mapping):
            raise ArgumentError("occurrence_index", message="The pick needs an occurrence identity.")
        obj = self[tag]
        self._revision(obj)
        record = next(item for item in self.records(skip_digestion=True) if item["tag"] == tag)
        for key in ("frame", "occurrence_index", "query_offset"):
            value = identity.get(key)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 0:
                raise ArgumentError(key, value=value)
        if (
            identity["frame"] != self._view.player.index
            or identity.get("analysis_name") != obj.analysis_name
            or identity.get("analysis_revision") != record["analysis_revision"]
            or identity.get("query_revision") != record["query_revision"]
            or obj.broken
        ):
            raise ArgumentError(
                "occurrence_index", message="The pick is stale; point at the current interaction again."
            )
        page = self.inspect(
            tag,
            structure_index=int(identity["frame"]),
            offset=int(identity["query_offset"]),
            limit=1,
            skip_digestion=True,
        )
        if (
            len(page["observations"]) != 1
            or page["observations"][0]["occurrence_index"] != identity["occurrence_index"]
        ):
            obj._inspected_page = None
            raise ArgumentError("occurrence_index", message="The picked occurrence is absent from this query position.")
        self._observation_atoms(
            tag, identity["occurrence_index"], page["frame"], page["analysis_revision"], page["query_revision"]
        )
        return page

    def _observation_atoms(self, tag, occurrence_index, structure_index, analysis_revision, query_revision):
        obj = self[tag]
        self._revision(obj)
        record = next(item for item in self.records(skip_digestion=True) if item["tag"] == tag)
        frame = int(_indices([structure_index], self._system().structures.n_structures, "structure_index")[0])
        if (
            frame != self._view.player.index
            or analysis_revision != record["analysis_revision"]
            or query_revision != record["query_revision"]
            or obj.broken
        ):
            raise ArgumentError(
                "occurrence_index",
                value=occurrence_index,
                message="Observation identity is stale; inspect the current frame again.",
            )
        if obj.filter["structure_indices"] != "all" and frame not in obj.filter["structure_indices"]:
            raise ArgumentError("structure_index", value=structure_index)
        if (
            isinstance(occurrence_index, (bool, np.bool_))
            or not isinstance(occurrence_index, (int, np.integer))
            or occurrence_index < 0
        ):
            raise ArgumentError("occurrence_index", value=occurrence_index)
        page = getattr(obj, "_inspected_page", None)
        if (
            page is None
            or page["frame"] != frame
            or page["analysis_revision"] != analysis_revision
            or page["query_revision"] != query_revision
        ):
            raise ArgumentError(
                "occurrence_index",
                value=occurrence_index,
                message="Inspect the current observation page before acting.",
            )
        observation = next(
            (item for item in page["observations"] if item["occurrence_index"] == occurrence_index), None
        )
        if observation is None:
            raise ArgumentError(
                "occurrence_index",
                value=occurrence_index,
                message="Occurrence is absent from the latest inspected page.",
            )
        return sorted(
            {int(atom) for participant in observation["participants"] for atom in participant["atom_indices"]}
        )

    @signal(tags=["interaction", "selection"])
    @digest()
    def select_observation(
        self, tag, occurrence_index, *, structure_index, analysis_revision, query_revision, skip_digestion=False
    ):
        """Activate every participant atom of a current inspected observation.

        Supply frame/revisions from the latest ``inspect`` page. Stale or filtered identities
        raise before changing selection. Compound participants retain all atoms.
        """
        atoms = self._observation_atoms(tag, occurrence_index, structure_index, analysis_revision, query_revision)
        self._view.active_selection.set(atoms, skip_digestion=True)
        return atoms

    @signal(tags=["interaction", "camera"])
    @digest()
    def focus_observation(
        self, tag, occurrence_index, *, structure_index, analysis_revision, query_revision, skip_digestion=False
    ):
        """Focus canonical system positions of a current observation's atoms.

        Uses the existing camera selection operation; this does not unwrap
        compound participants or alter the analysis's periodic images.
        """
        atoms = self._observation_atoms(tag, occurrence_index, structure_index, analysis_revision, query_revision)
        self._view.focus_selection(atoms, structure_indices=[structure_index], skip_digestion=True)

    def _static_messages(self):
        # Explicit bounded export: never silently drop occurrences or frames.
        messages = []
        size = 0
        for record in self.records(skip_digestion=True):
            obj = self[record["tag"]]
            frames = []
            for frame in range(self._system().structures.n_structures):
                payload = deepcopy(self._frame(obj, frame))
                size += len(json.dumps(payload, allow_nan=False).encode("utf-8"))
                if size > 64 * 1024 * 1024:
                    raise ValueError(
                        "Interaction HTML projection exceeds 64 MiB. Reduce visual filters before exporting."
                    )
                frames.append(payload)
            messages.append({"op": "set_interaction_series", **record, "coordinate_unit": "nm", "frames": frames})
        return messages
