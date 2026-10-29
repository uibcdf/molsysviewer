"""Native child for #270; owns its shell, state, figures and live Qt window."""


def main():

    import json
    import sys
    import time
    from pathlib import Path

    import molsysviewer.standalone_qt as qt
    from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QFileDialog

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)

    import molsysmt as msm

    import molsysviewer as msv

    out = Path(sys.argv[1])
    qt._qt_shell_state_path = lambda: out / "shell-state.json"
    first, second = msv.demo["dialanine"], msv.demo["pentalanine"]
    runtime = qt.create_standalone_qt0_window(
        first, output_filename=str(out / "shell.html"), apply_project_config=False
    )
    app, window, web = runtime["app"], runtime["window"], runtime["webview"]
    view, bridge = web._molsysviewer_view, web._molsysviewer_qt_bridge
    window.show()

    def wait(predicate, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            app.processEvents()
            if predicate():
                return
            time.sleep(0.01)
        raise AssertionError(
            f"Qt workbench timed out: {window.statusBar().currentMessage()}; failed={bridge.failed_deliveries}"
        )

    def idle():
        wait(lambda: bridge.ready and not bridge.queue and bridge.inflight is None)

    def evaluate(script):
        result = []
        web.page().runJavaScript("JSON.stringify(" + script + ")", result.append)
        wait(lambda: bool(result))
        return json.loads(result[0]) if isinstance(result[0], str) and result[0] else result[0]

    try:
        print("initial-ready", flush=True)
        idle()
        report = {
            "authority": evaluate("window.__molsysviewerDocsController.hasPythonAuthority()"),
            "provider_file": msm.__file__,
        }
        # Use the shared real context-menu form; no native replacement or fake UI.
        evaluate("""(() => {
            const c = window.__molsysviewerDocsController;
            c.contextMenu.open({event:'interaction_context_menu',kind:'structure',atom_indices:[0,1]},120,120,[]);
            document.querySelector('[data-molsysviewer-context-submenu="Create"]').click();
            document.querySelector('[data-molsysviewer-context-action="create_region_from_target"]').click();
            document.querySelector('input[placeholder="Region tag (optional)"]').value='qt-region';
            [...document.querySelectorAll('button')].find(x=>x.textContent==='Create Region').click();
        })()""")
        wait(lambda: "qt-region" in view.regions)
        idle()
        report["region_atoms"] = list(view.regions["qt-region"].atom_indices)

        def download(script, filename, *, cancel=False):
            selected = []
            timer = QTimer(window)
            timer.setInterval(20)

            def choose():
                dialog = QApplication.activeModalWidget()
                if not isinstance(dialog, QFileDialog):
                    return
                timer.stop()
                if cancel:
                    dialog.reject()
                else:
                    # Select the directory and filename explicitly, then verify
                    # the actual modal result before accepting written bytes.
                    dialog.setDirectory(str(out))
                    dialog.selectFile(filename)
                    dialog.accept()
                choice = {"title": dialog.windowTitle(), "files": dialog.selectedFiles(), "result": dialog.result()}
                print("download-dialog", choice, flush=True)
                selected.append(choice)

            timer.timeout.connect(choose)
            timer.start()
            if callable(script):
                script()
            else:
                evaluate(script)
            wait(lambda: bool(selected))
            if not cancel:
                assert selected[0]["result"] == QFileDialog.DialogCode.Accepted, selected
                assert selected[0]["files"] == [str(out / filename)], selected
            wait(lambda: not window._molsysviewer_downloads)
            if cancel:
                assert not (out / filename).exists()
            else:
                try:
                    wait(lambda: (out / filename).exists())
                except AssertionError as error:
                    raise AssertionError(
                        f"{error}; dialog={selected}; outputs={sorted(p.name for p in out.iterdir())}"
                    ) from error
            timer.stop()

        download(
            """(() => {
            const c=window.__molsysviewerDocsController;
            c.setPanelMode('navigate',true); c.groupPanel.openSection('export');
            document.querySelector('[data-molsysviewer-export-html="true"]').click();
        })()""",
            "studio-view.html",
        )
        assert "qt-region" in (out / "studio-view.html").read_text()
        download(
            """(() => {
            const link=document.createElement('a');
            link.href=URL.createObjectURL(new Blob(['cancelled'],{type:'text/plain'}));
            link.download='cancelled.txt'; link.click();
        })()""",
            "cancelled.txt",
            cancel=True,
        )
        print("downloads-completed", flush=True)
        native_export = (
            next(action for action in window.menuBar().actions() if action.text() == "Export").menu().actions()[0]
        )
        download(native_export.trigger, "native-view.html")
        native_html = (out / "native-view.html").read_text()
        assert "qt-region" in native_html and 'id="molsysviewer-runtime-source"' in native_html
        import re

        assert not re.search(r'["\']host_event_transport["\']\s*:\s*["\']url-scheme["\']', native_html)
        report["native_download_and_cancel"] = True
        view.set_panel_mode(None, expanded=False)
        idle()
        report["camera_received"] = view._request_camera_snapshot(timeout_s=3)
        image = view._request_image_export(width_px=320, height_px=240, timeout_s=10)
        assert image and image.get("data_uri", "").startswith("data:image/png;base64,"), image
        report["image_received"] = True
        view.widget.viewer_mode = "cinema"
        idle()
        report["python_mode"] = evaluate("window.__molsysviewerDocsController.getViewerMode()")
        evaluate("""(() => {
            const c=window.__molsysviewerDocsController;
            c.contextMenu.open({event:'interaction_context_menu',kind:'empty'},120,120,[]);
            document.querySelector('[data-molsysviewer-context-submenu="View"]').click();
            [...document.querySelectorAll('[data-molsysviewer-context-action="set_viewer_mode"]')].find(x=>x.textContent.startsWith('Standard')).click();
        })()""")
        wait(lambda: view.widget.viewer_mode == "standard")
        report["browser_mode"] = view.widget.viewer_mode
        view.widget.autohide_controls = False
        idle()
        position = evaluate("""(() => {
            const r=document.querySelector('button[title="Fullscreen"]').getBoundingClientRect();
            return [Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)];
        })()""")
        QTest.mouseClick(
            web.focusProxy() or web, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(*position)
        )
        wait(lambda: window.isFullScreen() and evaluate("Boolean(document.fullscreenElement)"))
        window.activateWindow()
        web.setFocus()
        # Deliver to WebEngine directly: Xvfb has no window manager to grant
        # native activation, but the canvas keyboard behavior must still work.
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_Escape)
        wait(lambda: not window.isFullScreen())
        report["fullscreen_roundtrip"] = True
        print("fullscreen-completed", flush=True)
        report["loads"] = []
        for i in range(10):
            source = first if i % 2 == 0 else second
            qt._load_molecular_system_into_qt_host(
                source,
                window=window,
                webview=web,
                current_state={"base_title": "Qt review"},
                loaded_label="review",
                status_message="Loading review system",
            )
            idle()
            atoms = evaluate(
                "window.__molsysviewerDocsController.plugin.managers.structure.hierarchy.current.structures.map(x=>x.cell.obj.data.elementCount)"
            )
            assert len(atoms) == 1, atoms
            report["loads"].append(atoms[0])
            window.grab().save(str(out / f"system-{i}.png"))
        import imageio.v2 as imageio
        import numpy as np

        changes = []
        for i in range(9):
            before, after = (imageio.imread(out / f"system-{j}.png") for j in (i, i + 1))
            h, w = before.shape[:2]
            a = before[h // 5 : 4 * h // 5, w // 5 : 4 * w // 5, :3].astype(float)
            b = after[h // 5 : 4 * h // 5, w // 5 : 4 * w // 5, :3].astype(float)
            changed = float(np.mean(np.max(np.abs(a - b), axis=2) > 25))
            assert changed > 0.005, f"The native window still shows the previous system ({i=}, {changed=})"
            changes.append(changed)
        report["changed_molecular_pixels"] = min(changes)
        assert view._request_camera_snapshot(timeout_s=3)
        ticks = []
        timer = QTimer(window)
        timer.setInterval(10)
        timer.timeout.connect(lambda: ticks.append(True))
        timer.start()
        received_frames = []
        view.widget.on_msg(
            lambda _widget, event, _buffers: (
                received_frames.append(event) if event.get("event") == "movie_frame" else None
            )
        )
        view.movie.add_camera_orbit(duration_ms=1000, n_keyframes=4)
        movie = view.movie.export(out / "orbit.gif", fps=2, width_px=240, height_px=160, timeout_s=30)
        timer.stop()
        import imageio.v2 as imageio

        assert len(received_frames) == 3
        import base64
        import io

        raw = [imageio.imread(io.BytesIO(base64.b64decode(f["data_uri"].split(",", 1)[1]))) for f in received_frames]
        opposite = float(np.mean(np.abs(raw[0].astype(float) - raw[1].astype(float))))
        assert opposite > 1, f"The half-orbit image still uses the previous camera ({opposite=})"
        report["movie_camera_image_difference"] = opposite
        decoded = imageio.mimread(movie)
        # GIF encoders can coalesce identical viewpoints in a complete orbit.
        assert len(decoded) >= 2
        assert all(frame.shape[:2] == (160, 240) and frame.std() > 1 for frame in decoded)
        assert ticks, "Movie export blocked the Qt event loop"
        report["movie_frames"] = len(received_frames)
        report["timeout_without_reply"] = (
            view._wait_for_frontend_reply("_last_image_export_event", view._last_image_export_event, 0.05) is None
        )
        report["failed_deliveries"] = bridge.failed_deliveries
        print("movie-completed", flush=True)
        other = qt.create_standalone_qt0_window(second, apply_project_config=False)
        print("second-host-created", flush=True)
        other["window"].show()
        other_bridge = other["webview"]._molsysviewer_qt_bridge
        other_view = other["webview"]._molsysviewer_view
        wait(lambda: other_bridge.ready and not other_bridge.queue and other_bridge.inflight is None)
        assert other["webview"].page().profile() is not web.page().profile()
        implicit_html = Path(other["html_path"])
        assert implicit_html.exists()
        print("second-host-ready", flush=True)
        other["window"].close()
        print("second-host-closed", flush=True)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        print("deletions-processed", flush=True)
        assert other_view.closed and not implicit_html.exists()
        try:
            other_bridge.send({"op": "clear_all"})
        except RuntimeError:
            pass
        else:
            raise AssertionError("Closed host accepted a new send")
        assert not view.closed
        assert view._request_camera_snapshot(timeout_s=3)
        report["independent_host_and_cleanup"] = True
        (out / "report.json").write_text(json.dumps(report, indent=2))
    finally:
        view.close()
        first.close()
        second.close()
        window.close()
        app.processEvents()


if __name__ == "__main__":
    import faulthandler

    faulthandler.enable()
    faulthandler.dump_traceback_later(150)
    try:
        main()
    finally:
        faulthandler.cancel_dump_traceback_later()
