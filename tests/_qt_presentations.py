"""Native window/transport ownership probe; deliberately not a GPU visual gate."""


def main():
    import json
    import sys
    from pathlib import Path

    import molsysviewer.standalone_qt as qt
    from molsysviewer.standalone_qt.view_channel import QtViewChannel
    from PySide6.QtCore import QCoreApplication, QEvent

    import molsysviewer as msv

    output = Path(sys.argv[1])
    qt._qt_shell_state_path = lambda: output / "shell-state.json"
    runtime = qt.create_standalone_qt0_window(None, apply_project_config=False)
    app, window, web = runtime["app"], runtime["window"], runtime["webview"]
    source = web._molsysviewer_view
    window.show()
    with msv.demo["dialanine"] as seed:
        msv.new_view(seed.molsys, view=source)
    service = source.addons.manager.presentations
    handle = service.prepare(
        lambda child: msv.new_view(source.molsys, selection=[0, 1, 2], view=child), title="Independent subset"
    )
    child = service.get(handle)
    child_runtime = service._records[handle]["runtime"]
    child_window = child_runtime["window"]
    assert child_runtime["app"] is app
    assert isinstance(child.widget, QtViewChannel)
    assert child.widget is not source.widget
    assert child.molsys.get_n_atoms() == 3
    assert not child_window.isVisible()
    service._show(handle, "window")
    assert child_window.isVisible()
    window.close()
    assert source.closed and not child.closed
    assert child_window.isVisible()
    child_window.close()
    assert child.closed
    assert not service.records()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    assert not Path(child_runtime["html_path"]).exists()
    assert not Path(runtime["html_path"]).exists()
    (output / "result.json").write_text(
        json.dumps(
            {
                "same_application": True,
                "independent_qt_transport": True,
                "source_close_preserves_result": True,
                "native_close_releases_result": True,
                "temporary_shells_released": True,
                "platform": app.platformName(),
                "scope": "Native Qt windows and transports; no molecular GPU or human visual qualification.",
            }
        )
    )


if __name__ == "__main__":
    main()
