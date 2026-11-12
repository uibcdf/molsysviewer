"""Straight camera paths on real molecular scenes, without changing the default."""

import json
import math
import os
import subprocess
from copy import deepcopy
from pathlib import Path

import molsysmt as msm
import numpy as np
import pytest

import molsysviewer as msv

BEGIN = {"position": [0, 0, 10], "target": [0, 0, 0], "up": [0, 1, 0]}
END = {"position": [10, 0, 0], "target": [0, 0, 0], "up": [0, 1, 0]}
MODE = "cartesian-constant-up@1"


@pytest.fixture
def view():
    with msv.demo["dialanine"] as value:
        value.movie.set_baseline(1000, camera=BEGIN)
        value.movie.add_track(
            {
                "tag": "camera",
                "target": {"domain": "camera"},
                "property": "pose",
                "keys": [{"time_ms": 1000, "value": END}],
            }
        )
        yield value


def enable_cartesian(view):
    recipe = view.movie.to_dict()
    recipe["camera_interpolation"] = MODE
    view.movie.from_dict(recipe)
    return recipe


@pytest.mark.parametrize("easing", ["linear", "ease-in", "ease-out", "ease-in-out"])
def test_cartesian_is_explicit_and_preserves_detached_seek_and_preview(view, easing):
    default = view.movie.evaluate(500)
    np.testing.assert_allclose(default["camera"]["position"], [math.sqrt(50), 0, math.sqrt(50)], atol=1e-12)
    assert "camera_interpolation" not in view.movie.to_dict()
    recipe = enable_cartesian(view)
    view.movie.update_track(
        "camera", keys=[{"time_ms": 0, "value": BEGIN, "easing": easing}, {"time_ms": 1000, "value": END}]
    )
    for at in [900, 100, 500, 0, 1000, 100]:
        raw = at / 1000
        fraction = (
            raw * raw
            if easing == "ease-in"
            else 1 - (1 - raw) * (1 - raw)
            if easing == "ease-out"
            else 2 * raw * raw
            if easing == "ease-in-out" and raw < 0.5
            else 1 - 2 * (1 - raw) * (1 - raw)
            if easing == "ease-in-out"
            else raw
        )
        sample = view.movie.evaluate(at)
        np.testing.assert_allclose(sample["camera"]["position"], [10 * fraction, 0, 10 * (1 - fraction)], atol=1e-12)
        assert sample["camera"]["target"] == BEGIN["target"]
        # The sample reconstructs an orthonormal basis; allow its few-ULP
        # normalization error, rather than requiring exact vector arithmetic.
        np.testing.assert_allclose(sample["camera"]["up"], BEGIN["up"], rtol=0, atol=4 * np.finfo(float).eps)
    assert view.movie._timeline.preview_recipe()["camera_interpolation"] == MODE
    recipe["camera_interpolation"] = "user mutation"
    assert view.movie.to_dict()["camera_interpolation"] == MODE


@pytest.mark.parametrize(
    "end,reason",
    [
        ({**END, "position": [0, 0, -22]}, "unsafe viewing direction"),
        ({**END, "position": [0, 4, -22]}, "unsafe viewing direction"),
        ({**END, "up": [0, 0, 1]}, "constant up vector"),
    ],
)
def test_whole_cartesian_segment_is_checked_before_publishing_import_or_edit(view, end, reason):
    before = view.movie.to_dict()
    recipe = deepcopy(before)
    recipe["camera_interpolation"] = MODE
    recipe["tracks"][0]["keys"][0]["value"] = end
    with pytest.raises(ValueError, match=reason):
        view.movie.from_dict(recipe)
    assert view.movie.to_dict() == before
    enable_cartesian(view)
    before = view.movie.to_dict()
    with pytest.raises(ValueError, match=reason):
        view.movie.update_track("camera", keys=[{"time_ms": 1000, "value": end}])
    assert view.movie.to_dict() == before


def test_explicit_zero_pose_replaces_the_baseline_without_a_fictitious_segment(view):
    recipe = view.movie.to_dict()
    recipe["baseline"]["camera"]["up"] = [1, 0, 0]
    recipe["tracks"][0]["keys"].insert(0, {"time_ms": 0, "value": BEGIN})
    recipe["camera_interpolation"] = MODE
    view.movie.from_dict(recipe)
    assert view.movie.evaluate(500)["camera"]["position"] == [5, 0, 5]
    before = view.movie.to_dict()
    with pytest.raises(ValueError, match="constant up vector"):
        view.movie.update_track("camera", keys=[{"time_ms": 1000, "value": END}])
    assert view.movie.to_dict() == before


