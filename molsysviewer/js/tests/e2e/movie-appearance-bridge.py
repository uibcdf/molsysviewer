"""Real molecular authority for arbitrary-time appearance, preview and media."""

import asyncio
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv


def main():
    root = Path(__file__).resolve().parents[4]
    fixture = runpy.run_path(str(root / "tests/test_movie_appearance.py"))
    transport = runpy.run_path(str(Path(__file__).with_name("canvas-popup-bridge.py")))
    media = runpy.run_path(str(Path(__file__).with_name("movie-export-bridge.py")))
    with fixture["make_appearance_view"]() as view:
        result = None
        task = None

        async def operation(event):
            nonlocal result
            try:
                if "seek" in event:
                    sample = await view.movie.seek_async(event["seek"], timeout=20)
                    result = {"ok": True, "sample": sample}
                elif "play" in event:
                    sample = await view.movie.play_async(timeout=20)
                    result = {"ok": True, "sample": sample}
                elif "save" in event:
                    await view.save_session_async(event["save"], timeout=20)
                    with msv.load_session(event["save"]) as restored:
                        assert restored.movie.to_dict() == view.movie.to_dict()
                        assert restored.export_state()["environment"] == view.export_state()["environment"]
                    result = {"ok": True, "restored": True}
                elif "export" in event:
                    answer = await view.movie.export_async(
                        event["export"], fps=4, width_px=1280, height_px=720, sample_level=0, timeout=20
                    )
                    metadata, images, manifest = media["_video"](Path(answer["path"]))
                    assert len(images) == 4 and metadata["fps"] == 4
                    assert metadata["size"] == (1280, 720) and abs(metadata["duration"] - 1) < 0.01
                    assert manifest == answer["manifest"]
                    assert manifest["recipe"] == view.movie.to_dict()
                    assert len(manifest["recipe"]["tracks"]) == 12
                    means = [float(image.mean()) for image in images]
                    assert means[-1] > means[0] + 30
                    result = {"ok": True, "export": answer, "decoded_mean_brightness": means}
            except Exception as error:
                import traceback

                result = {"ok": False, "error": str(error), "traceback": traceback.format_exc()}

        def action(owner, event):
            nonlocal task, result
            if "movie_appearance" in event:
                assert task is None or task.done()
                result = None
                task = asyncio.create_task(operation(event["movie_appearance"]))
                return True
            if event.get("movie_appearance_status"):
                return {"movie_appearance_result": result}
            return False

        transport["serve"](view, action, async_processing=True)


if __name__ == "__main__":
    main()
