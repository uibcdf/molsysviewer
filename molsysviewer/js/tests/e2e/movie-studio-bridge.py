"""Actual Python Movie/scene authority; only notebook comm delivery is adapted."""

import base64
import io
import json
import os
import runpy
import sys
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import molsysviewer as msv


def main():
    serve = runpy.run_path(str(Path(__file__).with_name("canvas-popup-bridge.py")))["serve"]
    with msv.demo["pentalanine"] as seed:
        with seed.extract(structure_indices=[0, 8, 3]) as view:
            view.whole.set_representation("ball-and-stick", color="blue")
            view.regions.add(atom_indices=[0, 1], tag="site", representation="ball-and-stick", color="orange")
            coordinates = msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="angstrom").copy()
            original = view.molsys
            captured = {}

            def action(owner, event):
                content = event.get("payload", event)
                frame = content.get("movie_frame")
                if content.get("event") == "visual_state_snapshot" and isinstance(frame, dict):
                    captured.setdefault(frame["job_id"], {})[frame["frame_index"]] = frame["data_uri"]
                if "movie_editor_duration_ms" in event:
                    owner.movie.set_duration(event["movie_editor_duration_ms"])
                    return {"duration_ms": owner.movie.duration_ms}
                if event.get("movie_editor_status"):
                    np.testing.assert_array_equal(
                        msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="angstrom"), coordinates
                    )
                    assert view.molsys is original
                    return {
                        "movie_editor": {
                            "recipe": owner.movie.to_dict(),
                            "busy": owner.movie._studio.job is not None,
                            "pending": len(owner._frontend_requests._pending),
                            "callbacks": len(owner.widget._scheduled_callbacks),
                            "frame": owner.player.index,
                            "source_unchanged": True,
                        }
                    }
                if event.get("movie_editor_archive"):
                    path = Path(event["movie_editor_archive"])
                    with zipfile.ZipFile(path) as archive:
                        manifest = json.loads(archive.read("manifest.json"))
                        frames = [name for name in archive.namelist() if name.endswith(".png")]
                        assert frames
                        return {"archive": {"manifest": manifest, "frames": len(frames), "bytes": path.stat().st_size}}
                if event.get("movie_editor_media"):
                    media = runpy.run_path(str(Path(__file__).with_name("movie-export-bridge.py")))["_video"]
                    metadata, frames, manifest = media(Path(event["movie_editor_media"]))
                    assert manifest["encoder"]["codec_family"] == "av1"
                    assert len(frames) == manifest["sampling"]["frame_count"] == 2
                    assert metadata["size"] == (1280, 720) and metadata["fps"] == 2
                    assert abs(metadata["duration"] - 1) < 0.01
                    with zipfile.ZipFile(event["reference"]) as archive:
                        images = [base64.b64encode(archive.read(f"frames/{i:08d}.png")).decode() for i in range(2)]
                    diagnostics = os.environ.get("MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR")
                    if diagnostics:
                        import shutil

                        import imageio.v2 as imageio

                        shutil.copyfile(event["movie_editor_media"], Path(diagnostics) / "studio-av1.webm")
                        shutil.copyfile(event["reference"], Path(diagnostics) / "studio-reference.zip")
                        (Path(diagnostics) / "av1-manifest.json").write_text(
                            json.dumps(manifest, indent=2), encoding="utf-8"
                        )
                        for i, frame in enumerate(frames):
                            imageio.imwrite(Path(diagnostics) / f"av1-native-{i}.png", frame)
                            reference = imageio.imread(io.BytesIO(base64.b64decode(images[i])))
                            imageio.imwrite(Path(diagnostics) / f"av1-expected-{i}.png", reference)
                            original_frame = captured[manifest["job_id"]][i]
                            (Path(diagnostics) / f"av1-input-{i}.png").write_bytes(
                                base64.b64decode(original_frame.split(",", 1)[1])
                            )
                    return {"manifest": manifest, "images": images, "last_output": owner.movie._studio.last_output}
                return False

            artifacts = os.environ.get("MOLSYSVIEWER_MOVIE_DIAGNOSTICS_DIR")
            if artifacts:
                import molsysmt as msm

                Path(artifacts, "movie-studio-origin.json").write_text(
                    json.dumps(
                        {
                            "python": sys.version,
                            "molsysviewer": msv.__file__,
                            "molsysmt": msm.__file__,
                            "pyunitwizard": msv.pyunitwizard.__file__,
                            "native": {
                                name: module.__file__
                                for name, module in sys.modules.copy().items()
                                if name.startswith("molsysmt")
                                and str(getattr(module, "__file__", "")).endswith((".so", ".pyd"))
                            },
                        },
                        indent=2,
                    )
                    + "\n"
                )
            serve(view, action, async_processing=True)


if __name__ == "__main__":
    main()
