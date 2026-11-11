"""Real molecular Movie producer and independent media reader for browser receiving."""

import asyncio
import base64
import io
import json
import runpy
import subprocess
import sys
import traceback
import zipfile
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import molsysmt as msm
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from molsysviewer._pyunitwizard import puw

import molsysviewer as msv


def _video(path):
    reader = imageio_ffmpeg.read_frames(str(path), input_params=["-threads", "1"], output_params=["-threads", "1"])
    try:
        metadata = next(reader)
        width, height = metadata["size"]
        frames = [np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3) for raw in reader]
    finally:
        reader.close()
    result = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-threads", "1", "-i", str(path), "-f", "ffmetadata", "-"],
        capture_output=True,
        check=True,
        timeout=10,
    )
    line = next(line for line in result.stdout.decode().splitlines() if line.lower().startswith("comment="))
    value = line.split("=", 1)[1]
    decoded = []
    escaped = False
    for char in value:
        if not escaped and char == "\\":
            escaped = True
        else:
            decoded.append(char)
            escaped = False
    return metadata, frames, json.loads("".join(decoded))


def main():
    bridge = runpy.run_path(str(Path(__file__).with_name("canvas-popup-bridge.py")))
    source = msm.systems["pentalanine"]["traj_pentalanine.h5msm"]
    with msv.new_view(source, structure_indices=[4999, 0, 73]) as view:
        xyz = puw.get_value(view.molsys.structures.coordinates, to_unit="angstrom")
        center = xyz.mean(axis=(0, 1))
        view.scene.set_background("white")
        view.regions.add(tag="site", atom_indices=[0, 1, 2, 3], representation="ball-and-stick")
        view.shapes.add_sphere(center=puw.quantity(center + [5, 0, 0], "angstrom"), radius="1 angstrom", tag="marker")
        view.annotations.add("Movie control", atom_indices=[0], tag="note")
        view.movie.set_baseline(
            1000, camera={"position": (center + [0, 0, 35]).tolist(), "target": center.tolist(), "up": [0, 1, 0]}
        )
        for tag, domain, prop, target, time, value in [
            ("frame", "structure", "index", None, 500, 2),
            ("site-visible", "region", "visible", "site", 250, False),
            (
                "orbit",
                "camera",
                "pose",
                None,
                1000,
                {"position": (center + [35, 0, 0]).tolist(), "target": center.tolist(), "up": [0, 1, 0]},
            ),
        ]:
            view.movie.add_track(
                {
                    "tag": tag,
                    "target": {"domain": domain, **({"tag": target} if target else {})},
                    "property": prop,
                    "keys": [{"time_ms": time, "value": value}],
                }
            )
        current = None
        result = None
        progress = []
        output = {}
        reports = {}
        captured = {}

        async def produce(event):
            nonlocal result
            path = Path(event["path"])

            def report(row):
                progress.append(row)

            try:
                answer = await view.movie.export_async(
                    path,
                    width_px=event.get("width", 640),
                    height_px=event.get("height", 360),
                    fps=4,
                    format=event.get("format"),
                    overwrite=event.get("overwrite", False),
                    include_overlays=event.get("include_overlays", True),
                    on_progress=report,
                    timeout=event.get("timeout", 15),
                )
                output[path.suffix] = path
                reports[path.suffix] = answer["manifest"]
                result = {
                    "ok": True,
                    "export": answer,
                    "frames": list(progress),
                    "owner_retired": view.movie._export_job is None,
                }
            except asyncio.CancelledError:
                result = {"ok": False, "cancelled": True, "owner_retired": view.movie._export_job is None}
            except Exception as error:
                result = {
                    "ok": False,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                    "owner_retired": view.movie._export_job is None,
                }

        def action(owner, event):
            nonlocal current, result
            content = event.get("payload", event)
            frame = content.get("movie_frame")
            if content.get("event") == "visual_state_snapshot" and isinstance(frame, dict):
                captured.setdefault(frame["job_id"], {})[frame["frame_index"]] = frame["data_uri"]
            if "movie_export" in event:
                result = None
                progress.clear()
                current = asyncio.create_task(produce(event["movie_export"]))
                return True
            if event.get("movie_export_cancel"):
                current.cancel()
                return True
            if event.get("movie_export_status"):
                return {"movie_export_result": result, "progress_count": len(progress)}
            if "movie_export_legend" in event:
                owner.scene.set_legend([("Control", 0xFF0000)] if event["movie_export_legend"] else [])
                return True
            if event.get("movie_export_verify"):
                with zipfile.ZipFile(output[".zip"]) as archive:
                    manifest = json.loads(archive.read("manifest.json"))
                    pngs = [imageio.imread(io.BytesIO(archive.read(f"frames/{i:08d}.png")))[:, :, :3] for i in range(4)]
                metadata, videos, stored = _video(output[".mp4"])
                source = [
                    imageio.imread(io.BytesIO(base64.b64decode(captured[stored["job_id"]][i].split(",", 1)[1])))[
                        :, :, :3
                    ]
                    for i in range(4)
                ]
                assert manifest == reports[".zip"]
                assert stored == reports[".mp4"]
                assert metadata["size"] == (pngs[0].shape[1], pngs[0].shape[0])
                assert metadata["fps"] == 4 and abs(metadata["duration"] - 1) < 0.01
                assert len(videos) == 4
                assert stored["sampling"] == manifest["sampling"]
                assert stored["recipe"] == manifest["recipe"]
                assert stored["encoder"]["threads"] == 1
                independent_capture_errors = []
                for actual, expected, independent in zip(videos, source, pngs, strict=True):
                    assert float(np.std(actual)) > 1
                    assert float(np.abs(actual.astype(float) - expected).mean()) < 8
                    independent_capture_errors.append(float(np.abs(actual.astype(float) - independent).mean()))
                assert max(independent_capture_errors) < 8
                change = float(np.abs(pngs[0].astype(float) - pngs[-1]).mean())
                assert change > 0.1
                references = []
                for index, image in enumerate(source):
                    values = image.astype(np.int16)
                    mask = (values.max(axis=2) - values.min(axis=2)) > 60
                    for axis in (0, 1):
                        for shift in (-1, 1):
                            mask &= np.abs(values - np.roll(values, shift, axis=axis)).max(axis=2) <= 8
                    mask[:2] = mask[-2:] = False
                    mask[:, :2] = mask[:, -2:] = False
                    candidates = np.flatnonzero(mask)
                    assert len(candidates) >= 16
                    positions = candidates[np.linspace(0, len(candidates) - 1, 32, dtype=int)]
                    references.append(
                        {
                            "time": index / 4 + 0.001,
                            "pixels": [
                                {
                                    "x": int(p % image.shape[1]),
                                    "y": int(p // image.shape[1]),
                                    "rgb": image[p // image.shape[1], p % image.shape[1]].tolist(),
                                }
                                for p in positions
                            ],
                        }
                    )
                return {
                    "browser_reference": references,
                    "verified_video": {
                        "size": list(metadata["size"]),
                        "frames": len(videos),
                        "fps": metadata["fps"],
                        "duration": metadata["duration"],
                        "scene_change": change,
                        "embedded_recipe": True,
                        "independent_capture_mean_errors": independent_capture_errors,
                    },
                }
            return False

        bridge["serve"](view, action, async_processing=True)


if __name__ == "__main__":
    main()
