"""Native child for #270; owns its shell, state, figures and live Qt window."""


def main():

    import json
    import sys
    import time
    from pathlib import Path

    import molsysviewer.standalone_qt as qt
    from molsysviewer.standalone_qt.utils import _show_status
    from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt, QTimer
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QDialogButtonBox, QFileDialog, QLineEdit

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

    def evaluate(script, target=web):
        result = []
        target.page().runJavaScript("JSON.stringify(" + script + ")", result.append)
        wait(lambda: bool(result))
        return json.loads(result[0]) if isinstance(result[0], str) and result[0] else result[0]

    try:
        print("initial-ready", flush=True)
        idle()
        report = {
            "authority": evaluate("window.__molsysviewerDocsController.hasPythonAuthority()"),
            "provider_file": msm.__file__,
            "qt_platform": app.platformName(),
            "initial_binary_projection": not view._current_molecular_projection.is_materialized,
        }
        assert report["initial_binary_projection"], "Initial Qt data unnecessarily materialized numeric JSON"
        assert web._molsysviewer_qt_payload_handler.served
        chrome = window._molsysviewer_chrome
        QApplication.setActiveWindow(window)
        web.setFocus()
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_H)
        wait(
            lambda: (
                evaluate("getComputedStyle(document.querySelector('.molsysviewer-help-card').parentElement).display")
                == "flex"
            ),
            timeout=3,
        )
        evaluate(
            "(() => {window.__helpPainted=false; requestAnimationFrame(()=>requestAnimationFrame(()=>window.__helpPainted=true));})()"
        )
        wait(lambda: evaluate("window.__helpPainted"))
        window.grab().save(str(out / "help-native.png"))
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)
        assert (
            evaluate("getComputedStyle(document.querySelector('.molsysviewer-help-card').parentElement).display")
            == "flex"
        )
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_H, Qt.KeyboardModifier.ShiftModifier)
        wait(
            lambda: (
                evaluate("getComputedStyle(document.querySelector('.molsysviewer-help-card').parentElement).display")
                == "none"
            ),
            timeout=3,
        )
        report["help_keyboard"] = True
        assert window.menuWidget() is None, "The native host must not duplicate the canvas menus"
        assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
        assert chrome.header.isVisible() and not window.statusBar().isVisible()
        assert not chrome.status.isVisible(), "Idle status must not occupy a permanent bar"
        assert chrome.buttons["close"].accessibleName() == "Close window"
        assert chrome.frame.edges(QPoint(0, 0)) == (Qt.Edge.LeftEdge | Qt.Edge.TopEdge)
        geometry = window.geometry()
        QTest.mouseClick(chrome.buttons["maximize"], Qt.MouseButton.LeftButton)
        wait(window.isMaximized)
        if app.platformName() == "wayland":
            # QWidget's requested flag precedes the compositor's configure.
            # Receive the real resize before sending a second window gesture.
            wait(lambda: window.geometry().size() != geometry.size())
        assert chrome.buttons["maximize"].accessibleName() == "Restore window"
        QTest.mouseDClick(chrome.header, Qt.MouseButton.LeftButton, pos=QPoint(200, 15))
        wait(lambda: not window.isMaximized())
        wait(lambda: window.geometry().size() == geometry.size())
        QTest.keyClick(QApplication.focusWidget() or web, Qt.Key.Key_H)
        wait(
            lambda: (
                evaluate("getComputedStyle(document.querySelector('.molsysviewer-help-card').parentElement).display")
                == "flex"
            ),
            timeout=3,
        )
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_Escape)
        wait(
            lambda: (
                evaluate("getComputedStyle(document.querySelector('.molsysviewer-help-card').parentElement).display")
                == "none"
            ),
            timeout=3,
        )
        _show_status(window, "Could not load the selected source.", kind="error")
        assert chrome.status.isVisible() and "Could not" in chrome.status.text()
        _show_status(window, "Ready.", kind="ready")
        assert not chrome.status.isVisible()
        report["modern_window_chrome"] = True
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
                    # Exercise the visible editor: selectFile() can preserve an
                    # already focused editor's proposed name (seen on hosted Qt).
                    dialog.setDirectory(str(out))
                    editor = dialog.findChild(QLineEdit, "fileNameEdit")
                    assert editor is not None
                    editor.setFocus()
                    editor.selectAll()
                    QTest.keyClicks(editor, filename)
                    buttons = dialog.findChild(QDialogButtonBox, "buttonBox")
                    assert buttons is not None
                    save = buttons.button(QDialogButtonBox.StandardButton.Save)
                    assert save is not None
                    QTest.mouseClick(save, Qt.MouseButton.LeftButton)
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
        actions = window._molsysviewer_host_actions
        assert actions["open_file"].shortcut().toString() == "Ctrl+O"
        assert actions["new_view"].shortcut().toString() == "Ctrl+N"
        assert actions["studio"].shortcut().toString() == "Ctrl+1"
        assert actions["addons"].shortcut().toString() == "Ctrl+2"
        assert actions["restore_last"].shortcut().toString() == "Ctrl+Shift+R"
        assert actions["status_details"].shortcut().toString() == "Ctrl+Shift+D"
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_H)
        wait(
            lambda: (
                evaluate("getComputedStyle(document.querySelector('.molsysviewer-help-card').parentElement).display")
                == "flex"
            )
        )
        # Help is shared, but desktop capabilities are present only in this host.
        assert "Ctrl+Shift+D" in evaluate("document.querySelector('[data-molsysviewer-host-shortcuts]').textContent")
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_Escape)
        report["host_shortcut_help"] = True

        def native_export_shortcut():
            QApplication.setActiveWindow(window)
            web.setFocus()
            QTest.keyClick(web, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)

        download(native_export_shortcut, "native-view.html")
        report["native_shortcuts"] = True
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
        detail_message = "Download interrupted: " + "a long file name " * 30
        _show_status(window, detail_message, kind="error")
        wait(chrome.fullscreen_status.isVisible)
        QTest.mouseClick(chrome.fullscreen_status, Qt.MouseButton.LeftButton)
        wait(lambda: chrome.details is not None and chrome.details.isVisible())
        from PySide6.QtWidgets import QPlainTextEdit, QPushButton

        assert chrome.details.findChild(QPlainTextEdit, "molsysviewerStatusText").toPlainText() == detail_message
        QTest.mouseClick(chrome.details.findChild(QPushButton, "molsysviewerCopyStatus"), Qt.MouseButton.LeftButton)
        assert QApplication.clipboard().text() == detail_message
        chrome.details.close()
        wait(lambda: chrome.details is None)
        assert window.isFullScreen() and evaluate("Boolean(document.fullscreenElement)")
        _show_status(window, "Ready.", kind="ready")
        report["fullscreen_status_details"] = True
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_H)
        wait(
            lambda: (
                evaluate("getComputedStyle(document.querySelector('.molsysviewer-help-card').parentElement).display")
                == "flex"
            )
        )
        help_bounds = evaluate("""(() => {
            const card=document.querySelector('.molsysviewer-help-card'), r=card.getBoundingClientRect(),
            host=card.parentElement.getBoundingClientRect();
            return {width:r.width, height:r.height, hostWidth:host.width, hostHeight:host.height,
                font:parseFloat(getComputedStyle(card).fontSize),
                columns:getComputedStyle(card.querySelector('.molsysviewer-help-grid')).gridTemplateColumns.split(' ').length};
        })()""")
        assert 0 < help_bounds["width"] <= help_bounds["hostWidth"]
        assert 0 < help_bounds["height"] <= help_bounds["hostHeight"]
        report["help_layout"] = help_bounds
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_Escape)
        wait(
            lambda: (
                evaluate("getComputedStyle(document.querySelector('.molsysviewer-help-card').parentElement).display")
                == "none"
            )
        )
        assert window.isFullScreen(), "Escape closes Help before leaving fullscreen"
        window.activateWindow()
        web.setFocus()
        # Deliver to WebEngine directly: Xvfb has no window manager to grant
        # native activation, but the canvas keyboard behavior must still work.
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_Escape)
        wait(lambda: not window.isFullScreen())
        report["fullscreen_roundtrip"] = True
        assert chrome.header.isVisible() and window.menuWidget() is None
        assert not window.statusBar().isVisible()

        # Exercise the visible Load workspace through genuine WebEngine input.
        def web_click(selector):
            evaluate(
                "(() => {window.__clickPainted=false; requestAnimationFrame(()=>requestAnimationFrame(()=>window.__clickPainted=true));})()"
            )
            wait(lambda: evaluate("window.__clickPainted"))
            target = evaluate(
                """(() => {
                const element=document.querySelector("""
                + json.dumps(selector)
                + """);
                if (!element) throw Error('Missing visible control');
                element.scrollIntoView({block:'nearest'});
                const r=element.getBoundingClientRect(), x=r.x+r.width/2, y=r.y+r.height/2;
                const hit=document.elementFromPoint(x,y);
                return {x,y,visible:r.width>0&&r.height>0&&(hit===element||element.contains(hit))};
            })()"""
            )
            assert target["visible"], f"Control is hidden or obscured: {selector}"
            QTest.mouseClick(
                web.focusProxy() or web,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(target["x"]), round(target["y"])),
            )
            app.processEvents()

        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_1, Qt.KeyboardModifier.ControlModifier)
        web_click('[data-molsysviewer-group-panel-tab="load"]')
        wait(
            lambda: (
                evaluate(
                    "document.querySelector('[data-molsysviewer-group-panel-tab=load]').getAttribute('aria-current')"
                )
                == "page"
            )
        )
        source_path = str(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
        field_selector = '[data-molsysviewer-load-source="0"] [data-molsysviewer-load-field="source"]'
        dialog_errors = []
        dialog_answers = []
        picker_events = []
        view.widget.on_msg(
            lambda _widget, event, _buffers: (
                picker_events.append(event) if event.get("action") == "browse_load_files" else None
            )
        )

        def answer_file_dialog(accept):
            deadline = time.monotonic() + 10

            def answer():
                dialog = app.activeModalWidget()
                if not isinstance(dialog, QFileDialog):
                    if time.monotonic() < deadline:
                        QTimer.singleShot(30, answer)
                    else:
                        dialog_errors.append("No native file picker appeared")
                    return
                buttons = dialog.findChild(QDialogButtonBox)
                if accept:
                    dialog.selectFile(source_path)
                    button = buttons.button(QDialogButtonBox.StandardButton.Open)
                else:
                    button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
                dialog_answers.append(accept)

            QTimer.singleShot(30, answer)

        before_atoms = int(msm.get(view.molsys, n_atoms=True))
        answer_file_dialog(False)
        web_click('[data-molsysviewer-load-browse="0"]')
        wait(
            lambda: (
                bool(dialog_errors)
                or (
                    dialog_answers == [False]
                    and evaluate(
                        "getComputedStyle(document.querySelector('[data-molsysviewer-load-file-picker]')).display"
                    )
                    == "none"
                )
            )
        )
        if dialog_errors:
            window.grab().save(str(out / "file-picker-failure.png"))
        assert not dialog_errors, {
            "errors": dialog_errors,
            "picker_events": picker_events,
            "dom": evaluate(
                "({picker:document.querySelector('[data-molsysviewer-load-file-picker]').style.display,active:document.activeElement.tagName})"
            ),
        }
        assert evaluate("document.querySelector(" + json.dumps(field_selector) + ").value") == ""
        assert int(msm.get(view.molsys, n_atoms=True)) == before_atoms
        report["native_file_picker_cancelled"] = True
        answer_file_dialog(True)
        web_click('[data-molsysviewer-load-browse="0"]')
        wait(
            lambda: (
                bool(dialog_errors)
                or evaluate("document.querySelector(" + json.dumps(field_selector) + ").value") == source_path
            )
        )
        assert not dialog_errors, dialog_errors
        assert int(msm.get(view.molsys, n_atoms=True)) == before_atoms
        report["native_file_picker_selected"] = True
        # Also prove ordinary typing, without assigning input.value from JS.
        web_click(field_selector)
        QTest.keyClick(web.focusProxy() or web, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClicks(web.focusProxy() or web, source_path)
        assert evaluate("document.querySelector(" + json.dumps(field_selector) + ").value") == source_path
        web_click("[data-molsysviewer-load-operation]")
        key_target = app.focusWidget() or web.focusProxy() or web
        for key in (Qt.Key.Key_Home, Qt.Key.Key_Down, Qt.Key.Key_Return):
            QTest.keyClick(key_target, key)
        wait(lambda: evaluate("document.querySelector('[data-molsysviewer-load-operation]').value") == "replace")
        evaluate(
            "(() => {window.__loadPainted=false; requestAnimationFrame(()=>requestAnimationFrame(()=>window.__loadPainted=true));})()"
        )
        wait(lambda: evaluate("window.__loadPainted"))
        window.grab().save(str(out / "load-native.png"))
        web_click("[data-molsysviewer-load-submit]")
        wait(lambda: view.molsys.get_n_atoms() == 62)
        idle()
        assert "Loaded: 62 atoms" in evaluate("document.querySelector('[data-molsysviewer-load-status]').textContent")
        assert (
            evaluate(
                "document.querySelector('[data-molsysviewer-group-panel-tab=system]').getAttribute('aria-current')"
            )
            == "page"
        )
        report["shared_studio_loading"] = True
        report["visible_studio_loading"] = True
        view.set_panel_mode(None, expanded=False)
        idle()
        print("fullscreen-completed", flush=True)
        report["loads"] = []
        report["binary_replacements"] = 0
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
            assert not view._current_molecular_projection.is_materialized
            report["binary_replacements"] += 1
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
            assert changed > 0.005, f"The native molecular image did not change ({i=}, {changed=}, std={b.std()})"
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
        other = qt.create_standalone_qt0_window(
            second, selection=[0, 1], structure_indices=[8, 0, 3], load_mode="all", apply_project_config=False
        )
        print("second-host-created", flush=True)
        other["window"].show()
        other_bridge = other["webview"]._molsysviewer_qt_bridge
        other_view = other["webview"]._molsysviewer_view
        wait(lambda: other_bridge.ready and not other_bridge.queue and other_bridge.inflight is None)
        assert other["webview"].page().profile() is not web.page().profile()
        assert other_view.molsys.get_n_atoms() == 62
        assert other_view.molsys.structures.n_structures == 3
        assert other_view.regions["selection"].atom_indices == (0, 1)
        assert not other_view.whole.visible
        assert not other_view._current_molecular_projection.is_materialized
        assert (
            evaluate(
                "window.__molsysviewerDocsController.plugin.managers.structure.hierarchy.current.structures[0].cell.obj.data.elementCount",
                target=other["webview"],
            )
            == 62
        )
        report["all_mode_and_structure_indices"] = True
        implicit_html = Path(other["html_path"])
        assert implicit_html.exists()
        print("second-host-ready", flush=True)
        QTest.mouseClick(other["window"]._molsysviewer_chrome.buttons["close"], Qt.MouseButton.LeftButton)
        print("second-host-closed", flush=True)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        print("deletions-processed", flush=True)
        assert other_view.closed and not implicit_html.exists()
        assert other_view._studio_file_picker is None
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