@pytest.mark.parametrize("mode", [None, True, 1, "cartesian", "unknown", {}])
def test_unknown_camera_modes_do_not_replace_a_plan(view, mode):
    before = view.movie.to_dict()
    recipe = deepcopy(before)
    recipe["camera_interpolation"] = mode
    with pytest.raises(ValueError, match="camera interpolation"):
        view.movie.from_dict(recipe)
    assert view.movie.to_dict() == before


def test_cartesian_recipe_survives_review_rebase_and_real_session(view, tmp_path):
    coordinates = msm.pyunitwizard.get_value(view.molsys.structures.coordinates, to_unit="nm").copy()
    enable_cartesian(view)
    view.movie.set_duration(1500)
    view.movie.rebase(view.movie.review_rebase())
    reviewed = view.movie.review_import(view.movie.to_dict())
    assert reviewed["can_apply"]
    view.movie.apply_import(reviewed)
    assert view.movie.to_dict()["camera_interpolation"] == MODE
    report = view.movie.review_import(view.movie.to_dict(), camera={**BEGIN, "up": [1, 0, 0]})
    assert not report["can_apply"]
    assert any(row["reason"] == "incompatible_scene_or_track" for row in report["conflicts"])
    expected = view.movie.evaluate(500)
    path = tmp_path / "straight-camera.msv"
    view.save_session(path)
    with msv.load_session(path) as restored:
        assert restored.movie.to_dict()["camera_interpolation"] == MODE
        assert restored.movie.evaluate(500) == expected
        np.testing.assert_array_equal(
            msm.pyunitwizard.get_value(restored.molsys.structures.coordinates, to_unit="nm"), coordinates
        )


def test_cartesian_rejects_overflow_and_preserves_subnormal_paths(view):
    recipe = enable_cartesian(view)
    recipe["baseline"]["camera"]["position"] = [1e308, 0, 0]
    recipe["baseline"]["camera"]["target"] = [1e308 - 1e293, 0, 0]
    recipe["tracks"][0]["keys"][0]["value"] = {
        "position": [-1e308, 0, 0],
        "target": [-1e308 + 1e293, 0, 0],
        "up": [0, 1, 0],
    }
    with pytest.raises(ValueError, match="finite coordinate range"):
        view.movie.from_dict(recipe)
    recipe = view.movie.to_dict()
    recipe["baseline"]["camera"]["position"] = [0, 0, 1e-320]
    recipe["tracks"][0]["keys"][0]["value"]["position"] = [1e-320, 0, 0]
    view.movie.from_dict(recipe)
    assert view.movie.evaluate(500)["camera"]["position"] == [5e-321, 0, 5e-321]


def test_documented_cartesian_example(view):
    text = (Path(__file__).parents[1] / "docs/content/user/movie/timeline.md").read_text()
    block = text.split("<!-- cartesian-camera-example -->", 1)[1].split("```python", 1)[1].split("```", 1)[0]
    exec(compile(block, "movie-cartesian-example", "exec"), {"view": view})
    assert view.movie.evaluate(500)["camera"]["position"] == [5, 0, 5]


def test_shared_cartesian_oracle_uses_the_real_timeline(view):
    oracle = json.loads(
        (Path(__file__).parents[1] / "molsysviewer/js/tests/fixtures/movie-cartesian-oracle.json").read_text()
    )
    for entry in oracle["valid"]:
        recipe = view.movie.to_dict()
        recipe.update(camera_interpolation=MODE, baseline={**recipe["baseline"], "camera": entry["begin"]})
        recipe["tracks"] = [
            {"tag": "camera", "target": {"domain": "camera"}, "property": "pose", "keys": entry["keys"]}
        ]
        view.movie.from_dict(recipe)
        for sample in entry["samples"]:
            np.testing.assert_allclose(
                view.movie.evaluate(sample["time_ms"])["camera"]["position"], sample["position"], atol=1e-12
            )
            np.testing.assert_allclose(
                view.movie.evaluate(sample["time_ms"])["camera"]["target"],
                sample.get("target", entry["begin"]["target"]),
                atol=1e-12,
            )


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_MOVIE_BROWSER_TEST") != "1",
    reason="Explicit real Mol*/Chromium Cartesian Movie receiving is required.",
)
def test_native_cartesian_camera_seek_and_preview():
    """Receive actual primary/popup geometry and cross-language preview samples."""
    js = Path(__file__).parents[1] / "molsysviewer/js"
    subprocess.run(["node", "tests/e2e/movie-seek.e2e.js"], cwd=js, check=True, timeout=180)
