"""Receive an explicit molecular story without conflating controls with simulation."""

import asyncio
import os
import subprocess
from pathlib import Path

import numpy as np
import pytest
from molsysviewer._pyunitwizard import puw
from molsysviewer.interactions import _analysis_signature

import molsysviewer as msv
from tests._movie_story import ANALYSIS, DEFAULT_ANALYSIS, TIMES, make_story_view


def test_story_uses_native_candidates_explicit_controls_and_evaluated_coverage(tmp_path):
    view, context = make_story_view()
    with view:
        recipe = view.movie.to_dict()
        result = view.interactions.get_analysis(ANALYSIS)
        before = _analysis_signature(result)
        default_before = _analysis_signature(view.interactions.get_analysis(DEFAULT_ANALYSIS))
        coordinates = puw.get_value(view.get_coordinates(), to_unit="nm").copy()
        assert context["controls"][1].startswith("synthetic")
        assert context["calculation"]["distance_threshold_nm"] == 0.4
        assert 0.23 < context["distances_nm"][0] <= 0.4
        assert context["distances_nm"][1] > 5
        for frame, evaluated, count in [(0, [0], result.n_interactions), (1, [1], 0), (2, [], 0)]:
            rows = result.query(structure_indices=[frame]).to_dict()
            assert rows["evaluated_structure_indices"].tolist() == evaluated
            assert len(rows["occurrence_indices"]) == count
        samples = {at: view.movie.evaluate(at) for at in TIMES}
        assert [samples[at]["structure_index"] for at in TIMES] == [0, 0, 0, 1, 2, 0]
        view.save_session(tmp_path / "story.msv")
        with msv.load_session(tmp_path / "story.msv") as restored:
            assert restored.movie.to_dict() == recipe
            assert _analysis_signature(restored.interactions.get_analysis(ANALYSIS)) == before
            assert _analysis_signature(restored.interactions.get_analysis(DEFAULT_ANALYSIS)) == default_before
            assert {at: restored.movie.evaluate(at) for at in TIMES} == samples
            np.testing.assert_array_equal(puw.get_value(restored.get_coordinates(), to_unit="nm"), coordinates)
            assert restored.trajectory_plot.records()[0]["series"][0]["observation"] == context
        html = asyncio.run(view.movie.export_async(tmp_path / "story.html"))
        assert html["manifest"]["recipe"] == recipe
        assert html["manifest"]["composition"]["source_context"]["plots"][0]["series"][0]["observation"] == context
        assert _analysis_signature(result) == before
        np.testing.assert_array_equal(puw.get_value(view.get_coordinates(), to_unit="nm"), coordinates)


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_MOVIE_BROWSER_TEST") != "1",
    reason="Select the real molecular-story browser receiving explicitly.",
)
def test_native_integrated_molecular_movie():
    subprocess.run(
        ["node", "tests/e2e/movie-story.e2e.js"],
        cwd=Path(__file__).parents[1] / "molsysviewer/js",
        check=True,
        timeout=360,
    )
