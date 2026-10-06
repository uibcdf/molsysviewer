"""Measure coordinates plus sparse interactions in a fresh viewer process.

Fixtures retain intact demo molecules. Occurrences are synthetic; this measures
the consumer/result boundary, not detector chemistry or browser GPU throughput.
Run one workload and relation pattern per process for meaningful RSS readings.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import tempfile
import time
from pathlib import Path

import molsysmt as msm
import numpy as np
from molsysmt.native import Structures

ROOT = Path(__file__).resolve().parents[2]
if os.environ.get("MOLSYSVIEWER_TEST_INSTALLED") != "1":
    sys.path.insert(0, str(ROOT))

import molsysviewer as msv  # noqa: E402

CASES = {"smoke": (1, 4, 5), "small": (1, 5000, 5), "medium": (162, 1000, 100), "large": (1613, 100, 1000)}
LAYOUTS = {
    "hbond": ("hbond", ("donor", "hydrogen", "acceptor"), ((0,), (1,), (10,))),
    "rings": ("pi_pi", ("ring_a", "ring_b"), (tuple(range(6)), tuple(range(16, 22)))),
    "water2": (
        "water_bridge",
        tuple(f"leg_{leg}_{role}" for leg in range(1, 3) for role in ("donor", "hydrogen", "acceptor")),
        ((0,), (1,), (10,), (10,), (11,), (20,)),
    ),
    "water3": (
        "water_bridge",
        tuple(f"leg_{leg}_{role}" for leg in range(1, 4) for role in ("donor", "hydrogen", "acceptor")),
        ((0,), (1,), (10,), (10,), (11,), (20,), (20,), (21,), (30,)),
    ),
}


def rss_mib():
    with open("/proc/self/status") as source:
        for line in source:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    raise RuntimeError("This RSS probe requires Linux /proc.")


def peak_rss_mib():
    """Linux lifetime high-water mark, including fixture assembly."""
    import resource

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def build_molsys(copies, frames):
    """Repeat intact public demo molecules; this synthetic fixture has no PBC."""
    source = msm.convert(
        msm.systems["pentalanine"]["traj_pentalanine.h5msm"], to_form="molsysmt.MolSys", structure_indices=0
    )
    parts = [
        msm.structure.translate(source, translation=f"[{(index % 20) * 5}, {(index // 20) * 5}, 0] nm", in_place=False)
        for index in range(copies)
    ]
    molsys = msm.merge(parts, structure_indices=0, keep_ids=False, to_form="molsysmt.MolSys")
    # Repeat one intact structure through the public native data boundary.
    # Concatenating thousands of one-frame MolSys objects measures fixture
    # assembly rather than the consumer's coordinate/interaction residency.
    coordinates = msm.pyunitwizard.get_value(molsys.structures.coordinates, to_unit="nm")
    molsys.structures = Structures(
        coordinates=msm.pyunitwizard.quantity(np.repeat(coordinates, frames, axis=0), "nm"),
    )
    del parts, source
    molsys.structures.time = None
    return molsys


def build_analysis(n_atoms, frames, per_frame, pattern, layout):
    """Build sparse participant columns, including parallel observations.

    ``rings`` uses two six-atom groups on the intact peptide topology. These
    groups exercise centroid/participant costs; they are not aromatic rings
    detected in the peptide. Water roles similarly measure the display adapter.
    """
    evaluated = np.arange(frames - 1)
    structures = np.repeat(evaluated[evaluated % 10 != 1], per_frame)
    count = len(structures)
    relations = count if pattern == "churn" else max(1, n_atoms // 10)
    kind, roles, groups = LAYOUTS[layout]
    members = np.array([atom for group in groups for atom in group])
    relation_ids = np.arange(relations)
    copies = n_atoms // 62
    bases = (relation_ids % copies) * 62 + (relation_ids // copies) % 32
    participant_atoms = (bases[:, None] + members).ravel()
    lengths = np.tile([len(group) for group in groups], relations)
    return msm.Interactions(
        n_atoms=n_atoms,
        n_structures=frames,
        evaluated_structure_indices=np.arange(frames - 1),
        relation_types=[kind] * relations,
        relation_participant_offsets=np.arange(relations + 1) * len(roles),
        participant_roles=roles * relations,
        participant_atom_offsets=np.r_[0, np.cumsum(lengths)],
        participant_atoms=participant_atoms,
        occurrence_structures=structures,
        occurrence_relations=np.arange(count) % relations,
        occurrence_evidence=np.zeros(count, dtype=np.int32),
        evidence_labels=["synthetic"],
        measurements={"distance": np.full(count, 0.2)},
        measure_units={"distance": "nm"},
        method="synthetic_adapter_residency",
        parameters={"relation_pattern": pattern, "participant_layout": layout},
        software={"molsysmt": msm.__version__},
    )


def reference_query(analysis, options):
    """Direct membership reference, without provider query/index operations.

    The only matrix is relations × stored participant members (at most twelve
    per relation here). It never enumerates possible atom pairs or trajectories.
    """
    relation_atoms = analysis.participant_atoms.reshape(len(analysis.relation_types), -1)
    selected = options.get("selection", "all")
    mode = options.get("mode", "involving_selection")
    membership = (
        np.ones_like(relation_atoms, dtype=bool)
        if isinstance(selected, str)
        else np.isin(relation_atoms, np.atleast_1d(selected))
    )
    incident, internal = membership.any(axis=1), membership.all(axis=1)
    allowed = {
        "involving_selection": incident,
        "within_selection": internal,
        "across_selection_boundary": incident & ~internal,
    }.get(mode)
    if mode == "between_selections":
        b = np.atleast_1d(options["selection_2"])
        allowed = incident & np.isin(relation_atoms, b).any(axis=1)
        if options.get("exclusive", False):
            allowed &= np.isin(relation_atoms, np.union1d(selected, b)).all(axis=1)
    requested = options.get("structure_indices", "all")
    coverage = analysis.evaluated_structure_indices
    if not isinstance(requested, str):
        requested = np.fromiter(dict.fromkeys(np.atleast_1d(requested).tolist()), dtype=np.int64)
        coverage = requested[np.isin(requested, coverage)]
    positions = np.flatnonzero(
        allowed[analysis.occurrence_relations] & np.isin(analysis.occurrence_structures, coverage)
    )
    order = np.empty(analysis.n_structures, dtype=np.int64)
    order[coverage] = np.arange(len(coverage))
    positions = positions[np.argsort(order[analysis.occurrence_structures[positions]], kind="stable")]
    return positions, coverage


def check_query(analysis, options, query):
    expected, coverage = reference_query(analysis, options)
    actual = query.to_dict()
    # Identity/membership must be exact; row order within filtered queries is
    # not a consumer requirement. Coverage retains the requested frame order.
    np.testing.assert_array_equal(np.sort(actual["occurrence_indices"]), np.sort(expected))
    np.testing.assert_array_equal(actual["evaluated_structure_indices"], coverage)
    np.testing.assert_array_equal(
        actual["structure_indices"], analysis.occurrence_structures[actual["occurrence_indices"]]
    )
    assert query.n_interactions == len(expected)


def query_workloads(frames, n_atoms):
    axes = {"frame": 0, "nonconsecutive": [frames - 2, 0, frames // 2], "trajectory": "all"}
    selections = {
        "atom": {"selection": 0},
        "involving_selection": {"selection": [0, 1, 10, 16, 20, 30]},
        "within_selection": {"selection": list(range(62)), "mode": "within_selection"},
        "across_selection_boundary": {"selection": list(range(16)), "mode": "across_selection_boundary"},
        "between_selections": {
            "selection": list(range(6)),
            "selection_2": list(range(10, 31)),
            "mode": "between_selections",
        },
        "exclusive": {
            "selection": list(range(16)),
            "selection_2": list(range(16, 62)),
            "mode": "between_selections",
            "exclusive": True,
        },
        "wide_internal": {"selection": list(range(min(1024, n_atoms))), "mode": "within_selection"},
    }
    workloads = {f"structures_{axis}": {"structure_indices": value} for axis, value in axes.items()}
    workloads.update(
        {
            f"{name}_{axis}": {**options, "structure_indices": value}
            for name, options in selections.items()
            for axis, value in axes.items()
        }
    )
    workloads.update({"empty_frame": {"structure_indices": 1}, "unevaluated_frame": {"structure_indices": frames - 1}})
    return workloads


def run(case, pattern, layout="hbond", repeats=3):
    copies, frames, per_frame = CASES[case]
    snapshots = {"imports": rss_mib()}
    started = time.perf_counter()
    molsys = build_molsys(copies, frames)
    fixture_ms = (time.perf_counter() - started) * 1000
    axes = molsys.get_n_atoms()
    snapshots["fixture"] = rss_mib()
    started = time.perf_counter()
    analysis = build_analysis(axes, frames, per_frame, pattern, layout)
    construction_ms = (time.perf_counter() - started) * 1000
    snapshots["analysis"] = rss_mib()
    started = time.perf_counter()
    view = msv.new_view(molsys)
    view_ms = (time.perf_counter() - started) * 1000
    snapshots["view"] = rss_mib()
    try:
        started = time.perf_counter()
        view.interactions.attach(analysis, name="sparse", assume_aligned=True)
        attach_ms = (time.perf_counter() - started) * 1000
        snapshots["attached"] = rss_mib()
        options = {"selection": 0, "structure_indices": 0}
        started = time.perf_counter()
        first = view.interactions.query("sparse", **options)
        first_ms = (time.perf_counter() - started) * 1000
        snapshots["indexed"] = rss_mib()
        check_query(analysis, options, first)
        queries = {}
        for label, options in query_workloads(frames, axes).items():
            timings = []
            for _ in range(repeats):
                started = time.perf_counter()
                query = view.interactions.query("sparse", **options)
                timings.append((time.perf_counter() - started) * 1000)
            check_query(analysis, options, query)
            queries[label] = {
                "median_ms": float(np.median(timings)),
                "max_ms": max(timings),
                "matches": query.n_interactions,
            }
        snapshots["queries_checked"] = rss_mib()
        started = time.perf_counter()
        view.interactions.add("sparse", tag="all")
        view.interactions.add("sparse", tag="subset", selection=[0])
        add_sets_ms = (time.perf_counter() - started) * 1000
        assert view.interactions.get_analysis("sparse") is analysis
        assert len(view.molsys.interactions) == 1
        snapshots["two_sets"] = rss_mib()
        started = time.perf_counter()
        geometry = view.interactions._messages(frames // 2)
        geometry_ms = (time.perf_counter() - started) * 1000
        snapshots["projected"] = rss_mib()
        segment_multiplier = {"water2": 2, "water3": 3}.get(layout, 1)
        for payload in geometry:
            assert payload["status"] == "evaluated", payload["status"]
            assert payload["n_supported"] == payload["n_observations"]
            assert payload["n_segments"] == segment_multiplier * payload["n_observations"]
            assert payload["n_skipped"] == 0
        assert view.interactions._messages(1)[0]["status"] == "evaluated"
        assert view.interactions._messages(1)[0]["n_observations"] == 0
        assert view.interactions._messages(frames - 1)[0]["status"] == "unevaluated"
        inspection = view.interactions.inspect("all", structure_index=0)
        storage = storage_measurement(analysis)
        snapshots["checks_complete"] = rss_mib()
        return {
            "case": case,
            "pattern": pattern,
            "atoms": axes,
            "structures": frames,
            "layout": layout,
            "occurrences": analysis.n_interactions,
            "relations": len(analysis.relation_types),
            "coordinate_mib": axes * frames * 3 * 8 / 1024**2,
            "analysis_numeric_mib": analysis.numeric_nbytes / 1024**2,
            "fixture_ms": fixture_ms,
            "construction_ms": construction_ms,
            "view_ms": view_ms,
            "attach_ms": attach_ms,
            "rss_phases_mib": snapshots,
            "rss_loaded_mib": rss_mib(),
            "peak_rss_mib": peak_rss_mib(),
            "first_atom_frame_ms": first_ms,
            "first_matches": first.n_interactions,
            "queries": queries,
            "query_repeats": repeats,
            "add_two_sets_ms": add_sets_ms,
            "two_set_projection_ms": geometry_ms,
            "geometry_bytes": len(json.dumps(geometry).encode()),
            "projected_occurrences": geometry[0]["n_observations"],
            "projected_segments": geometry[0]["n_segments"],
            "inspection_bytes": len(json.dumps(inspection).encode()),
            "provider_version": msm.__version__,
            "provider_source": msm.__file__,
            "python": platform.python_version(),
            "storage": storage,
        }
    finally:
        view.close()


def storage_measurement(analysis):
    """Measure public interactions-only H5MSM, materializing one named layer.

    This is a warm filesystem read in the existing process, not cold-file
    latency or fresh-reader residency. No coordinate layer is written/read.
    """
    with tempfile.TemporaryDirectory(prefix="msv-interaction-residency-") as directory:
        filename = str(Path(directory) / "interactions.h5msm")
        started = time.perf_counter()
        msm.h5msm.write_layers(filename, interactions={"sparse": analysis})
        write_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        loaded = msm.h5msm.read_layers(filename, layers=["interactions"], analysis_names=["sparse"])["interactions"][
            "sparse"
        ]
        read_ms = (time.perf_counter() - started) * 1000
        for column in (
            "participant_atoms",
            "occurrence_structures",
            "occurrence_relations",
            "evaluated_structure_indices",
        ):
            np.testing.assert_array_equal(getattr(loaded, column), getattr(analysis, column))
        for options in ({"structure_indices": [analysis.n_structures - 2, 0]}, {"atom_indices": [0]}):
            np.testing.assert_array_equal(
                loaded.query(**options).to_dict()["occurrence_indices"],
                analysis.query(**options).to_dict()["occurrence_indices"],
            )
        return {"h5msm_bytes": Path(filename).stat().st_size, "write_ms": write_ms, "warm_read_ms": read_ms}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--pattern", choices=("reuse", "churn"), required=True)
    parser.add_argument("--layout", choices=LAYOUTS, default="hbond")
    parser.add_argument("--repeats", type=int, default=3)
    arguments = parser.parse_args()
    if arguments.repeats < 1:
        parser.error("--repeats must be positive")
    print(json.dumps(run(arguments.case, arguments.pattern, arguments.layout, arguments.repeats), sort_keys=True))
