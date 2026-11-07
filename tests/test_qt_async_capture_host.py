"""Actual Qt Core async-host preflight; no renderer or native-window claim."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("host", ["ordinary", "qtasyncio"])
def test_qt_async_capture_requires_an_explicit_integrated_gui_loop(host, tmp_path):
    pytest.importorskip("PySide6.QtAsyncio")
    script = r"""
import asyncio
from pathlib import Path
import sys
from PySide6 import QtAsyncio
from PySide6.QtCore import QCoreApplication, QObject, QTimer
from molsysviewer import MolSysView, demo
from molsysviewer.standalone_qt.utils import QtMessageBridge
from molsysviewer.standalone_qt.view_channel import QtViewChannel
from molsysviewer.viewer.frontend_requests import FrontendRequestError

app = QCoreApplication([])
parent = QObject()
channel = QtViewChannel(QtMessageBridge(parent, QTimer))
with demo["dialanine"] as source, MolSysView(transport=channel) as view:
    view.load(source.molsys)
    view._ready = True
    view._frontend_capabilities = {"visual_state_capture": [1]}
    async def run():
        if sys.argv[1] == "ordinary":
            before = len(channel._bridge.queue)
            for method, suffix in ((view.save_state_async, ".json"), (view.save_session_async, ".msv")):
                path = Path(sys.argv[2]) / ("unsupported" + suffix)
                try:
                    await method(path)
                except FrontendRequestError as error:
                    assert "QtAsyncio" in str(error), str(error)
                else:
                    raise AssertionError("Unsupported GUI loop accepted a capture")
                assert not path.exists()
                assert not view._frontend_requests._pending
                assert len(channel._bridge.queue) == before
        else:
            channel._require_async_capture_host()
            done = asyncio.get_running_loop().create_future()
            channel._schedule_callback(0.005, lambda: done.set_result("GUI timer dispatched"))
            assert await asyncio.wait_for(done, 1) == "GUI timer dispatched"
            assert not channel._scheduled_callbacks
            channel.close()
            try:
                channel._require_async_capture_host()
            except FrontendRequestError as error:
                assert "view_closed" in str(error)
            else:
                raise AssertionError("Closed native host accepted an async capture")
    if sys.argv[1] == "ordinary":
        asyncio.run(run())
    else:
        loop = QtAsyncio.QAsyncioEventLoop(app)
        async def owned_main():
            try:
                await run()
            finally:
                await loop.shutdown_asyncgens()
                await loop.shutdown_default_executor()
        task = loop.create_task(owned_main())
        task.add_done_callback(lambda _: loop.stop())
        try:
            loop.run_forever()
            task.result()
        finally:
            loop.close()
print("QT_ASYNC_PREFLIGHT_OK", flush=True)
"""
    root = str(Path(__file__).resolve().parents[1])
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [root, os.environ.get("PYTHONPATH")]))}
    result = subprocess.run(
        [sys.executable, "-c", script, host, str(tmp_path)],
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "QT_ASYNC_PREFLIGHT_OK" in result.stdout
