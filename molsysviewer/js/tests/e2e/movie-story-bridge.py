"""Live scientific authority for the integrated Movie receiving scenario."""

import asyncio
import base64
import hashlib
import importlib
import json
import os
import runpy
import sys
import traceback
import zipfile
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root))
from molsysviewer._pyunitwizard import puw
from molsysviewer.interactions import _analysis_signature, _to_plain
from tests._movie_story import ANALYSIS, TIMES, make_story_view

import molsysviewer as msv


def main():
    work = Path(os.environ["MOLSYSVIEWER_MOVIE_STORY_WORKSPACE"])
    evidence = (
        Path(os.environ["MOLSYSVIEWER_MOVIE_EVIDENCE_DIR"])
        if os.environ.get("MOLSYSVIEWER_MOVIE_EVIDENCE_DIR")
        else None
    )
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
    restoring = os.environ.get("MOLSYSVIEWER_MOVIE_STORY_SESSION")
    if restoring:
        view = msv.load_session(restoring)
        context = view.trajectory_plot.records()[0]["series"][0]["observation"]
    else:
        view, context = make_story_view()
    transport = runpy.run_path(str(Path(__file__).with_name("canvas-popup-bridge.py")))
    media = runpy.run_path(str(Path(__file__).with_name("movie-export-bridge.py")))
    with view:
        result, task, references = None, None, []
        scientific = view.interactions.get_analysis(ANALYSIS)
        scientific_hash = _analysis_signature(scientific)
        all_science = {
            name: (analysis, _analysis_signature(analysis)) for name, analysis in view.molsys.interactions.items()
        }
        coordinates = puw.get_value(view.get_coordinates(), to_unit="nm").copy()
        scientific_calls = []
        previous = sys.getprofile()

        def profile(frame, event, argument):
            if previous:
                previous(frame, event, argument)
            if event == "call" and frame.f_code.co_name in {
                "get_buch_hbonds",
                "add_missing_hydrogens",
                "reconcile_protonation",
            }:
                if frame.f_globals.get("__name__", "").startswith("molsysmt."):
                    scientific_calls.append(frame.f_code.co_name)

        def unchanged():
            assert view.interactions.get_analysis(ANALYSIS) is scientific
            assert _analysis_signature(scientific) == scientific_hash
            assert set(view.molsys.interactions) == set(all_science)
            assert all(
                view.molsys.interactions[name] is analysis and _analysis_signature(analysis) == signature
                for name, (analysis, signature) in all_science.items()
            )
            np.testing.assert_array_equal(puw.get_value(view.get_coordinates(), to_unit="nm"), coordinates)
            assert scientific_calls == [], scientific_calls

        def expected(at):
            sample = view.movie.evaluate(at)
            projected = view.interactions._frame(view.interactions["contacts"], sample["structure_index"])
            return {
                "sample": sample,
                "interaction": {key: projected[key] for key in ("status", "n_observations", "links")},
                "measurement_nm": context["distances_nm"][sample["structure_index"]],
            }

        identity = {
            "python": sys.version,
            "executable": sys.executable,
            "modules": origins,
            "native_sha256": native_sha,
            "restored": bool(restoring),
            "analysis_signature": scientific_hash,
            "analysis_signatures": {name: signature for name, (_, signature) in all_science.items()},
        }
        if evidence:
            (evidence / ("restored-origin.json" if restoring else "producer-origin.json")).write_text(
                json.dumps(identity, indent=2)
            )
        sys.setprofile(profile)

        async def operation(event):
            nonlocal result, references
            try:
                action = event["action"]
                if action == "metadata":
                    result = {
                        "ok": True,
                        "context": context,
                        "expected": {str(at): expected(at) for at in [*TIMES, 3000]},
                        "recipe": view.movie.to_dict(),
                        "frame": view.player.index,
                        "origin": identity,
                    }
                elif action == "references":
                    references = [
                        imageio.imread(base64.b64decode(uri.split(",", 1)[1]))[:, :, :3] for uri in event["images"]
                    ]
                    assert len(references) == 6
                    result = {"ok": True}
                elif action == "seek":
                    sample = await view.movie.seek_async(event["time_ms"], timeout=30)
                    result = {"ok": True, "sample": sample}
                elif action == "play":
                    sample = await view.movie.play_async(start_time_ms=0, timeout=30)
                    result = {"ok": True, "sample": sample}
                elif action == "save":
                    await view.save_session_async(work / "story.msv", timeout=30)
                    with msv.load_session(work / "story.msv") as restored:
                        assert restored.movie.to_dict() == view.movie.to_dict()
                        assert _analysis_signature(restored.interactions.get_analysis(ANALYSIS)) == scientific_hash
                        np.testing.assert_array_equal(
                            puw.get_value(restored.get_coordinates(), to_unit="nm"), coordinates
                        )
                    result = {"ok": True, "frame": view.player.index, "recipe": view.movie.to_dict()}
                elif action == "export":
                    path = work / ("story" + event["suffix"])
                    answer = await view.movie.export_async(
                        path, fps=2, width_px=1280, height_px=720, sample_level=0, timeout=30
                    )
                    assert answer["manifest"]["recipe"] == view.movie.to_dict()
                    if event["suffix"] == ".html":
                        result = {"ok": True, "manifest": answer["manifest"]}
                    else:
                        if event["suffix"] == ".zip":
                            with zipfile.ZipFile(path) as archive:
                                manifest = json.loads(archive.read("manifest.json"))
                                images = [
                                    imageio.imread(archive.read(f"frames/{i:08d}.png"))[:, :, :3] for i in range(6)
                                ]
                        else:
                            metadata, images, manifest = media["_video"](path)
                            assert metadata["size"] == (1280, 720) and metadata["fps"] == 2
                            assert abs(metadata["duration"] - 3) < 0.01
                        assert manifest == answer["manifest"] and len(images) == len(references) == 6
                        errors = [
                            float(np.abs(actual.astype(float) - reference.astype(float)).mean())
                            for actual, reference in zip(images, references, strict=True)
                        ]
                        assert max(errors) < (0.5 if event["suffix"] == ".zip" else 6), errors
                        assert (
                            manifest["composition"]["source_context"]["plots"][0]["series"][0]["observation"] == context
                        )
                        result = {"ok": True, "manifest": manifest, "reference_mean_rgb_errors": errors}
                        if evidence:
                            for index in (0, 2, 4, 5):
                                imageio.imwrite(
                                    evidence / f"decoded-{index}{event['suffix']}.png", images[index], format="png"
                                )
                    if evidence:
                        (evidence / path.name).write_bytes(path.read_bytes())
                else:
                    raise ValueError(action)
                unchanged()
                result["scientific_unchanged"] = True
                result["scientific_calls_during_playback"] = list(scientific_calls)
            except Exception as error:
                result = {"ok": False, "error": str(error), "traceback": traceback.format_exc()}

        def action(owner, event):
            nonlocal result, task
            if "movie_story" in event:
                assert task is None or task.done()
                result = None
                task = asyncio.create_task(operation(event["movie_story"]))
                return True
            if event.get("movie_story_status"):
                return {"movie_story_result": _to_plain(result)}
            return False

        try:
            transport["serve"](view, action, async_processing=True)
        finally:
            sys.setprofile(previous)


if __name__ == "__main__":
    main()
