"""Native rendered result disposal; no addon test helpers or software override."""


def main():
    import faulthandler
    import json
    import resource
    import sys
    import time
    from pathlib import Path

    import molsysviewer.standalone_qt as qt
    import numpy as np
    from molsysmt import pyunitwizard as puw
    from PySide6.QtCore import QCoreApplication, QEvent, qVersion
    from shiboken6 import isValid

    import molsysviewer as msv

    faulthandler.enable()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    output = Path(sys.argv[1])
    qt._qt_shell_state_path = lambda: output / "shell-state.json"
    runtime = qt.create_standalone_qt0_window(None, apply_project_config=False)
    app, window, web = runtime["app"], runtime["window"], runtime["webview"]
    view = web._molsysviewer_view
    owners = [(window, web.page(), web.page().profile())]
    shells = [Path(runtime["html_path"])]
    checks = []

    def wait(predicate):
        until = time.monotonic() + 30
        while time.monotonic() < until:
            app.processEvents()
            if predicate():
                return
            time.sleep(0.01)
        raise AssertionError("Native result disposal/geometry deadline.")

    def evaluate(target_web, script):
        answer = []
        target_web.page().runJavaScript("JSON.stringify(" + script + ")", answer.append)
        wait(lambda: bool(answer))
        return json.loads(answer[0]) if answer[0] else None

    def rendered(target, target_web):
        bridge = target_web._molsysviewer_qt_bridge
        wait(lambda: bridge.ready and not bridge.queue and bridge.inflight is None)
        expected = puw.get_value(target.molsys.structures.coordinates, to_unit="angstrom")[0]
        script = "(() => {const s=window.__molsysviewerDocsController?.getStructureData();if(!s)return null;const result=[];for(const u of s.units)for(const a of u.elements){const source=u.model.atomicHierarchy.atomSourceIndex.value(a);result[source]=Array.from(u.conformation.position(a,[0,0,0]));}return result;})()"
        wait(
            lambda: (
                (raw := evaluate(target_web, script)) is not None
                and np.asarray(raw).shape == expected.shape
                and np.allclose(raw, expected, rtol=0, atol=1e-4)
            )
        )
        assert not bridge.failed_deliveries

    def prepare(system, title):
        handle = view.addons.manager.presentations.prepare(lambda child: msv.new_view(system, view=child), title=title)
        child_runtime = view.addons.manager.presentations._records[handle]["runtime"]
        child_web = child_runtime["webview"]
        owners.append((child_runtime["window"], child_web.page(), child_web.page().profile()))
        shells.append(Path(child_runtime["html_path"]))
        return handle, child_runtime

    try:
        window.show()
        wait(lambda: web._molsysviewer_qt_bridge.ready)
        with msv.demo["dialanine"] as seed:
            handle, child = prepare(seed.molsys, "Rendered independent result")
            view.addons.manager.presentations._show(handle, "window")
            rendered(view.addons.manager.presentations.get(handle), child["webview"])
            checks.append("Independent native result renders source-indexed molecular coordinates")
            view.load(seed.molsys, mode="replace")
            rendered(view, web)
            for index in range(3):
                unshown, child_runtime = prepare(seed.molsys, f"Unpresented result {index}")
                assert not child_runtime["window"].isVisible()
                view.addons.manager.presentations.close(unshown)
                view.load(seed.molsys, mode="replace")
                rendered(view, web)
            checks.append("Unpresented result retirement preserves a rendered source and result")
            original_factory = view._independent_view_factory

            def observed_factory(title):
                failed_runtime = original_factory(title)
                failed_web = failed_runtime["webview"]
                owners.append((failed_runtime["window"], failed_web.page(), failed_web.page().profile()))
                shells.append(Path(failed_runtime["html_path"]))
                return failed_runtime

            def rejected(child):
                msv.new_view(seed.molsys, view=child)
                raise ValueError("Controlled native initializer rejection")

            view._independent_view_factory = observed_factory
            try:
                view.addons.manager.presentations.prepare(rejected, title="Rejected result")
            except ValueError as error:
                assert str(error) == "Controlled native initializer rejection"
            else:
                raise AssertionError("The native initializer unexpectedly succeeded.")
            finally:
                view._independent_view_factory = original_factory
            rendered(view, web)
            checks.append("Failed native initialization retires its unregistered runtime without changing the source")
        for record in list(view.addons.manager.presentations.records()):
            view.addons.manager.presentations.close(record["id"])
        window.close()

        def retired():
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
            return (
                all(not isValid(page) and not isValid(profile) for _, page, profile in owners)
                and all(not isValid(result_window) for result_window, _, _ in owners[1:])
                and not window.isVisible()
            )

        wait(retired)
        assert view.closed and not view.addons.manager.presentations.records()
        assert all(not shell.exists() for shell in shells)
        assert not app._molsysviewer_closing_hosts
        checks.append("Pages and profiles retire before all result windows and their temporary shells")
        (output / "result.json").write_text(
            json.dumps(
                {
                    "checks": checks,
                    "qt": qVersion(),
                    "platform": app.platformName(),
                    "native_owners_retired": len(owners),
                    "result_windows_destroyed": len(owners) - 1,
                    "scope": "Actual native Qt/WebEngine/Molstar drawing and complete disposal; not a human or installed qualification.",
                },
                indent=2,
            )
            + "\n"
        )
    finally:
        if not view.closed:
            window.close()


if __name__ == "__main__":
    main()
