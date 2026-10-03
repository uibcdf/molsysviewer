"""Measure real detectors over trajectories at the Viewer boundary.

Run in a fresh Linux process. The measurements include a real MolSysView and
its coordinates; they do not represent browser/GPU throughput or a size limit.
The default measures Buch on the complete 5,000-frame peptide demo. Other
families repeat the known positive/empty conformations from the shared real
chemical fixtures; these are bounded detector probes, not large-system claims.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path
from runpy import run_path

ROOT = Path(__file__).resolve().parents[2]
if os.environ.get("MOLSYSVIEWER_TEST_INSTALLED") != "1":
    sys.path.insert(0, str(ROOT))
else:
    run_path(str(ROOT / "devtools/_fixture_namespace.py"))["expose_fixture_namespace"](ROOT)

import molsysmt as msm  # noqa: E402
import numpy as np  # noqa: E402
from devtools.benchmarks.interactions_residency import peak_rss_mib  # noqa: E402
from devtools.interaction_family_fixtures import make_family_view  # noqa: E402
from devtools.qualify_interactions import observed_geometry  # noqa: E402
from molsysmt.native import Structures  # noqa: E402
from molsysviewer._private.interaction_families import FAMILIES  # noqa: E402

import molsysviewer as msv  # noqa: E402


def rss_mib():
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024
    raise RuntimeError("This measurement requires Linux /proc.")


def run_family(kind, structures=1000):
    """Measure one real family, retaining evaluated-empty conformations.

    The three-conformation analytical fixtures repeat positive, empty and
    positive frames. Disulfides use the actual large protein's one conformation.
    Counts and occurrence identities are verified outside the timed operations.
    """
    started = time.perf_counter()
    fixture = make_family_view(kind)
    source = fixture.view
    view = None
    try:
        baseline = fixture.calculate(name="baseline", structure_indices="all")
        frame_counts = np.bincount(baseline.occurrence_structures, minlength=baseline.n_structures)
        assert baseline.n_interactions > 0
        system = msm.copy(source.molsys)
        system.interactions = {}
        coordinates = msm.pyunitwizard.get_value(system.structures.coordinates, to_unit="nm")
        frame_indices = np.arange(structures) % len(coordinates)
        system.structures = Structures(coordinates=msm.pyunitwizard.quantity(coordinates[frame_indices], "nm"))
        system.structures.time = None
        view = msv.new_view(system)
        load_ms = (time.perf_counter() - started) * 1000
        before = rss_mib()
        getter = getattr(getattr(view.interactions, fixture.family), fixture.function)
        started = time.perf_counter()
        result = getter(name="measured", structure_indices="all", **fixture.parameters)
        detector_ms = (time.perf_counter() - started) * 1000
        after_detector = rss_mib()
        np.testing.assert_array_equal(result.evaluated_structure_indices, np.arange(structures))
        np.testing.assert_array_equal(
            np.bincount(result.occurrence_structures, minlength=structures), frame_counts[frame_indices]
        )
        atom = int(result.participant_atoms[0])
        selected_frames = list(dict.fromkeys([structures - 1, 0, structures // 2]))
        timings = []
        for _ in range(10):
            started = time.perf_counter()
            query = view.interactions.query("measured", selection=[atom], structure_indices=selected_frames)
            timings.append((time.perf_counter() - started) * 1000)
        query_data = query.to_dict()
        np.testing.assert_array_equal(
            query_data["structure_indices"], result.occurrence_structures[query_data["occurrence_indices"]]
        )
        assert np.isin(query_data["structure_indices"], selected_frames).all()
        started = time.perf_counter()
        view.interactions.add("measured", tag="measured")
        initial_set_projection_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        payload = view.interactions._messages(structures - 1)[0]
        projection_ms = (time.perf_counter() - started) * 1000
        assert payload["status"] == "evaluated"
        assert payload["n_observations"] == int(frame_counts[frame_indices[-1]])
        assert payload["n_supported"] == payload["n_observations"] and payload["n_skipped"] == 0
        return {
            "case": "real-family-repeated-conformations",
            "family": kind,
            "atoms": result.n_atoms,
            "structures": result.n_structures,
            "observations": result.n_interactions,
            "baseline_frame_counts": frame_counts.tolist(),
            "provider_version": msm.__version__,
            "provider_source": msm.__file__,
            "python": platform.python_version(),
            "setup_and_baseline_ms": load_ms,
            "detector_ms": detector_ms,
            "first_atom_frame_query_ms": timings[0],
            "warm_atom_frame_median_ms": float(np.median(timings[1:])),
            "query_matches": query.n_interactions,
            "query_frames": selected_frames,
            "projection_ms": projection_ms,
            "projection_cached": structures == 1,
            "initial_set_projection_ms": initial_set_projection_ms,
            "projected_occurrences": payload["n_observations"],
            "projected_segments": payload["n_segments"],
            "geometry_bytes": len(json.dumps(payload).encode()),
            "analysis_numeric_mib": result.numeric_nbytes / 1024**2,
            "rss_before_analysis_mib": before,
            "rss_after_detector_mib": after_detector,
            "rss_after_checks_mib": rss_mib(),
            "peak_process_rss_mib": peak_rss_mib(),
        }
    finally:
        source.close()
        if view is not None:
            view.close()


def main():
    started = time.perf_counter()
    view = msv.new_view(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    load_ms = (time.perf_counter() - started) * 1000
    try:
        before = rss_mib()
        started = time.perf_counter()
        result = view.interactions.hbonds.get_buch_hbonds(name="buch", structure_indices="all", pbc=True)
        compute_ms = (time.perf_counter() - started) * 1000
        assert result.n_structures == 5000 and result.n_atoms == 62
        np.testing.assert_array_equal(result.evaluated_structure_indices, np.arange(5000))
        assert result.n_interactions > 0
        view.interactions.add("buch", tag="real-hb")
        first_frame = int(result.occurrence_structures[0])
        frames = [4999, first_frame, 73]
        first = result.query(structure_indices=first_frame).to_dict()
        atom = int(result.relation(int(first["relation_indices"][0]))["participants"][1]["atom_indices"][0])
        timings = []
        for _ in range(20):
            started = time.perf_counter()
            query = view.interactions.query("buch", selection=[atom], structure_indices=frames)
            timings.append((time.perf_counter() - started) * 1000)
        matches = query.n_interactions
        started = time.perf_counter()
        trajectory_matches = view.interactions.query("buch", selection=[atom]).n_interactions
        atom_trajectory_ms = (time.perf_counter() - started) * 1000
        expected, _, images = observed_geometry(view, "buch", "real-hb", frames=frames)
        assert len(expected) == result.n_interactions
        print(
            json.dumps(
                {
                    "case": "real-pentalanine-complete-trajectory",
                    "atoms": result.n_atoms,
                    "structures": result.n_structures,
                    "observations": result.n_interactions,
                    "provider_version": msm.__version__,
                    "provider_source": msm.__file__,
                    "python": platform.python_version(),
                    "load_ms": load_ms,
                    "detector_ms": compute_ms,
                    "first_atom_frame_query_ms": timings[0],
                    "warm_atom_frame_median_ms": float(np.median(timings[1:])),
                    "atom_trajectory_query_ms": atom_trajectory_ms,
                    "atom_trajectory_matches": trajectory_matches,
                    "query_frames": frames,
                    "query_matches": matches,
                    "nonzero_image_observations": images,
                    "analysis_numeric_mib": result.numeric_nbytes / 1024**2,
                    "rss_before_analysis_mib": before,
                    "rss_after_checks_mib": rss_mib(),
                    "peak_process_rss_mib": peak_rss_mib(),
                }
            )
        )
    finally:
        view.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=list(FAMILIES) + ["water_bridge_2"], default="hbond")
    parser.add_argument("--structures", type=int)
    arguments = parser.parse_args()
    if arguments.structures is not None and arguments.structures < 1:
        parser.error("--structures must be positive")
    if arguments.family == "hbond":
        if arguments.structures is not None:
            parser.error("The Buch demo probe retains all 5,000 actual structures.")
        main()
    else:
        size = arguments.structures or (1 if arguments.family == "disulfide_candidate" else 1000)
        print(json.dumps(run_family(arguments.family, size), sort_keys=True))
