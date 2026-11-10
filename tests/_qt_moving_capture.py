"""Continuous capture on the actual Qt transport; no scientific replies supplied."""


async def exercise_qt_moving_capture(
    *, view, bridge, js, wait, wait_js, open_work, click, saved_state, report, out, beats
):
    import asyncio
    import importlib.util
    import json
    from copy import deepcopy
    from pathlib import Path

    import numpy as np

    import molsysviewer as msv

    root = Path(__file__).resolve().parents[1]
    fixture = root / "molsysviewer/js/tests/e2e/moving-capture-bridge.py"
    spec = importlib.util.spec_from_file_location("qt_moving_scientific_fixture", fixture)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    coordinates, cells, near = module.configure_moving_scene(view)
    original = view.molsys
    await wait(lambda: not bridge.queue and bridge.inflight is None and not bridge._controls, "moving-scene-applied")
    harness = (root / "molsysviewer/js/tests/e2e/harness.bundle.js").read_text()
    await js("(() => {" + harness + ";return !!window.Harness.inspectMovingCaptureDraw;})()")
    await js("""(() => {
        const c=window.__molsysviewerDocsController;
        const p=window.__nativeMoving={draws:[],frames:[],active:null};
        const original=window.__molsysviewerDocsHandleMessage;
        window.__molsysviewerDocsHandleMessage=function(message) {
            if(message.op==='request_visual_state' && message.capture_version===2) {
                p.active={request_id:message.request_id,lastFrame:c.trajectory.getTrajectoryState().currentFrame,changes:[]};
            }
            return original.apply(this,arguments);
        };
        p.releaseFrames=c.onTrajectoryState(state=>{
            if(p.frames.at(-1)!==state.currentFrame)p.frames.push(state.currentFrame);
            if(p.frames.length>64)p.frames.shift();
            if(p.active && p.active.lastFrame!==state.currentFrame) {
                p.active.lastFrame=state.currentFrame;p.active.changes.push(state.currentFrame);
            }
        });
        let replay=true;
        p.subscription=c.plugin.canvas3d.didDraw.subscribe(()=>{
            if(replay)return;
            const draw=window.Harness.inspectMovingCaptureDraw(c);
            if(draw)p.draws.push(draw);
            if(p.draws.length>256)p.draws.shift();
        });replay=false;
        p.release=()=>{p.subscription.unsubscribe();p.releaseFrames();window.__molsysviewerDocsHandleMessage=original;};
        return true;
    })()""")
    held, replies, verdicts, queries, requests = [], [], [], [], []
    holding = False
    task = None
    sink, sender = bridge.event_sink, bridge.send
    host = f"widget-host:{view._binary_session_id}"

    def receive(event):
        if event.get("event") in {"request_dynamic_region_evaluation", "request_interaction_frame"}:
            queries.append(deepcopy(event))
            if event.get("event") == "request_dynamic_region_evaluation" and holding:
                held.append(deepcopy(event))
                return
        if event.get("event") == "visual_state_snapshot":
            replies.append(deepcopy(event))
        return sink(event)

    def send(message):
        if message.get("op") == "request_visual_state":
            requests.append(deepcopy(message))
        if message.get("op") == "studio_action_result" and message.get("action") == "save_work_file":
            verdicts.append(deepcopy(message))
        return sender(message)

    bridge.event_sink, bridge.send = receive, send
    cases = report["moving_cases"] = []
    try:
        # Receive the actual production handshake; never fabricate negotiation.
        assert 2 in view._frontend_capabilities.get("visual_state_capture", [])
        view.player.play(fps=2, mode="ping-pong")
        view.scene.spin(True, speed=0.05)
        await wait_js("window.__nativeMoving.frames.length>=3", "native-continuous-playback")
        assert queries and all(event.get("_query_endpoint_id") == host for event in queries), {
            "expected_host": host,
            "observed_queries": queries,
        }
        for kind in ("state", "session"):
            for source in ("studio", "python-async"):
                print(f"PHASE moving-{source}-{kind}", flush=True)
                path = out / f"moving-{source}-{kind}.{'json' if kind == 'state' else 'msv'}"
                await open_work(path, kind)
                mark = len(replies), len(requests), len(verdicts), len(beats)
                await js("(() => {window.__nativeMoving.active=null;return true;})()")
                holding = True
                await wait(lambda: bool(held), "genuine-scientific-query-held", timeout=3)
                if source == "studio":
                    await click("[data-molsysviewer-work-file-save]")
                else:
                    operation = view.save_session_async if kind == "session" else view.save_state_async
                    task = asyncio.create_task(operation(path))  # Real public five-second default.
                active = await wait_js(
                    "window.__nativeMoving.active?.changes.length>=2 && window.__nativeMoving.active",
                    "two-native-frame-changes-after-real-capture-request",
                    timeout=4,
                )
                assert held and len(replies) == mark[0], "Pending science must prevent an early snapshot."
                held_count = len(held)
                holding = False
                for event in held[:]:
                    sink(event)
                held.clear()
                if source == "studio":
                    await wait(lambda start=mark[2]: len(verdicts) > start, "moving-studio-save-verdict")
                    assert verdicts[-1]["ok"], verdicts[-1]
                else:
                    await task
                    task = None
                captured = replies[mark[0] :]
                assert len(captured) == 1 and captured[0]["ok"], captured
                request = requests[mark[1] :]
                assert len(request) == 1 and request[0]["capture_version"] == 2, request
                reply = captured[0]
                assert request[0]["request_id"] == reply["request_id"] == active["request_id"]
                saved = saved_state(path, kind)
                draws = await js("window.__nativeMoving.draws")
                draw = next(
                    d
                    for d in reversed(draws)
                    if d["snapshot"] == reply["snapshot"] and d["structure_index"] == reply["structure_index"]
                )
                assert saved["view"]["camera"] == draw["snapshot"]
                assert saved["view"]["playback"] == draw["playback"]
                assert draw["playback"]["playing"] and draw["playback"]["mode"] == "ping-pong"
                frame = saved["view"]["structure_index"]
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
                occurrences = view.interactions.query("moving-analysis", structure_indices=[frame]).to_dict()[
                    "occurrence_indices"
                ]
                assert bool(draw["interactions"]) == bool(len(occurrences))
                if kind == "session":
                    restored = msv.load_session(path)
                else:
                    restored = msv.new_view(view.molsys)
                    restored.load_state(path)
                with restored:
                    state = restored.export_state()
                    assert state["view"]["camera"] == saved["view"]["camera"]
                    assert state["view"]["structure_index"] == frame
                    assert restored.regions["moving-near"].atom_indices == (() if frame == 1 else (1,))
                assert view.molsys is original
                np.testing.assert_array_equal(
                    msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="nm"), coordinates
                )
                assert len(beats) > mark[3]
                assert view.player.is_playing
                cases.append(
                    {
                        "source": source,
                        "kind": kind,
                        "structure_index": frame,
                        "held_real_queries": held_count,
                        "frame_changes_after_request": active["changes"],
                        "native_draw": draw,
                        "expected_frame_occurrences": len(occurrences),
                        "independent_file_restore": True,
                        "source_identity_and_coordinates_unchanged": True,
                        "heartbeat_progress": len(beats) - mark[3],
                    }
                )
        assert queries and all(event.get("_query_endpoint_id") == host for event in queries)
        assert {event["event"] for event in queries} == {
            "request_dynamic_region_evaluation",
            "request_interaction_frame",
        }
        report["moving_query_owners"] = {"expected": host, "queries": queries}
        report["moving_scope"] = (
            "Actual Qt primary transport; independent headless file recovery. Native popup and independent-window restoration are separate scopes."
        )
        # Stopped empty/freeze controls are separate from uninterrupted saves.
        view.player.pause()
        view.scene.spin(False)
        view.player.go_to_structure(1)
        await wait_js(
            "window.__nativeMoving.draws.at(-1)?.structure_index===1 && window.__nativeMoving.draws.at(-1)?.regionAtoms===0 && !window.__nativeMoving.draws.at(-1)?.playback.playing",
            "native-empty-frame-control",
        )
        empty_path = out / "native-empty-state.json"
        await view.save_state_async(empty_path)
        empty = saved_state(empty_path, "state")
        assert empty["view"]["structure_index"] == 1 and not empty["view"]["playback"]["playing"]
        with msv.new_view(view.molsys) as restored:
            restored.load_state(empty_path)
            assert restored.player.index == 1 and restored.regions["moving-near"].atom_indices == ()
        report["native_empty_control"] = {"structure_index": 1, "region_atoms": 0, "independent_file_restore": True}
        view._clear_dynamic_region_cache(near.uid)
        view._dynamic_region_evaluation_budget_ms = -1
        view._handle_dynamic_region_evaluation_request({"frame": 0})
        await wait_js(
            "window.__nativeMoving.draws.at(-1)?.structure_index===1 && window.__nativeMoving.draws.at(-1)?.regionAtoms===1",
            "native-cross-frame-static-freeze",
        )
        frozen = await js("""(() => {
            const c=window.__molsysviewerDocsController,entry=c.state.regionIndex.get('moving-near');
            const ref=typeof entry.component==='string'?entry.component:entry.component.ref;
            const structure=c.plugin.state.data.cells.get(ref).obj.data,unit=structure.units[0],position=[0,0,0];
            unit.conformation.position(unit.elements[0],position);
            return {frame:c.trajectory.getTrajectoryState().currentFrame,atoms:entry.atomIndices,position};
        })()""")
        assert near.mode == "static" and near.atom_indices == (1,)
        assert frozen["frame"] == 1 and frozen["atoms"] == [1]
        np.testing.assert_allclose(frozen["position"], 10 * coordinates[1, 1], rtol=0, atol=2e-4)
        np.testing.assert_array_equal(msv.pyunitwizard.get_value(view.get_coordinates(), to_unit="nm"), coordinates)
        report["native_freeze_control"] = {"computed_frame": 0, "displayed": frozen, "mode": near.mode}
    finally:
        holding = False
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        for event in held:
            sink(event)
        bridge.event_sink, bridge.send = sink, sender
        view.player.pause()
        view.scene.spin(False)
        await js("(() => {window.__nativeMoving.release();return true;})()")
        (out / "moving-transport.json").write_text(
            json.dumps({"expected_host": host, "requests": requests, "replies": replies, "queries": queries}, indent=2)
        )
