"""Native minimize/hide receiving, preserving actual draw or honest refusal."""


async def exercise_qt_background_capture(
    *, view, window, web, js, idle, wait, wait_js, saved_state, report, out, events, inbound, beats
):
    import time

    from molsysviewer.viewer.frontend_requests import FrontendRequestError

    import molsysviewer as msv

    original = view.molsys
    cases = report["native_background_cases"] = []
    visibility = "({visibility:document.visibilityState,hidden:document.hidden,draws:window.__nativeDrawSequence})"

    async def restore_window():
        window.hide()
        window.showNormal()
        window.raise_()
        window.activateWindow()
        window.windowHandle().requestActivate()
        await wait(
            lambda: window.isVisible() and window.windowHandle().isExposed(), "native-window-exposed", timeout=10
        )
        await wait_js("!document.hidden", "native-document-visible", timeout=10)

    for mode in ("minimized", "hidden"):
        for kind in ("state", "session"):
            await restore_window()
            await idle()
            before = await js(visibility)
            extension = "json" if kind == "state" else "msv"
            path = out / f"background-{mode}-{kind}.{extension}"
            marker = b"caller-owned work must survive unavailable rendering"
            path.write_bytes(marker)
            mark_events, mark_beats = len(events), len(beats)
            try:
                if mode == "minimized":
                    window.showMinimized()
                    await wait(
                        lambda: not window.windowHandle().isExposed(),
                        "native-window-unexposed-after-minimize-request",
                        timeout=5,
                    )
                else:
                    window.hide()
                    assert not window.isVisible()
                # Native host state and document visibility are observed, not
                # overwritten through CDP, CSS or property getters.
                observed = await wait_js("document.hidden && " + visibility, "native-document-hidden", timeout=5)
                started = time.monotonic()
                outcome, reason = "saved", None
                try:
                    operation = view.save_session_async if kind == "session" else view.save_state_async
                    await operation(path)  # Preserve the actual public five-second default.
                except FrontendRequestError as error:
                    outcome, reason = "refused", error.extra["reason"]
                    assert reason in {"request_timeout", "renderer_refused"}, reason
                    assert path.read_bytes() == marker
                seconds = time.monotonic() - started
                after = await js(visibility)
                native = {
                    "visible": window.isVisible(),
                    "minimized": window.isMinimized(),
                    "exposed": window.windowHandle().isExposed(),
                    "active": window.isActiveWindow(),
                }
                reply = [e for e in events[mark_events:] if e.get("event") == "visual_state_snapshot"]
                if outcome == "saved":
                    assert after["draws"] > observed["draws"], "A hidden save requires an actual new native draw."
                    assert len(reply) == 1 and reply[0]["ok"]
                    saved = saved_state(path, kind)
                    assert saved["view"]["camera"] == reply[0]["snapshot"]
                    assert saved["view"]["structure_index"] == reply[0]["structure_index"]
                assert len(beats) > mark_beats
                assert not view._frontend_requests._pending and not view._work_file_saves._pending
                assert view.molsys is original
                cases.append(
                    {
                        "native_mode": mode,
                        "restoration": "explicit hide/show remap",
                        "kind": kind,
                        "outcome": outcome,
                        "reason": reason,
                        "seconds": seconds,
                        "before": before,
                        "unavailable": observed,
                        "after": after,
                        "native_after": native,
                        "heartbeat_progress": len(beats) - mark_beats,
                        "destination_preserved_on_refusal": outcome == "refused",
                        "source_identity_preserved": True,
                    }
                )
            finally:
                await restore_window()
            await idle()
            if cases[-1]["outcome"] == "refused":
                # Resuming the original native render clock must not revive
                # the expired save or replace an existing destination.
                await wait_js(f"window.__nativeDrawSequence>{before['draws']}", "native-resumed-draw")
                assert path.read_bytes() == marker
                cases[-1]["late_resume_preserves_destination"] = True
            fresh = out / f"recovered-{mode}-{kind}.{extension}"
            mark = len(events)
            operation = view.save_session_async if kind == "session" else view.save_state_async
            await operation(fresh)
            replies = [e for e in events[mark:] if e.get("event") == "visual_state_snapshot"]
            assert len(replies) == 1 and replies[0]["ok"]
            saved = saved_state(fresh, kind)
            assert saved["view"]["camera"] == replies[0]["snapshot"]
            restored = msv.load_session(fresh) if kind == "session" else msv.new_view(view.molsys)
            with restored:
                if kind == "state":
                    restored.load_state(fresh)
                state = restored.export_state()
                assert state["view"]["camera"] == saved["view"]["camera"]
                assert state["view"]["structure_index"] == saved["view"]["structure_index"]
            cases[-1]["visible_retry_independently_restored"] = True
            assert view.molsys is original
            assert not view._frontend_requests._pending and not view._work_file_saves._pending
            assert not web.page().isLoading()
            print("BACKGROUND", mode, kind, cases[-1]["outcome"], reason, flush=True)
    report["native_background_scope"] = (
        "Actual native Wayland exposure and document visibility after a minimize request or explicit hide, followed by explicit hide/show remap. Wayland does not expose minimized-state queries or an unminimize request; isMinimized is observed rather than asserted. No simulated browser lifecycle or human claim."
    )
