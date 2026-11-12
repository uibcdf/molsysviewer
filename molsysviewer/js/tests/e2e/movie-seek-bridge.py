"""Real MolSysViewer authority for the browser Movie seek guard."""

import asyncio
import json
import os
import runpy
import sys
from pathlib import Path

import molsysmt as msm

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv


def main():
    diagnostics = os.environ.get("MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR")
    if diagnostics:
        import pyunitwizard

        Path(diagnostics, "movie-authority-origin.json").write_text(
            json.dumps(
                {
                    "molsysviewer": {"file": msv.__file__, "version": msv.__version__},
                    "molsysmt": {"file": msm.__file__, "version": msm.__version__},
                    "pyunitwizard": {"file": pyunitwizard.__file__, "version": pyunitwizard.__version__},
                },
                indent=2,
            )
            + "\n"
        )
    bridge = runpy.run_path(str(Path(__file__).with_name("canvas-popup-bridge.py")))
    source = msm.systems["pentalanine"]["traj_pentalanine.h5msm"]
    with msv.new_view(source, structure_indices=[4999, 0, 73]) as view:
        view.regions.add(tag="site", atom_indices=[0, 1, 2, 3], representation="ball-and-stick")
        view.shapes.add_sphere(center="[0, 0, 0] angstrom", radius="1 angstrom", tag="site")
        view.movie.set_baseline(1000, camera={"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]})
        view.movie.add_track(
            {
                "tag": "frame",
                "target": {"domain": "structure"},
                "property": "index",
                "keys": [{"time_ms": 250, "value": 2}],
            }
        )
        view.movie.add_track(
            {
                "tag": "region",
                "target": {"domain": "region", "tag": "site"},
                "property": "visible",
                "keys": [{"time_ms": 250, "value": False}],
            }
        )
        view.movie.add_track(
            {
                "tag": "camera",
                "target": {"domain": "camera"},
                "property": "pose",
                "keys": [{"time_ms": 1000, "value": {"position": [30, 0, 0], "target": [0, 0, 0], "up": [0, 1, 0]}}],
            }
        )
        result = None
        preview = {}

        async def seek(at):
            nonlocal result
            try:
                sample = await view.movie.seek_async(at, timeout=15)
                result = {"ok": True, "sample": sample, "frame": view.player.index, "playing": view.player.is_playing}
            except Exception as error:
                result = {"ok": False, "error": str(error)}

        async def play(event):
            try:
                sample = await view.movie.play_async(event["loop"], start_time_ms=event["start"], timeout=12)
                preview["play"] = {"ok": True, "sample": sample}
            except Exception as error:
                preview["play"] = {"ok": False, "error": str(error)}

        async def pause():
            try:
                sample = await view.movie.pause_async()
                preview["pause"] = {"ok": True, "sample": sample}
            except Exception as error:
                preview["pause"] = {"ok": False, "error": str(error)}

        async def save(path):
            try:
                await view.save_session_async(path, timeout=12)
                with msv.load_session(path) as restored:
                    preview["save"] = {
                        "ok": True,
                        "frame": restored.player.index,
                        "camera": restored.camera.get_snapshot(),
                        "visible": restored.regions["site"].visible,
                        "same_recipe": restored.movie.to_dict() == view.movie.to_dict(),
                        "camera_interpolation": restored.movie.to_dict().get("camera_interpolation"),
                        "import_schema": restored.movie.to_dict().get("provenance", {}).get("schema"),
                        "source_version": restored.movie.to_dict().get("provenance", {}).get("source_version"),
                        "source_binding": restored.movie.to_dict().get("provenance", {}).get("source_binding"),
                    }
            except Exception as error:
                preview["save"] = {"ok": False, "error": str(error)}

        def action(owner, event):
            nonlocal result
            if event.get("movie_use_legacy"):
                first = {"position": [0, 0, 30], "target": [0, 0, 0], "up": [0, 1, 0]}
                last = {**first, "position": [30, 0, 0]}
                source = {
                    "molsysmovie_version": 1,
                    "keyframes": [
                        {"time_ms": 0, "camera": first, "structure_index": 0, "layer_visibility": {"site": True}},
                        {"time_ms": 1000, "camera": last, "structure_index": 2, "layer_visibility": {"site": False}},
                    ],
                }
                review = owner.movie.review_import(
                    source,
                    target_map=[
                        {
                            "source": {"domain": "legacy", "tag": "site"},
                            "target": {"domain": "region", "tag": "site"},
                        }
                    ],
                )
                assert review["can_apply"], review["conflicts"]
                owner.movie.apply_import(review)
                return True
            if event.get("movie_use_cartesian"):
                recipe = owner.movie.to_dict()
                recipe["camera_interpolation"] = "cartesian-constant-up@1"
                owner.movie.from_dict(recipe)
                return True
            if event.get("movie_start_motion"):
                owner.player.play(fps=8)
                owner.scene.spin(True)
                return True
            if "movie_seek" in event:
                result = None
                assert 2 in owner._frontend_capabilities.get("visual_state_capture", [])
                asyncio.create_task(seek(event["movie_seek"]))
                return True
            if event.get("movie_seek_status"):
                return {"movie_seek_result": result}
            if "movie_preview_play" in event:
                preview.clear()
                asyncio.create_task(play(event["movie_preview_play"]))
                return True
            if event.get("movie_preview_pause"):
                asyncio.create_task(pause())
                return True
            if "movie_preview_save" in event:
                preview.pop("save", None)
                asyncio.create_task(save(event["movie_preview_save"]))
                return True
            if event.get("movie_preview_status"):
                return {"movie_preview_result": dict(preview)}
            return False

        bridge["serve"](view, action, async_processing=True)


if __name__ == "__main__":
    main()
