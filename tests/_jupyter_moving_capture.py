"""Real scientific/file controls run inside the live Jupyter kernel for #319."""


def configure(view, output, root):
    import asyncio
    import importlib.util
    import json
    import time
    import zipfile
    from pathlib import Path

    import molsysmt as msm
    import numpy as np

    import molsysviewer as msv

    fixture = Path(root) / "molsysviewer/js/tests/e2e/moving-capture-bridge.py"
    spec = importlib.util.spec_from_file_location("jupyter_moving_science", fixture)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    inbound = []

    def received(widget, content, buffers):
        body = content.get("payload", content)
        inbound.append(
            {
                key: body[key]
                for key in ("event", "generation", "viewer_id", "session_id", "stream_id", "target_endpoint_id")
                if key in body
            }
        )
        if len(inbound) > 128:
            del inbound[0]

    view.widget.on_msg(received)
    coordinates, cells, near = module.configure_moving_scene(view)
    original = view.molsys
    loop = asyncio.get_running_loop()
    beats = {"count": 0, "handle": None, "closed": False}

    def beat():
        if not beats["closed"]:
            beats["count"] += 1
            beats["handle"] = loop.call_later(0.01, beat)

    beat()
    # Fixture-only negotiation. Production still advertises v1.
    view._frontend_capabilities["visual_state_capture"] = [1, 2]

    def start():
        view.player.play(fps=2, mode="ping-pong")
        view.scene.spin(True, speed=0.05)
        return {"heartbeat": beats["count"], "playing": view.player.is_playing}

    async def save(name, kind):
        operation = view.save_session_async if kind == "session" else view.save_state_async
        await operation(output / name)  # Preserve the real public five-second default.
        return {"heartbeat": beats["count"]}

    def inspect(name, kind, draw):
        path = output / name
        if kind == "session":
            with zipfile.ZipFile(path) as archive:
                saved = json.loads(archive.read("state.json"))
        else:
            saved = json.loads(path.read_text())
        frame = saved["view"]["structure_index"]
        assert saved["view"]["camera"] == draw["snapshot"]
        assert saved["view"]["playback"] == draw["playback"]
        assert draw["playback"]["playing"] and draw["playback"]["mode"] == "ping-pong"
        assert saved["box_display"]["structure_index"] == frame == draw["box_structure_index"]

        def close(actual, expected):
            np.testing.assert_allclose(actual, expected, rtol=0, atol=2e-4)

        close(draw["center"], [10 * frame, 0, 0])
        close(draw["boxEnd"], 10 * cells[frame, 0])
        close(draw["annotation"]["anchor"], 10 * coordinates[frame, 0])
        text = next(item for item in draw["annotationPresentation"] if item["kind"] == "text")
        close(text["textCenter"], draw["annotation"]["position"])
        close(text["cpuCenter"], draw["annotation"]["position"])
        distance = next(item for item in draw["measurement"]["geometry"] if len(item.get("points", [])) == 2)
        close(distance["points"], 10 * coordinates[frame, :2])
        assert draw["regionAtoms"] == (0 if frame == 1 else 1)
        assert all(index == frame for index in draw["interactions"])
        occurrences = (
            view.molsys.interactions["moving-analysis"].query(structure_indices=[frame]).to_dict()["occurrence_indices"]
        )
        assert bool(draw["interactions"]) == bool(len(occurrences))
        restored = msv.load_session(path) if kind == "session" else msv.new_view(view.molsys)
        with restored:
            if kind == "state":
                restored.load_state(path)
            state = restored.export_state()
            assert state["view"]["camera"] == saved["view"]["camera"]
            assert state["view"]["structure_index"] == frame
            assert restored.regions["moving-near"].atom_indices == (() if frame == 1 else (1,))
        assert view.molsys is original
        np.testing.assert_array_equal(
            msv.pyunitwizard.get_value(msm.get(view.molsys, coordinates=True), to_unit="nm"), coordinates
        )
        assert view.player.is_playing
        return {
            "structure_index": frame,
            "expected_frame_occurrences": len(occurrences),
            "independent_file_restore": True,
            "source_identity_and_coordinates_unchanged": True,
            "heartbeat": beats["count"],
            "pending_saves": len(view._work_file_saves._pending),
            "pending_captures": len(view._frontend_requests._pending),
        }

    def stop_owned():
        view.player.pause()
        view.scene.spin(False)
        beats["closed"] = True
        if beats["handle"] is not None:
            beats["handle"].cancel()
        view.widget.on_msg(received, remove=True)
        return {"heartbeat": beats["count"], "playing": view.player.is_playing}

    async def stop():
        from molsysviewer.viewer.visual_capture import _capture_owned_call

        return await _capture_owned_call(view, stop_owned, deadline=time.monotonic() + 5)

    def status():
        transfers = []
        for endpoint, manager in view._iter_structure_transfer_managers():
            active = manager.active
            transfers.append(
                {
                    "endpoint": endpoint,
                    "active": active is not None,
                    "state": active.state.value if active is not None else None,
                    "generation": active.generation if active is not None else None,
                }
            )
        return {
            "heartbeat": beats["count"],
            "playing": view.player.is_playing,
            "transfers": transfers,
            "ready": view._ready,
            "deferred_operations": len(view._endpoint_transfers.state(None).deferred),
            "closed": view.closed,
            "comm_id": view.widget.comm.comm_id,
            "comm_closed": view.widget.comm._closed,
            "inbound": inbound[:],
        }

    return {
        "start": start,
        "status": status,
        "save": save,
        "inspect": inspect,
        "stop": stop,
    }
