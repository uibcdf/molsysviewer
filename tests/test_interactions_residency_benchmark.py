"""Independent membership and projection guards for the sparse scale probe."""

import sys

import numpy as np
import pytest
from devtools.benchmarks.interactions_detector import run_family
from devtools.benchmarks.interactions_residency import LAYOUTS, build_analysis, reference_query, run

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Linux /proc residency probes")


@pytest.mark.parametrize("layout", LAYOUTS)
@pytest.mark.parametrize("pattern", ["reuse", "churn"])
def test_reference_respects_membership_empty_frames_and_original_occurrence_identity(layout, pattern):
    analysis = build_analysis(62, 4, 5, pattern, layout)
    # First relation includes atom 0. Only the reuse case observes it again.
    expected = [0, 6] if pattern == "reuse" else [0]
    options = {"selection": 0, "structure_indices": [2, 0, 3, 1]}
    positions, coverage = reference_query(analysis, options)
    np.testing.assert_array_equal(np.sort(positions), expected)
    np.testing.assert_array_equal(coverage, [2, 0, 1])
    for mode in ("involving_selection", "across_selection_boundary"):
        positions, _ = reference_query(analysis, {**options, "mode": mode})
        np.testing.assert_array_equal(np.sort(positions), expected)
    assert reference_query(analysis, {**options, "mode": "within_selection"})[0].size == 0
    assert reference_query(analysis, {"selection": [], "mode": "within_selection"})[0].size == 0
    # A full local molecule contains every member of all these relations.
    assert len(reference_query(analysis, {"selection": list(range(62)), "mode": "within_selection"})[0]) == 10
    for frame in (1, 3):
        positions, coverage = reference_query(analysis, {"structure_indices": frame})
        assert positions.size == 0
        np.testing.assert_array_equal(coverage, [1] if frame == 1 else [])
    other_atom = LAYOUTS[layout][2][-1][0]
    options = {"selection": [0], "selection_2": [other_atom], "mode": "between_selections"}
    np.testing.assert_array_equal(np.sort(reference_query(analysis, options)[0]), expected)
    assert reference_query(analysis, {**options, "exclusive": True})[0].size == 0


@pytest.mark.parametrize("layout", LAYOUTS)
@pytest.mark.parametrize("pattern", ["reuse", "churn"])
def test_real_demo_benchmark_checks_all_queries_projection_and_h5msm(layout, pattern):
    report = run("smoke", pattern, layout, repeats=1)
    assert report["atoms"] == 62
    assert report["structures"] == 4
    assert report["occurrences"] == 10
    assert len(report["queries"]) == 26
    assert report["queries"]["empty_frame"]["matches"] == 0
    assert report["queries"]["unevaluated_frame"]["matches"] == 0
    assert report["projected_occurrences"] == 5
    assert report["projected_segments"] == {"water2": 10, "water3": 15}.get(layout, 5)
    assert report["storage"]["h5msm_bytes"] > 0


@pytest.mark.parametrize("kind", ["pi_pi", "water_bridge", "water_bridge_2"])
def test_real_detectors_keep_empty_frames_and_occurrences_separate_from_segments(kind):
    report = run_family(kind, structures=12)
    assert report["baseline_frame_counts"][1] == 0
    assert report["observations"] == 4 * sum(report["baseline_frame_counts"])
    assert report["projected_occurrences"] == report["baseline_frame_counts"][2]
    multiplier = {"water_bridge": 2, "water_bridge_2": 3}.get(kind, 1)
    assert report["projected_segments"] == multiplier * report["projected_occurrences"]
