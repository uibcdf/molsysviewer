"""Portable presentations use real scene owners and preserve their source."""

import asyncio
import json
import os
import re
import subprocess
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from molsysviewer._pyunitwizard import puw

import molsysviewer as msv


@pytest.fixture
def view():
    with msv.demo["pentalanine"] as seed:
        with seed.extract(structure_indices=[0, 8, 3]) as view:
            view.whole.set_representation("ball-and-stick", color=0x204060)
            view.regions.add(tag="site", atom_indices=[0, 1, 2], representation="spacefill", color=0xFF5500)
            view.annotations.add("Beginning", atom_indices=[0], tag="note")
            view.movie.set_baseline(1000, camera={"position": [0, 0, 40], "target": [0, 0, 0], "up": [0, 1, 0]})
            view.movie.add_track(
                {
                    "tag": "frame",
                    "target": {"domain": "structure"},
                    "property": "index",
                    "keys": [{"time_ms": 500, "value": 2}],
                }
            )
            yield view


def embedded(html, name):
    match = re.search(r'<script id="' + name + r'" type="application/json">(.*?)</script>', html, re.S)
    assert match, name
    return json.loads(match[1])


def test_headless_html_is_self_contained_and_preserves_source(view, tmp_path):
    before = deepcopy(view.export_state())
    coordinates = puw.get_value(view.molsys.structures.coordinates, to_unit="nm").copy()
    recipe = view.movie.to_dict()
    result = asyncio.run(view.movie.export_async(tmp_path / "movie.html", format="html"))
    assert result["manifest"]["recipe"] == recipe
    assert result["manifest"]["assets"]["policy"] == "embedded-offline"
    assert result["bytes"] > 10000
    assert view.export_state() == before
    np.testing.assert_array_equal(puw.get_value(view.molsys.structures.coordinates, to_unit="nm"), coordinates)
    html = (tmp_path / "movie.html").read_text()
    messages = embedded(html, "molsysviewer-messages")
    assert len([row for row in messages if row["op"] == "load_molsys_payload"]) == 1
    assert len(next(row for row in messages if row["op"] == "load_molsys_payload")["payload"]["structures"]) == 3
    assert embedded(html, "molsysviewer-runtime-source")
    assert '"movie_presentation"' in html


def test_atomic_web_destination_and_callback_failure(view, tmp_path):
    path = tmp_path / "existing.html"
    path.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        asyncio.run(view.movie.export_async(path))

    def fail(_):
        raise RuntimeError("receiving failure")

    with pytest.raises(RuntimeError, match="receiving failure"):
        asyncio.run(view.movie.export_async(path, overwrite=True, on_progress=fail))
    assert path.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [path]
    asyncio.run(view.movie.export_async(path, overwrite=True))
    assert path.read_bytes().startswith(b"<!DOCTYPE html>")


def test_stale_callback_cannot_publish_a_recipe(view, tmp_path):
    def change(_):
        view.movie.set_duration(1500)

    path = tmp_path / "stale.html"
    with pytest.raises(Exception, match="superseded"):
        asyncio.run(view.movie.export_async(path, on_progress=change))
    assert not path.exists()


def test_cancelled_web_task_does_not_publish(view, tmp_path):
    async def cancel():
        task = asyncio.create_task(view.movie.export_async(tmp_path / "cancelled.html"))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    assert not list(tmp_path.iterdir())
    assert view.movie._export_job is None


def test_concurrent_web_export_has_one_owner(view, tmp_path):
    async def receive():
        return await asyncio.gather(
            view.movie.export_async(tmp_path / "first.html"),
            view.movie.export_async(tmp_path / "second.html"),
            return_exceptions=True,
        )

    results = asyncio.run(receive())
    assert sum(isinstance(result, dict) for result in results) == 1
    assert sum(isinstance(result, Exception) and "pending" in str(result) for result in results) == 1
    assert len(list(tmp_path.iterdir())) == 1
    assert view.movie._export_job is None


def test_closed_source_cannot_publish_after_progress(view, tmp_path):
    with pytest.raises(Exception, match="superseded"):
        asyncio.run(view.movie.export_async(tmp_path / "closed.html", on_progress=lambda _: view.close()))
    assert not list(tmp_path.iterdir())


def test_visible_overlay_needs_an_explicit_exclusion(view, tmp_path):
    view.scene.set_legend([{"label": "Site", "color": 0xFF5500}])
    view.movie.rebase(view.movie.review_rebase())
    with pytest.raises(ValueError, match="plots/legends"):
        asyncio.run(view.movie.export_async(tmp_path / "refused.html"))
    result = asyncio.run(view.movie.export_async(tmp_path / "excluded.html", include_overlays=False))
    assert result["manifest"]["composition"]["excluded_dom_overlays"] == ["colour-legend"]
    messages = embedded((tmp_path / "excluded.html").read_text(), "molsysviewer-messages")
    assert not any(row["op"] == "set_legend" for row in messages)


def test_dynamic_regions_are_not_silently_frozen(view, tmp_path):
    view.regions.add(tag="moving", selection="atom_index < 3").set_mode("dynamic")
    view.movie.set_baseline(1000, camera={"position": [0, 0, 40], "target": [0, 0, 0], "up": [0, 1, 0]})
    with pytest.raises(ValueError, match="static regions"):
        asyncio.run(view.movie.export_async(tmp_path / "dynamic.html"))
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "options", [{"width_px": 0}, {"height_px": True}, {"overwrite": 1}, {"timeout": 0}, {"include_overlays": 1}]
)
def test_invalid_web_options_preserve_destination(view, tmp_path, options):
    path = tmp_path / "invalid.html"
    with pytest.raises(ValueError):
        asyncio.run(view.movie.export_async(path, **options))
    assert not path.exists()


@pytest.mark.skipif(
    os.environ.get("MOLSYSVIEWER_MOVIE_BROWSER_TEST") != "1",
    reason="Explicit real Mol*/Chromium offline Movie receiving is required.",
)
def test_native_offline_movie_presentation():
    """Receive the complete Python recipe in an offline native renderer."""
    js = Path(__file__).parents[1] / "molsysviewer/js"
    subprocess.run(["node", "tests/e2e/movie-web.e2e.js"], cwd=js, check=True, timeout=180)
