"""Independent layout/metadata contracts; real rasterization has a browser guard."""

import os
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest
from molsysviewer.viewer._movie_composition import (
    checked_composition,
    overlay_requirements,
    overlay_revisions,
    overlays_unchanged,
)

import molsysviewer as msv

REQUIRED = [{"kind": "colour_legend", "tag": "colour-legend"}]


def layout():
    return {
        "schema": "molsysviewer.movie_composition@1",
        "placement": "normalized-centres-uniform-scale@1",
        "unit": "px",
        "viewport": {"width": 1000, "height": 800, "unit": "css-px"},
        "layers": [
            {
                **REQUIRED[0],
                "bounds": {"x": 800, "y": 20, "width": 100, "height": 40},
                "output": {"x": 1043, "y": 18, "width": 90, "height": 36},
                "rendering": {"opacity": 1, "view_box": {"width": 100, "height": 40}},
            }
        ],
    }


def test_independent_uniform_scale_and_normalized_centres():
    # 1280/1000 != 720/800. The uniform scale is 0.9, centre (850,40)
    # maps to (1088,36), and each vector retains its aspect ratio.
    expected = layout()
    answer = checked_composition(expected, REQUIRED, 1280, 720)
    assert answer == expected
    answer["layers"].clear()
    assert len(expected["layers"]) == 1


@pytest.mark.parametrize(
    "change",
    [
        lambda row: row.update(unit="nm"),
        lambda row: row["viewport"].update(unit="px"),
        lambda row: row["viewport"].update(width=True),
        lambda row: row["viewport"].update(height=float("nan")),
        lambda row: row["layers"][0]["bounds"].update(x=-2),
        lambda row: row["layers"][0]["output"].update(width=91),
        lambda row: row["layers"][0].update(tag="other"),
        lambda row: row["layers"].append(deepcopy(row["layers"][0])),
        lambda row: row.update(layers=[]),
    ],
)
def test_wrong_units_missing_overlays_and_wrong_geometry_are_refused(change):
    value = layout()
    change(value)
    with pytest.raises(ValueError):
        checked_composition(value, REQUIRED, 1280, 720)


def test_declared_context_is_detached_and_public_overlay_changes_have_new_lifetimes():
    with msv.demo["dialanine"] as view:
        before = overlay_revisions(view)
        view.trajectory_plot.show(
            {"Control": [0.5]},
            y_label="Control (nm)",
            tag="colour-legend",
            observations=[{"schema": "test.control@1", "method": "analytic fixture", "unit": "nm"}],
        )
        view.scene.set_legend([("Control", 0xFF0000)])
        required, context = overlay_requirements(view, view.export_state())
        assert required == [{"kind": "trajectory_plot", "tag": "colour-legend"}, *REQUIRED]
        assert context["plots"][0]["series"][0]["observation"]["unit"] == "nm"
        assert overlay_revisions(view) != before
        retained = overlay_revisions(view)
        assert overlays_unchanged(view, retained)
        view.scene.set_legend([("Control", 0xFF0000)])
        assert not overlays_unchanged(view, retained)
        assert retained[1] is not view._scene_look["legend"]
        context["plots"].clear()
        assert len(overlay_requirements(view, view.export_state())[1]["plots"]) == 1


@pytest.mark.parametrize(
    "name,phrase",
    [("MovieOverlayUnavailable", "Expand"), ("MovieOverlayChanged", "fixed"), ("MovieOverlayLimit", "32 overlays")],
)
def test_fixed_renderer_failures_have_catalogued_recovery_without_echoing_renderer_text(name, phrase):
    from molsysviewer.viewer.frontend_requests import _renderer_failure

    error = _renderer_failure({"error_type": name, "message": "/private/not-a-diagnostic"})
    assert phrase in str(error)
    assert "/private" not in str(error)
    unknown = _renderer_failure({"error_type": "/private/not-a-type", "message": "untrusted"})
    assert unknown.extra["reason"] == "renderer_refused"
    assert "untrusted" not in str(unknown) and "/private" not in str(unknown)


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_MOVIE_BROWSER_TEST") != "1",
    reason="Select the actual Mol*/Chromium Movie composition guard explicitly.",
)
def test_native_movie_overlay_composition():
    subprocess.run(
        ["node", "tests/e2e/movie-composition.e2e.js"],
        cwd=Path(__file__).parents[1] / "molsysviewer/js",
        check=True,
        timeout=180,
    )
