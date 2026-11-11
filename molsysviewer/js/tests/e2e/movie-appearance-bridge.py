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
                if event.get("rebase_setup"):
                    recipe = view.movie.to_dict()
                    view.annotations.add("Reviewed scene", atom_indices=[2], tag="rebase-note")
                    before = view.export_state()
                    before.get("view", {}).pop("camera", None)
                    revisions = (
                        view.history._edit_revision,
                        view.player._intent_revision,
                        view._camera_projection_revision,
                    )
                    try:
                        await view.movie.seek_async(500, timeout=20)
                    except ValueError as error:
                        assert "untracked changes" in str(error)
                    else:
                        raise AssertionError("An unreviewed scene edit must not start a Movie seek.")
                    after = view.export_state()
                    after.get("view", {}).pop("camera", None)
                    assert after == before and revisions == (
                        view.history._edit_revision,
                        view.player._intent_revision,
                        view._camera_projection_revision,
                    )
                    review = view.movie.review_rebase()
                    assert review["can_apply"] and view.movie.to_dict() == recipe
                    view.movie.rebase(review)
                    assert view.movie.to_dict()["tracks"] == recipe["tracks"]
                    view.movie.validate()
                    result = {"ok": True, "changes": review["changes"], "tracks_retained": True}
                elif "seek" in event:
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
                elif event.get("baseline_reset"):
                    from molsysviewer.interactions import _analysis_signature

                    view.movie.update_track("background", keys=[{"time_ms": 0, "value": 0xFFFFFF}])
                    recipe = view.movie.to_dict()
                    molecular_system = view.molsys
                    scientific = _analysis_signature(view.interactions.get_analysis("story-hbonds"))
                    view.shapes["site"].delete()
                    view.annotations["note"].delete()
                    view.annotations.add("Later", atom_indices=[1], tag="later")
                    state = await view.movie.reset_async(timeout=20)
                    assert view.movie.to_dict() == recipe and view.molsys is molecular_system
                    assert _analysis_signature(view.interactions.get_analysis("story-hbonds")) == scientific
                    assert view.annotations.get("later") is None
                    assert state["environment"]["background"] == {"color": 0}
                    assert (
                        next(row for row in view.movie.evaluate(0)["appearance"] if row["property"] == "background")[
                            "value"
                        ]
                        == 0xFFFFFF
                    )
                    result = {"ok": True, "state": state, "scientific_unchanged": True}
                elif "baseline_capture" in event:
                    recipe = await view.movie.capture_baseline_async(2500, timeout=20)
                    await view.save_session_async(event["baseline_capture"], timeout=20)
                    with msv.load_session(event["baseline_capture"]) as restored:
                        assert restored.movie.to_dict() == recipe
                        assert restored.player.index == recipe["baseline"]["scene"]["view"]["structure_index"]
                    result = {
                        "ok": True,
                        "camera": recipe["baseline"]["camera"],
                        "frame": recipe["baseline"]["scene"]["view"]["structure_index"],
                        "tracks": len(recipe["tracks"]),
                        "session_reopened": True,
                    }
                elif event.get("layer_gate_setup"):
                    camera = view.movie.to_dict()["baseline"]["camera"]
                    view.player.go_to_structure(0)
                    view.layers.add("movie-layer")
                    view.shapes["site"].set_layer_tag("movie-layer")
                    view.shapes.add_sphere(
                        center="[0,0,0] angstrom", radius="1 angstrom", tag="gate-hidden", layer_tag="movie-layer"
                    ).hide()
                    view.movie.set_baseline(1000, camera=camera)
                    view.movie.add_track(
                        {
                            "tag": "gate",
                            "target": {"domain": "layer", "tag": "movie-layer"},
                            "property": "visible",
                            "keys": [{"time_ms": 500, "value": False}],
                        }
                    )
                    result = {"ok": True}
                elif "layer_seek" in event:
                    await view.movie.seek_async(event["layer_seek"], timeout=20)
                    view.movie.validate()
                    result = {
                        "ok": True,
                        "site_hidden": view.shapes["site"]._hidden,
                        "other_hidden": view.shapes["gate-hidden"]._hidden,
                    }
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
