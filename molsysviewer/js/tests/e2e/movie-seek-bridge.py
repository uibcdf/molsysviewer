"""Real MolSysViewer authority for the browser Movie seek guard."""

import asyncio
import runpy
import sys
from pathlib import Path

import molsysmt as msm

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv


def main():
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

        async def seek(at):
            nonlocal result
            try:
                sample = await view.movie.seek_async(at, timeout=15)
                result = {"ok": True, "sample": sample, "frame": view.player.index, "playing": view.player.is_playing}
            except Exception as error:
                result = {"ok": False, "error": str(error)}

        def action(owner, event):
            nonlocal result
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
            return False

        bridge["serve"](view, action, async_processing=True)


if __name__ == "__main__":
    main()
