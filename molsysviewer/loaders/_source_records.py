"""Compact source correspondence, validation and explicit transfer operations."""

import hashlib
import json
from bisect import bisect_right
from copy import deepcopy
from numbers import Integral

import numpy as np

from .._pyunitwizard import puw


def _coalesce_runs(runs):
    result = []
    for source, current, length in sorted(runs, key=lambda run: run[1]):
        if result and result[-1][0] + result[-1][2] == source and result[-1][1] + result[-1][2] == current:
            result[-1][2] += length
        else:
            result.append([int(source), int(current), int(length)])
    return result


def _remap_runs(runs, correspondence):
    """Visit selected indices, rather than expand all source indices."""
    if correspondence is None:
        return deepcopy(runs)
    ordered = sorted(runs, key=lambda run: run[1])
    starts = [run[1] for run in ordered]
    remapped = []
    for old, destinations in correspondence.items():
        index = bisect_right(starts, old) - 1
        if index < 0:
            continue
        source, current, length = ordered[index]
        if old >= current + length:
            continue
        for new in destinations:
            remapped.append([source + old - current, new, 1])
    return _coalesce_runs(remapped)


def _record_atom_runs(record, runs):
    record["atom_map"] = {"encoding": "runs", "runs": runs}
    record["n_atoms"] = sum(run[2] for run in runs)
    record["start"] = min((run[1] for run in runs), default=0)
    record["stop"] = max((run[1] + run[2] for run in runs), default=0)


def _remap_source_records(records, atom_map=None, frames=None):
    atoms = None if atom_map is None else {old: [new] for old, new in atom_map.items()}
    structures = None
    if frames is not None:
        structures = {}
        for new, old in enumerate(frames):
            structures.setdefault(int(old), []).append(new)
    result = []
    for original in records:
        record = deepcopy(original)
        _record_atom_runs(record, _remap_runs(record["atom_map"]["runs"], atoms))
        if not record["n_atoms"]:
            continue
        record["structure_map"]["runs"] = _remap_runs(record["structure_map"]["runs"], structures)
        record["index"] = len(result)
        result.append(record)
    return result


def _source_atom_indices(record):
    return [index for _, start, length in record["atom_map"]["runs"] for index in range(start, start + length)]


def _uncovered_atom_runs(records, count):
    intervals = sorted((start, start + length) for record in records for _, start, length in record["atom_map"]["runs"])
    cursor = 0
    missing = []
    for start, stop in intervals:
        if start > cursor:
            missing.append([cursor, cursor, start - cursor])
        cursor = max(cursor, stop)
    if cursor < count:
        missing.append([cursor, cursor, count - cursor])
    return missing


def _source_binding(molsys, identity):
    """Hash the ordered system in bounded chunks; callers cache the result.

    This verifies content/index correspondence, not the claimed file's origin.
    The structural scene fingerprint remains independently topological.
    """
    digest = hashlib.sha256()
    digest.update(json.dumps(identity, sort_keys=True).encode())
    count = int(molsys.get_n_atoms())
    frames = int(molsys.structures.n_structures)
    digest.update(json.dumps([count, frames]).encode())
    for name, unit in (("coordinates", "nm"), ("time", "ps"), ("box", "nm")):
        quantity = getattr(molsys.structures, name)
        digest.update(name.encode())
        if quantity is None:
            digest.update(b"none")
            continue
        values = np.asarray(puw.get_value(quantity, to_unit=unit))
        digest.update(json.dumps(values.shape).encode())
        for start in range(0, values.size, 65536):
            chunk = np.asarray(values.flat[start : start + 65536], dtype="<f8")
            # -0.0 and +0.0 describe the same submitted coordinates.
            chunk[chunk == 0] = 0
            digest.update(chunk.tobytes())
    return {"n_atoms": count, "n_structures": frames, "fingerprint": "sha256:" + digest.hexdigest()}


def _validate_source_state(state):
    """Validate intervals without allocating dense atom/structure lookup arrays."""
    if (
        not isinstance(state, dict)
        or not isinstance(state.get("version"), int)
        or isinstance(state["version"], bool)
        or state["version"] != 1
    ):
        raise ValueError("Unsupported source-record state version.")
    binding = state.get("binding")

    def integer(value):
        return isinstance(value, Integral) and not isinstance(value, (bool, np.bool_))

    if (
        not isinstance(binding, dict)
        or any(
            not integer(binding.get(key)) or not 0 <= binding[key] <= np.iinfo(np.int64).max
            for key in ("n_atoms", "n_structures")
        )
        or not isinstance(binding.get("fingerprint"), str)
        or len(binding["fingerprint"]) != 71
        or not binding["fingerprint"].startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in binding["fingerprint"][7:])
    ):
        raise ValueError("Invalid source-record system binding.")
    records = state.get("records")
    if not isinstance(records, list):
        raise ValueError("Source records must be a list.")
    ids, intervals = set(), []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError("Invalid source record.")
        source_id = record.get("source_id")
        if (
            not isinstance(source_id, str)
            or not source_id.strip()
            or source_id in ids
            or not integer(record.get("index"))
            or record["index"] != index
            or not isinstance(record.get("origin"), dict)
            or any(
                record.get(key) is not None and not isinstance(record[key], str)
                for key in ("label", "region_tag", "region_uid", "parent_source_id")
            )
        ):
            raise ValueError("Invalid or duplicate source identity.")
        ids.add(source_id)
        for name, count in (("atom_map", binding["n_atoms"]), ("structure_map", binding["n_structures"])):
            mapping = record.get(name)
            if (
                not isinstance(mapping, dict)
                or mapping.get("encoding") != "runs"
                or not isinstance(mapping.get("runs"), list)
                or mapping.get("status", "known") not in {"known", "unverified"}
            ):
                raise ValueError("Invalid source correspondence encoding.")
            cursor = 0
            for run in mapping["runs"]:
                if (
                    not isinstance(run, list)
                    or len(run) != 3
                    or not all(integer(i) for i in run)
                    or run[0] < 0
                    or run[1] < cursor
                    or run[2] <= 0
                    or run[0] + run[2] > np.iinfo(np.int64).max
                    or run[1] + run[2] > count
                ):
                    raise ValueError("Invalid or overlapping source correspondence runs.")
                cursor = run[1] + run[2]
                if name == "atom_map":
                    intervals.append((run[1], cursor))
            if mapping.get("status") == "unverified" and mapping["runs"]:
                raise ValueError("Unverified correspondence must not declare index runs.")
        runs = record["atom_map"]["runs"]
        if (
            not runs
            or any(not integer(record.get(key)) for key in ("start", "stop", "n_atoms"))
            or record["start"] != runs[0][1]
            or record["stop"] != runs[-1][1] + runs[-1][2]
            or record["n_atoms"] != sum(run[2] for run in runs)
        ):
            raise ValueError("Source atom accounting does not match its correspondence.")
    cursor = 0
    for start, stop in sorted(intervals):
        if start != cursor:
            raise ValueError("Source records must cover the current atoms exactly once.")
        cursor = stop
    if cursor != binding["n_atoms"]:
        raise ValueError("Source records do not cover the current atom domain.")
    return deepcopy(records)
