"""Fresh-process Python side of the pre-1.0 representative scale gate.

The atom axis is built from real molecular systems, not synthetic coordinate
clouds. ``181L`` supplies the small protein/crystal-solvent case. Larger cases
tile the solvated HP35 box along its cell vectors, producing a molecular
supercell with intact proteins, waters, ions, topology and periodic spacing.
Fixture construction belongs to MolSysMT and is timed separately.

Examples
--------
python devtools/benchmarks/representative_scale_gate.py --case small --structures 1
python devtools/benchmarks/representative_scale_gate.py --case large --structures 100 --repeats 3
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import resource
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import molsysmt as msm
import numpy as np

from molsysviewer import MolSysView
from molsysviewer import pyunitwizard as puw
from molsysviewer.loaders.array_native_molsys import serialize_array_native_molsys


MIB = 1024 * 1024


@dataclass(frozen=True)
class ScaleCase:
    system_name: str
    resource_name: str
    copies: int
    grid: tuple[int, int, int]


CASE_SPECS = {
    # 2,882 atoms: 181L includes protein, crystallographic waters, an ion and
    # a small molecule. Two cells avoid cutting molecules to hit exactly 2k.
    "small": ScaleCase("T4 lysozyme L99A", "181l.bcif.gz", 2, (2, 1, 1)),
    # HP35 is explicitly solvated. Integer supercells stay chemically and
    # spatially plausible while landing near the requested scale points.
    "medium": ScaleCase(
        "chicken villin HP35", "traj_chicken_villin_HP35_solvated.h5msm", 6, (3, 2, 1)
    ),
    "large": ScaleCase(
        "chicken villin HP35", "traj_chicken_villin_HP35_solvated.h5msm", 24, (4, 3, 2)
    ),
    "xlarge": ScaleCase(
        "chicken villin HP35", "traj_chicken_villin_HP35_solvated.h5msm", 72, (6, 4, 3)
    ),
}


def _current_rss_bytes() -> int:
    statm = Path("/proc/self/statm")
    if statm.exists():
        resident_pages = int(statm.read_text().split()[1])
        return resident_pages * os.sysconf("SC_PAGE_SIZE")
    # macOS reports bytes; Linux reports KiB. This fallback is diagnostic only.
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _cell_vectors_nm(molsys) -> np.ndarray:
    if molsys.structures.box is not None:
        return np.asarray(
            puw.get_value(molsys.structures.box, to_unit="nm"), dtype=np.float64
        )[0]
    coordinates = np.asarray(
        puw.get_value(molsys.structures.coordinates, to_unit="nm"), dtype=np.float64
    )[0]
    lengths = np.maximum(coordinates.max(axis=0) - coordinates.min(axis=0) + 1.0, 1.0)
    return np.diag(lengths)


def build_representative_molsys(case: str, n_structures: int):
    """Build one deterministic molecular supercell for a benchmark worker."""
    if n_structures <= 0:
        raise ValueError("n_structures must be positive")
    spec = CASE_SPECS[case]
    source = msm.convert(
        msm.systems[spec.system_name][spec.resource_name],
        to_form="molsysmt.MolSys",
        structure_indices=0,
    )
    cell = _cell_vectors_nm(source)
    parts = []
    for linear_index in range(spec.copies):
        ix = linear_index % spec.grid[0]
        iy = (linear_index // spec.grid[0]) % spec.grid[1]
        iz = linear_index // (spec.grid[0] * spec.grid[1])
        shift = ix * cell[0] + iy * cell[1] + iz * cell[2]
        parts.append(
            msm.structure.translate(
                source,
                translation=puw.quantity(shift, "nm"),
                in_place=False,
            )
        )
    merged = msm.merge(
        parts,
        structure_indices=0,
        keep_ids=False,
        to_form="molsysmt.MolSys",
    )

    if n_structures > 1:
        merged = msm.concatenate_structures(
            [merged] * n_structures,
            to_form="molsysmt.MolSys",
        )

    structures = np.asarray(
        puw.get_value(merged.structures.coordinates, to_unit="nm"), dtype=np.float64
    ).copy()
    if n_structures > 1:
        # A small deterministic rigid drift prevents a renderer from treating
        # every structure as byte-identical without distorting chemistry.
        structures[:, :, 0] += np.linspace(0.0, 0.05, n_structures)[:, None]
    merged.structures.coordinates = puw.quantity(structures, "nm")

    supercell = cell.copy()
    for axis, repeats in enumerate(spec.grid):
        supercell[axis] *= repeats
    merged.structures.box = puw.quantity(
        np.repeat(supercell[None, :, :], n_structures, axis=0), "nm"
    )
    merged.structures.structure_id = np.arange(n_structures, dtype=np.int64)
    # A sequence of structures need not be a trajectory. Do not invent time.
    merged.structures.time = None
    return merged


def run_worker(case: str, n_structures: int) -> dict:
    rss_start = _current_rss_bytes()
    started = time.perf_counter()
    molsys = build_representative_molsys(case, n_structures)
    n_atoms = int(molsys.get_n_atoms())
    fixture_ms = (time.perf_counter() - started) * 1000
    rss_after_fixture = _current_rss_bytes()

    started = time.perf_counter()
    payload = serialize_array_native_molsys(molsys)
    serialization_ms = (time.perf_counter() - started) * 1000
    rss_after_serialization = _current_rss_bytes()
    binary_bytes = sum(array.nbytes for array in payload.arrays)
    metadata_bytes = len(json.dumps(payload.metadata, separators=(",", ":")).encode())

    view = MolSysView()
    started = time.perf_counter()
    view.load(molsys, skip_digestion=True)
    load_registration_ms = (time.perf_counter() - started) * 1000
    view.close()
    del view
    gc.collect()
    rss_after_view_close = _current_rss_bytes()
    del payload
    gc.collect()
    rss_after_payload_release = _current_rss_bytes()
    del molsys
    gc.collect()
    rss_after_fixture_release = _current_rss_bytes()
    observed_peak = max(
        _peak_rss_bytes(),
        rss_after_fixture,
        rss_after_serialization,
        rss_after_view_close,
        rss_after_payload_release,
        rss_after_fixture_release,
    )

    return {
        "schema_version": 1,
        "case": case,
        "atoms": n_atoms,
        "structures": n_structures,
        "bytes": {"binary": binary_bytes, "metadata_json": metadata_bytes},
        "timings_ms": {
            "molsysmt_fixture_build": fixture_ms,
            "molsysviewer_array_native_serialization": serialization_ms,
            "molsysviewer_load_registration": load_registration_ms,
        },
        "rss_mib": {
            "start": rss_start / MIB,
            "after_fixture": rss_after_fixture / MIB,
            "after_serialization": rss_after_serialization / MIB,
            "peak": observed_peak / MIB,
            "after_view_close_with_fixture_and_payload": rss_after_view_close / MIB,
            "after_payload_release_with_fixture": rss_after_payload_release / MIB,
            "after_fixture_release": rss_after_fixture_release / MIB,
            "view_cycle_delta_with_fixture_and_payload": (
                rss_after_view_close - rss_after_serialization
            ) / MIB,
            "post_payload_release_delta_from_fixture": (
                rss_after_payload_release - rss_after_fixture
            ) / MIB,
            "post_fixture_release_delta_from_start": (
                rss_after_fixture_release - rss_start
            ) / MIB,
        },
    }


def emit_array_native_fixture(case: str, n_structures: int, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    molsys = build_representative_molsys(case, n_structures)
    fixture_ms = (time.perf_counter() - started) * 1000
    started = time.perf_counter()
    payload = serialize_array_native_molsys(molsys)
    serialization_ms = (time.perf_counter() - started) * 1000

    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(payload.metadata, separators=(",", ":")))
    array_files = []
    for index, array in enumerate(payload.arrays):
        filename = f"array-{index}.bin"
        array.tofile(output_dir / filename)
        array_files.append(filename)
    manifest = {
        "schema_version": 1,
        "case": case,
        "atoms": int(molsys.get_n_atoms()),
        "structures": n_structures,
        "metadata": metadata_path.name,
        "arrays": array_files,
        "bytes": {
            "metadata": metadata_path.stat().st_size,
            "arrays": sum((output_dir / name).stat().st_size for name in array_files),
        },
        "timings_ms": {
            "molsysmt_fixture_build": fixture_ms,
            "molsysviewer_array_native_serialization": serialization_ms,
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
    return manifest


def _median_summary(samples: list[dict]) -> dict:
    def summarize(path: tuple[str, ...]) -> dict:
        values = []
        for sample in samples:
            value = sample
            for key in path:
                value = value[key]
            values.append(float(value))
        median = statistics.median(values)
        return {
            "median": median,
            "mad": statistics.median(abs(value - median) for value in values),
            "min": min(values),
            "max": max(values),
        }

    return {
        "schema_version": 1,
        "case": samples[0]["case"],
        "atoms": samples[0]["atoms"],
        "structures": samples[0]["structures"],
        "repeats": len(samples),
        "timings_ms": {
            key: summarize(("timings_ms", key))
            for key in samples[0]["timings_ms"]
        },
        "rss_mib": {
            key: summarize(("rss_mib", key))
            for key in samples[0]["rss_mib"]
        },
        "bytes": samples[0]["bytes"],
        "samples": samples,
    }


def _table_row(summary: dict) -> dict:
    """Return the compact cross-case metrics used in the durable report."""
    timings = summary["timings_ms"]
    rss = summary["rss_mib"]
    return {
        "case": summary["case"],
        "atoms": summary["atoms"],
        "structures": summary["structures"],
        "repeats": summary["repeats"],
        "binary_mib": summary["bytes"]["binary"] / MIB,
        "metadata_mib": summary["bytes"]["metadata_json"] / MIB,
        "fixture_ms": timings["molsysmt_fixture_build"],
        "serialization_ms": timings["molsysviewer_array_native_serialization"],
        "registration_ms": timings["molsysviewer_load_registration"],
        "peak_growth_mib": {
            "median": rss["peak"]["median"] - rss["start"]["median"],
            "mad": rss["peak"]["mad"] + rss["start"]["mad"],
        },
        "view_cycle_delta_mib": rss["view_cycle_delta_with_fixture_and_payload"],
        "post_payload_release_delta_mib": rss["post_payload_release_delta_from_fixture"],
        "post_fixture_release_delta_mib": rss["post_fixture_release_delta_from_start"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_SPECS, required=True)
    parser.add_argument("--structures", type=int, required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--emit-directory", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--table-row", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.repeats <= 0:
        parser.error("--repeats must be positive")

    if args.worker:
        print(json.dumps(run_worker(args.case, args.structures), sort_keys=True))
        return 0

    if args.emit_directory is not None:
        print(json.dumps(
            emit_array_native_fixture(args.case, args.structures, args.emit_directory),
            sort_keys=True,
        ))
        return 0

    samples = []
    for _ in range(args.repeats):
        completed = subprocess.run(
            [
                sys.executable,
                __file__,
                "--case", args.case,
                "--structures", str(args.structures),
                "--worker",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        samples.append(json.loads(completed.stdout.splitlines()[-1]))
    summary = _median_summary(samples)
    if args.table_row:
        summary = _table_row(summary)
    elif args.summary_only:
        summary.pop("samples", None)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
