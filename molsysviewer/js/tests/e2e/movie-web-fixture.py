"""Produce a real Movie, then retire Python before testing offline playback."""

import asyncio
import hashlib
import importlib
import json
import os
import runpy
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[4]
out = Path(sys.argv[1])
origins = {
    name: str(Path(importlib.import_module(name).__file__).resolve())
    for name in ("molsysviewer", "molsysmt", "pyunitwizard", "molsysmt._rust")
}
for name, variable in (
    ("molsysviewer", "MOLSYSVIEWER_ROOT"),
    ("molsysmt", "MSV_RECEIVING_INNER_ROOT"),
    ("molsysmt._rust", "MSV_RECEIVING_INNER_ROOT"),
    ("pyunitwizard", "MSV_RECEIVING_SUPPORT_ROOT"),
):
    if os.environ.get(variable):
        assert Path(origins[name]).is_relative_to(Path(os.environ[variable]).resolve()), origins
native_sha = hashlib.sha256(Path(origins["molsysmt._rust"]).read_bytes()).hexdigest()
if os.environ.get("MOLSYSVIEWER_EXPECTED_NATIVE_SHA256"):
    assert native_sha == os.environ["MOLSYSVIEWER_EXPECTED_NATIVE_SHA256"]
(out / "fixture-origin.json").write_text(
    json.dumps(
        {
            "executable": sys.executable,
            "python": sys.version,
            "modules": origins,
            "native_sha256": native_sha,
        },
        indent=2,
    )
)
factory = runpy.run_path(str(root / "tests/test_movie_appearance.py"))["make_appearance_view"]
with factory() as view:
    camera = view.movie.to_dict()["baseline"]["camera"]
    view.movie.add_track(
        {
            "tag": "camera",
            "target": {"domain": "camera"},
            "property": "pose",
            "keys": [
                {
                    "time_ms": 1000,
                    "value": {
                        **camera,
                        "position": [camera["target"][0] + 35, camera["target"][1], camera["target"][2]],
                    },
                }
            ],
        }
    )
    before = view.export_state()
    samples = {str(at): view.movie.evaluate(at) for at in [0, 250, 500, 750, 1000]}
    result = asyncio.run(view.movie.export_async(out / "movie.html"))
    assert view.export_state() == before
    (out / "expected.json").write_text(json.dumps({"samples": samples, "manifest": result["manifest"]}))
    view.movie.set_duration(60000)
    asyncio.run(view.movie.export_async(out / "long.html"))
    # Include a visibly hidden, animated shape in another independent gate case.
    view.layers.add("movie-layer")
    view.shapes["site"].set_layer_tag("movie-layer")
    view.shapes.add_sphere(
        center="[0,0,0] angstrom", radius="1 angstrom", tag="gate-hidden", layer_tag="movie-layer"
    ).hide()
    view.movie.set_baseline(1000, camera=camera)
    for track in [
        {
            "tag": "gate",
            "target": {"domain": "layer", "tag": "movie-layer"},
            "property": "visible",
            "keys": [{"time_ms": 500, "value": False}],
        },
        {
            "tag": "shape-colour",
            "target": {"domain": "shape", "tag": "gate-hidden"},
            "property": "color",
            "keys": [{"time_ms": 1000, "value": 0xFF0000}],
        },
    ]:
        view.movie.add_track(track)
    asyncio.run(view.movie.export_async(out / "gates.html"))
    view.movie.add_track(
        {
            "tag": "overlay-frame",
            "target": {"domain": "structure"},
            "property": "index",
            "keys": [{"time_ms": 500, "value": 2}],
        }
    )
    # Overlay data is added after the baseline: export must use the current
    # declared scientific context, not a stale baseline copy.
    view.trajectory_plot.show(
        series={"Control": [0.2, 0.5, 0.3]},
        x=[0, 10, 20],
        colors=[0x00FF00],
        tag="control",
        title="Control <plot> & units",
        x_label="Time (ps)",
        y_label="Control (nm)",
        width=360,
        height=220,
        observations=[
            {
                "schema": "test.movie_control@1",
                "method": "explicit analytic test series",
                "units": {"x": "ps", "y": "nm"},
                "original_structure_indices": [4999, 0, 73],
            }
        ],
    )
    view.scene.set_legend([("Control (nm)", 0xFF0000), ("Group <A>&B", 0x0000FF)])
    result = asyncio.run(view.movie.export_async(out / "overlays.html"))
    assert len(result["manifest"]["composition"]["included_dom_overlays"]) == 2
    (out / "overlays-manifest.json").write_text(json.dumps(result["manifest"]))
