"""Real native work-file receiving for #319 over one application-owned Qt loop.

This child keeps optional Qt imports inside main for headless test collection.
It renders actual demo data and records the observed platform/renderer; this is
an automated functional guard, not human release acceptance or a universal
provider/platform compatibility claim.
"""

from __future__ import annotations

import faulthandler
import sys
from pathlib import Path


def main(output: Path) -> None:
    import asyncio
    import json
    import sys
    import time
    import traceback
    import zipfile
    from copy import deepcopy
    from importlib import import_module
    from threading import get_ident

    import molsysviewer.standalone_qt as qt

    import molsysviewer as msv

    qt_api = qt._import_qt()
    QTimer = qt_api["QTimer"]
    binding = QTimer.__module__.partition(".")[0]
    QtAsyncio = import_module(f"{binding}.QtAsyncio")
    QtCore = import_module(f"{binding}.QtCore")
    QPoint, Qt = QtCore.QPoint, QtCore.Qt
    QTest = import_module(f"{binding}.QtTest").QTest

    out = output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    qt._qt_shell_state_path = lambda: out / "shell-state.json"
    original = msv.demo["pentalanine"]
    selected = original.extract(structure_indices=[0, 8, 3])
    runtime = qt.create_standalone_qt0_window(
        selected.molsys,
        output_filename=str(out / "shell.html"),
        apply_project_config=False,
        title="MolSysViewer — native capture receiving",
        width=1160,
        height=800,
    )
    app, window, web = (runtime[k] for k in ("app", "window", "webview"))
    app.setQuitOnLastWindowClosed(False)
    view, bridge = web._molsysviewer_view, web._molsysviewer_qt_bridge
    events, inbound, phases, beats = [], [], [], []
    frontend_diagnostics = []
    rotation_index = 0
    lifetimes = []

    def checkpoint(name):
        lifetimes.append({"phase": name, "at": time.monotonic(), "thread": get_ident()})
        (out / "lifecycle.json").write_text(json.dumps(lifetimes, indent=2))

    for label, obj in (("window", window), ("webview", web), ("page", web.page()), ("profile", web.page().profile())):
        obj.destroyed.connect(lambda *_, label=label: checkpoint(label + "-destroyed"))
    app.aboutToQuit.connect(lambda: checkpoint("app-about-to-quit"))
    owner_thread = get_ident()
    sink = bridge.event_sink
    sender = bridge.send
    frontend_handler = bridge.handle_frontend_event

    def observed_frontend_event(event):
        if isinstance(event, dict) and event.get("event") in {"message_error", "frontend_error"}:
            frontend_diagnostics.append(deepcopy(event))
        return frontend_handler(event)

    bridge.handle_frontend_event = observed_frontend_event

    def observed_event(event):
        if event.get("event") in {"visual_state_snapshot", "frontend_error", "ready"} or event.get("action") in {
            "save_work_file",
            "cancel_work_file",
            "restore_work_file",
        }:
            events.append(deepcopy(event))
        return sink(event)

    def observed_send(message):
        if message.get("op") in {"request_visual_state", "cancel_visual_state", "studio_action_result"}:
            inbound.append(deepcopy(message))
        return sender(message)

    bridge.event_sink = observed_event
    bridge.send = observed_send
    heartbeat = QTimer(window)
    heartbeat.setInterval(2)
    heartbeat.timeout.connect(lambda: beats.append(get_ident()))
    heartbeat.start()
    window.show()

    async def wait(predicate, name, timeout=30):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if predicate():
                return
            await asyncio.sleep(0.01)
        raise AssertionError(
            f"Timed out at {name}; inflight={bridge.inflight}; controls={list(bridge._controls)}; failed={bridge.failed_deliveries}"
        )

    async def js(expression):
        future = asyncio.get_running_loop().create_future()

        def complete(value):
            if not future.done():
                future.set_result(json.loads(value) if isinstance(value, str) and value else value)

        web.page().runJavaScript("JSON.stringify(" + expression + ")", complete)
        return await asyncio.wait_for(future, 10)

    async def wait_js(expression, name, timeout=30):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            value = await js(expression)
            if value:
                return value
            await asyncio.sleep(0.01)
        raise AssertionError(f"Timed out at {name}; lastJS={value}; laststatus={window.statusBar().currentMessage()}")

    async def idle():
        await wait(
            lambda: bridge.ready and not bridge.queue and bridge.inflight is None and not bridge._controls,
            "bridge-idle",
        )

    async def open_work(path=None, kind=None):
        arguments = json.dumps({"path": str(path) if path else None, "kind": kind})
        await js("""(() => {
            const c=window.__molsysviewerDocsController;
            c.setPanelMode('navigate', true); c.groupPanel.openSection('export');
            return true;
        })()""")
        await wait_js("!!document.querySelector('[data-molsysviewer-work-files]')", "work-controls")
        await js(
            """(() => {
            const values="""
            + arguments
            + """;
            const root=document.querySelector('[data-molsysviewer-work-files]');
            if (values.kind) { const e=root.querySelector('[aria-label="Work file format"]'); e.value=values.kind; e.dispatchEvent(new Event('change',{bubbles:true})); }
            if (values.path) { const e=root.querySelector('[data-molsysviewer-work-file-path]'); e.value=values.path; e.dispatchEvent(new Event('input',{bubbles:true})); }
            return true;
        })()"""
        )

    async def click(selector):
        await js(
            """(() => {const e=document.querySelector("""
            + json.dumps(selector)
            + """); if(!e || e.disabled) throw new Error('Missing/disabled button'); e.click(); return true;})()"""
        )

    async def camera():
        return await js("window.__molsysviewerDocsController.getCameraSnapshot()")

    async def rotate():
        nonlocal rotation_index
        rotation_index += 1
        await js("(() => {window.__molsysviewerDocsController.setPanelMode('navigate',false);return true;})()")
        before = await camera()
        await js("""(() => {
            window.__nativeInput=[];
            if(window.__nativeInputObserved)return true;
            window.__nativeInputObserved=true;
            for (const type of ['pointerdown','pointermove','pointerup','mousedown','mousemove','mouseup']) {
                document.addEventListener(type,e=>window.__nativeInput.push({type,buttons:e.buttons,
                    button:e.button,x:e.clientX,y:e.clientY,target:e.target.tagName,trusted:e.isTrusted,at:performance.now()}),{capture:true});
            }
            return true;
        })()""")
        rect = await js(
            "(() => {const r=document.querySelector('canvas').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};})()"
        )
        start = QPoint(round(rect["x"] + rect["w"] * 0.51), round(rect["y"] + rect["h"] * 0.65))
        finish = QPoint(round(rect["x"] + rect["w"] * 0.73), round(rect["y"] + rect["h"] * 0.73))
        assert await js(f"document.elementFromPoint({start.x()},{start.y()}).tagName === 'CANVAS'")
        window.activateWindow()
        web.setFocus()
        target = web.focusProxy() or web
        widget_info = {
            "target_class": target.metaObject().className(),
            "target_size": [target.width(), target.height()],
            "web_size": [web.width(), web.height()],
            "window_active": window.isActiveWindow(),
            "target_focus": target.hasFocus(),
            "start": [start.x(), start.y()],
            "finish": [finish.x(), finish.y()],
            "canvas_rect": rect,
        }
        QTest.mouseMove(target, start)
        await asyncio.sleep(0.05)
        QTest.mousePress(target, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start)
        await asyncio.sleep(0.05)
        for step in range(1, 15):
            point = QPoint(
                round(start.x() + (finish.x() - start.x()) * step / 14),
                round(start.y() + (finish.y() - start.y()) * step / 14),
            )
            QTest.mouseMove(target, point, 3)
            await asyncio.sleep(0.02)
        QTest.mouseRelease(target, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, finish)
        await asyncio.sleep(0.05)
        encoded = json.dumps(before)
        try:
            await wait_js(
                "(() => {const a=window.__molsysviewerDocsController.getCameraSnapshot(),b="
                + encoded
                + ";return ['position','target','up'].some(k=>a[k].some((v,i)=>Math.abs(v-b[k][i])>1e-4));})()",
                "actual-native-rotation",
                timeout=5,
            )
        finally:
            (out / f"input-{rotation_index}.json").write_text(
                json.dumps(
                    {
                        "widget": widget_info,
                        "before": before,
                        "after": await camera(),
                        "events": await js("window.__nativeInput"),
                    },
                    indent=2,
                )
            )
        return before

    def saved_state(path, kind):
        if kind == "state":
            return json.loads(path.read_text())
        with zipfile.ZipFile(path) as archive:
            assert "structure.h5msm" in archive.namelist()
            return json.loads(archive.read("state.json"))

    async def restore(path, kind, saved):
        await rotate()
        altered = await camera()
        assert altered["position"] != saved["view"]["camera"]["position"]
        changed_frame = (saved["view"]["structure_index"] + 1) % 3
        view.player.go_to_structure(changed_frame)
        await idle()
        assert (
            await js("window.__molsysviewerDocsController.trajectory.getTrajectoryState().currentFrame")
            == changed_frame
        )
        await open_work(path, kind)
        draw_start = await js("window.__nativeDrawSequence")
        start = len(inbound)
        await click("[data-molsysviewer-work-file-restore]")
        await click("[data-molsysviewer-work-file-confirm]")
        await wait(
            lambda: any(
                m.get("op") == "studio_action_result" and m.get("action") == "restore_work_file"
                for m in inbound[start:]
            ),
            "restore-verdict",
        )
        verdict = next(
            m
            for m in inbound[start:]
            if m.get("op") == "studio_action_result" and m.get("action") == "restore_work_file"
        )
        assert verdict["ok"], verdict
        expected = json.dumps(saved["view"])
        await wait_js(
            "(() => {const c=window.__molsysviewerDocsController,a=c.getCameraSnapshot(),b="
            + expected
            + ";return c.trajectory.getTrajectoryState().currentFrame===b.structure_index && ['position','target','up'].every(k=>a[k].every((v,i)=>Math.abs(v-b.camera[k][i])<1e-5));})()",
            "restored-camera-and-changed-frame",
        )
        await wait_js(
            "(() => {const b="
            + expected
            + ",start="
            + str(draw_start)
            + ";return window.__nativeDrawRecords.some(d=>d.sequence>start && d.frame===b.structure_index && ['position','target','up'].every(k=>d.camera[k].every((v,i)=>Math.abs(v-b.camera[k][i])<1e-5)));})()",
            "fresh-restored-native-draw",
        )
        await idle()
        assert view.player.index == saved["view"]["structure_index"]
        assert await js("!document.querySelector('[data-molsysviewer-work-file-path]').disabled")
        return {
            "perturbed_camera": True,
            "changed_frame": changed_frame,
            "restored_frame": view.player.index,
            "fresh_restored_draw": True,
        }

    async def exercise():
        report = {
            "scope": "automated native Qt/WebEngine/Mol*; not human acceptance",
            "cases": [],
            "owner_thread": owner_thread,
        }
        try:
            await idle()
            report["platform"] = app.platformName()
            report["rendering"] = await js(
                """(() => {const c=window.__molsysviewerDocsController,canvas=c.plugin.canvas3d;const g=canvas?.webgl.gl;const e=g?.getExtension('WEBGL_debug_renderer_info');return {canvas:!!canvas,webgl2:!!g&&g instanceof WebGL2RenderingContext,renderer:e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):g?.getParameter(g.RENDERER),version:g?.getParameter(g.VERSION)};})()"""
            )
            assert report["rendering"]["canvas"] and report["rendering"]["webgl2"]
            await js("""(() => {const c=window.__molsysviewerDocsController;
                window.__nativeDrawSequence=0;window.__nativeDrawRecords=[];let replay=true;
                window.__nativeDrawSubscription=c.plugin.canvas3d.didDraw.subscribe(()=>{if(replay)return;
                    window.__nativeDrawRecords.push({sequence:++window.__nativeDrawSequence,
                        camera:c.getCameraSnapshot(),frame:c.trajectory.getTrajectoryState().currentFrame});
                    if(window.__nativeDrawRecords.length>256)window.__nativeDrawRecords.shift();
                });replay=false;return true;
            })()""")
            view.annotations.add("native capture", atom_indices=[0], tag="qt-note")
            await idle()
            for kind in ("state", "session"):
                for source in ("studio", "python-async"):
                    phases.append(f"{source}-{kind}")
                    print("PHASE " + phases[-1], flush=True)
                    view.player.go_to_structure((view.player.index + 1) % 3)
                    await idle()
                    await rotate()
                    path = out / f"{source}-{kind}.{'json' if kind == 'state' else 'msv'}"
                    start_events, start_inbound, start_beats = len(events), len(inbound), len(beats)
                    if source == "studio":
                        await open_work(path, kind)
                        await click("[data-molsysviewer-work-file-save]")
                        await wait(
                            lambda start=start_inbound: any(
                                m.get("op") == "studio_action_result" and m.get("action") == "save_work_file"
                                for m in inbound[start:]
                            ),
                            "save-verdict",
                        )
                        result = next(
                            m
                            for m in inbound[start_inbound:]
                            if m.get("op") == "studio_action_result" and m.get("action") == "save_work_file"
                        )
                        assert result["ok"], result
                        await wait_js(
                            "!document.querySelector('[data-molsysviewer-work-file-path]').disabled && /Saved/.test(document.querySelector('[data-molsysviewer-work-file-status]').textContent)",
                            "save-controls",
                        )
                    else:
                        operation = view.save_state_async if kind == "state" else view.save_session_async
                        await operation(path, timeout=10)
                    captures = [e for e in events[start_events:] if e.get("event") == "visual_state_snapshot"]
                    assert len(captures) == 1 and captures[0]["ok"], captures
                    reply = captures[0]
                    requests = [m for m in inbound[start_inbound:] if m.get("op") == "request_visual_state"]
                    assert len(requests) == 1 and reply["request_id"] == requests[0]["request_id"]
                    saved = saved_state(path, kind)
                    assert saved["view"]["camera"] == reply["snapshot"]
                    assert saved["view"]["structure_index"] == reply["structure_index"]
                    assert any(x["tag"] == "qt-note" for x in saved["annotations"])
                    assert len(beats) > start_beats and set(beats) == {owner_thread}
                    restored = await restore(path, kind, saved)
                    report["cases"].append(
                        {
                            "source": source,
                            "kind": kind,
                            "exact_correlated_camera": True,
                            "heartbeat_progress": len(beats) - start_beats,
                            **restored,
                        }
                    )
            phases.append("cancel-before-draw")
            print("PHASE " + phases[-1], flush=True)
            path = out / "cancelled.json"
            await open_work(path, "state")
            start_events, start_inbound = len(events), len(inbound)
            await js("""(() => {const c=window.__molsysviewerDocsController,canvas=c.plugin.canvas3d;
                window.__captureDrawProbe={draws:0,requests:0};let replay=true;
                const subscription=canvas.didDraw.subscribe(()=>{if(!replay)window.__captureDrawProbe.draws++;});replay=false;
                const original=canvas.requestDraw.bind(canvas);canvas.requestDraw=(...args)=>{window.__captureDrawProbe.requests++;return original(...args);};
                window.__releaseCaptureDraw=()=>{subscription.unsubscribe();canvas.requestDraw=original;c.plugin.animationLoop.start();};
                c.plugin.animationLoop.stop({noDraw:true});return true;
            })()""")
            await click("[data-molsysviewer-work-file-save]")
            await wait(
                lambda: any(m.get("op") == "request_visual_state" for m in inbound[start_inbound:]),
                "pending-draw-capture",
            )
            await wait_js("window.__captureDrawProbe.requests>0", "draw-wait-started")
            capture = next(m for m in inbound[start_inbound:] if m.get("op") == "request_visual_state")
            started = time.monotonic()
            await click("[data-molsysviewer-work-file-cancel]")
            await wait_js(
                "!document.querySelector('[data-molsysviewer-work-file-path]').disabled && /cancelled/i.test(document.querySelector('[data-molsysviewer-work-file-status]').textContent)",
                "cancel-unlock-before-draw",
                timeout=2,
            )
            assert await js("window.__captureDrawProbe.draws") == 0
            assert not path.exists() and not view._frontend_requests._pending and not view._work_file_saves._pending
            assert any(
                m.get("op") == "cancel_visual_state"
                and m.get("request_id") == capture["request_id"]
                and m.get("capture_revision") == capture["capture_revision"]
                for m in inbound[start_inbound:]
            )
            assert not any(
                e.get("event") == "visual_state_snapshot" and e.get("request_id") == capture["request_id"]
                for e in events[start_events:]
            )
            report["cancel_before_draw"] = {
                "unlocked_seconds": time.monotonic() - started,
                "draws": 0,
                "no_file": True,
                "exact_abort": True,
            }
            await js("(() => {window.__releaseCaptureDraw();return true;})()")
            await idle()
            await asyncio.sleep(0.1)
            assert not path.exists()
            assert not any(
                e.get("event") == "visual_state_snapshot" and e.get("request_id") == capture["request_id"]
                for e in events[start_events:]
            )
            report["cancel_before_draw"]["late_resume_no_revive"] = True
            from tests._qt_moving_capture import exercise_qt_moving_capture

            await exercise_qt_moving_capture(
                view=view,
                bridge=bridge,
                js=js,
                wait=wait,
                wait_js=wait_js,
                open_work=open_work,
                click=click,
                saved_state=saved_state,
                report=report,
                out=out,
                beats=beats,
            )
            from tests._qt_background_capture import exercise_qt_background_capture

            await exercise_qt_background_capture(
                view=view,
                window=window,
                web=web,
                js=js,
                idle=idle,
                wait=wait,
                wait_js=wait_js,
                saved_state=saved_state,
                report=report,
                out=out,
                events=events,
                inbound=inbound,
                beats=beats,
            )
            phases.append("constructor-write-failure")
            print("PHASE " + phases[-1], flush=True)
            import gc

            existing = {id(item) for item in gc.get_objects() if isinstance(item, msv.MolSysView)}
            shell_state = out / "shell-state.json"
            original_state = shell_state.read_bytes() if shell_state.exists() else None
            blocked = out / "caller-owned-directory.html"
            blocked.mkdir()
            marker = blocked / "keep.txt"
            marker.write_bytes(b"caller-owned destination")
            try:
                qt.create_standalone_qt0_window(None, output_filename=str(blocked), apply_project_config=False)
            except IsADirectoryError:
                pass
            else:
                raise AssertionError("A directory must not be overwritten as a Qt shell.")
            # Observe before GC/global cleanup: failed construction owns only its
            # new View and must leave the running host and prior state alone.
            failed_views = [
                item for item in gc.get_objects() if isinstance(item, msv.MolSysView) and id(item) not in existing
            ]
            assert all(item.closed and item.widget._bridge._closed for item in failed_views)
            assert (shell_state.read_bytes() if shell_state.exists() else None) == original_state
            assert marker.read_bytes() == b"caller-owned destination"
            assert not view.closed and window.isVisible()
            report["constructor_failure"] = {
                "native_writer_error": "IsADirectoryError",
                "new_views_closed_before_global_cleanup": True,
                "prior_shell_state_unchanged": True,
                "caller_destination_unchanged": True,
                "existing_host_preserved": True,
            }
            phases.append("project-configuration-before-owner")
            print("PHASE " + phases[-1], flush=True)
            import os

            from molsysviewer import config

            configured = out / "configured-project"
            configured.mkdir()
            (configured / "_molsysviewer.py").write_text(
                "from molsysviewer import config\nconfig.viewer_mode = 'cinema'\n"
            )
            prior_directory, prior_mode = Path.cwd(), config.viewer_mode
            child_runtime = None
            try:
                os.chdir(configured)
                child_runtime = qt.create_standalone_qt0_window(
                    None, output_filename=str(configured / "shell.html"), apply_project_config=True
                )
                configured_view = child_runtime["webview"]._molsysviewer_view
                assert configured_view.widget.viewer_mode == "cinema"
                assert configured_view.widget.runtime_session_id == configured_view._binary_session_id
                report["project_configuration"] = {"viewer_mode": "cinema", "owner_identity_bound": True}
            finally:
                os.chdir(prior_directory)
                config.viewer_mode = prior_mode
                if child_runtime is not None:
                    child_runtime["window"].close()
            report["loop"] = type(asyncio.get_running_loop()).__name__
            report["heartbeat_count"] = len(beats)
            report["failed_deliveries"] = bridge.failed_deliveries
            report["frontend_diagnostics"] = frontend_diagnostics
            report["providers"] = {
                "viewer_module": msv.__file__,
                "viewer_version": msv.__version__,
                "qt_binding": binding,
                "python": sys.version,
            }
            assert not bridge.failed_deliveries
            assert not frontend_diagnostics, frontend_diagnostics
            window.grab().save(str(out / "native-final.png"))
            return report
        except BaseException:
            report["phases"] = phases
            report["error"] = traceback.format_exc()
            (out / "partial-report.json").write_text(json.dumps(report, indent=2))
            raise
        finally:
            checkpoint("main-finally-entered")
            heartbeat.stop()
            checkpoint("before-window-close")
            window.close()
            checkpoint("after-window-close")
            await asyncio.sleep(0.1)
            checkpoint("after-cleanup-yield")
            report["closed"] = view.closed and bridge._closed and not bridge._controls
            (out / "events.json").write_text(json.dumps({"inbound": inbound, "events": events}, indent=2))

    try:
        loop = QtAsyncio.QAsyncioEventLoop(app)

        async def owned_application():
            try:
                return await exercise()
            finally:
                pending = asyncio.all_tasks(loop) - {asyncio.current_task()}
                for task in pending:
                    task.cancel()
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
                checkpoint("before-asyncgens-shutdown-in-live-loop")
                await loop.shutdown_asyncgens()
                checkpoint("before-executor-shutdown-in-live-loop")
                await loop.shutdown_default_executor()
                checkpoint("after-shutdown-in-live-loop")

        task = loop.create_task(owned_application())
        task.add_done_callback(lambda _: loop.stop())
        checkpoint("before-owned-loop")
        loop.run_forever()
        checkpoint("after-owned-loop")
        try:
            report = task.result()
            (out / "pre-exit-report.json").write_text(json.dumps(report, indent=2))
        finally:
            loop.close()
            checkpoint("after-owned-loop-close")
        (out / "report.json").write_text(json.dumps(report, indent=2))
        assert report["closed"]
        print("NATIVE_CAPTURE_JSON " + json.dumps(report), flush=True)
    finally:
        checkpoint("outer-finally")
        selected.close()
        original.close()
        checkpoint("outer-finally-complete")


if __name__ == "__main__":
    faulthandler.enable()
    faulthandler.dump_traceback_later(200)
    try:
        main(Path(sys.argv[1]))
    finally:
        faulthandler.cancel_dump_traceback_later()
