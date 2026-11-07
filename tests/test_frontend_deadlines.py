"""Connector deadlines use actual host loops and never a timer worker thread."""

import asyncio
import json
import os
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from threading import Event, Thread, get_ident
from types import SimpleNamespace

import IPython
import pytest
from molsysviewer.widget import MolSysViewerWidget

from molsysviewer import widget as widget_module


@pytest.fixture
def make_widget():
    # Raw widget tests own their Layout as well as the parent. ipywidgets.close()
    # deliberately leaves child widgets alone because they may be shared; once
    # the parent is unregistered the View-oriented teardown cannot discover it.
    with ExitStack() as cleanup:

        def create():
            widget = MolSysViewerWidget()
            cleanup.callback(widget.layout.close)
            cleanup.callback(widget.close)
            return widget

        yield create


def test_widget_finalization_does_not_import_digesters_during_interpreter_shutdown():
    result = subprocess.run(
        [sys.executable, "-c", "from molsysviewer.widget import MolSysViewerWidget; widget = MolSysViewerWidget()"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "sys.meta_path is None" not in result.stderr
    assert "Exception ignored" not in result.stderr


def test_widget_asyncio_deadline_runs_on_owner_and_cancellation_releases_it(make_widget):
    async def receive():
        widget = make_widget()
        callbacks = []
        completed = asyncio.Event()
        owner = get_ident()

        def answer():
            callbacks.append(get_ident())
            completed.set()

        try:
            fired = widget._schedule_callback(0.001, answer)
            assert len(widget._scheduled_callbacks) == 1
            await asyncio.wait_for(completed.wait(), timeout=1)
            assert callbacks == [owner]
            assert not widget._scheduled_callbacks
            fired.cancel()
            fired.cancel()
            cancelled = widget._schedule_callback(0.01, lambda: callbacks.append("cancelled"))
            cancelled.cancel()
            cancelled.cancel()
            widget._schedule_callback(0.01, lambda: callbacks.append("closed"))
            widget.close()
            assert not widget._scheduled_callbacks
            await asyncio.sleep(0.03)
            assert callbacks == [owner]
            with pytest.raises(RuntimeError, match="closed"):
                widget._schedule_callback(0, answer)
        finally:
            widget.close()

    asyncio.run(receive())


def test_widget_kernel_fallback_uses_the_real_tornado_loop(monkeypatch, make_widget):
    from tornado.ioloop import IOLoop

    async def receive():
        loop = IOLoop.current()
        monkeypatch.setattr(IPython, "get_ipython", lambda: SimpleNamespace(kernel=SimpleNamespace(io_loop=loop)))

        def no_asyncio_context():
            raise RuntimeError("Synchronous kernel comm entry")

        monkeypatch.setattr(widget_module, "get_running_loop", no_asyncio_context)
        widget = make_widget()
        completed = asyncio.Event()
        callbacks = []
        owner = get_ident()

        def answer():
            callbacks.append(get_ident())
            completed.set()

        try:
            widget._schedule_callback(0.001, answer)
            await asyncio.wait_for(completed.wait(), timeout=1)
            cancelled = widget._schedule_callback(0.01, lambda: callbacks.append("cancelled"))
            cancelled.cancel()
            widget._schedule_callback(0.01, lambda: callbacks.append("closed"))
            widget.close()
            await asyncio.sleep(0.03)
            assert callbacks == [owner]
            assert not widget._scheduled_callbacks
        finally:
            widget.close()

    asyncio.run(receive())


def test_widget_without_host_loop_refuses_instead_of_leaving_a_deadline(monkeypatch, make_widget):
    monkeypatch.setattr(IPython, "get_ipython", lambda: None)
    widget = make_widget()
    try:
        with pytest.raises(RuntimeError, match="no running notebook or asyncio event loop"):
            widget._schedule_callback(0.01, lambda: None)
        assert not widget._scheduled_callbacks
    finally:
        widget.close()


def test_unbound_widget_rejects_an_unrelated_worker_loop(monkeypatch, make_widget):
    monkeypatch.setattr(IPython, "get_ipython", lambda: None)
    widget = make_widget()
    failures = []

    def receive():
        async def unrelated_loop():
            try:
                widget._schedule_callback(0.001, lambda: None)
            except RuntimeError as error:
                failures.append(str(error))

        asyncio.run(unrelated_loop())

    try:
        worker = Thread(target=receive)
        worker.start()
        worker.join(timeout=1)
        assert not worker.is_alive()
        assert failures == ["The widget has no running notebook or asyncio event loop."]
        assert not widget._scheduled_callbacks
    finally:
        widget.close()


@pytest.mark.parametrize("host", ["asyncio", "tornado"])
def test_bound_host_accepts_comm_worker_but_runs_callback_on_its_own_loop(monkeypatch, host, make_widget):
    async def receive():
        if host == "tornado":
            from tornado.ioloop import IOLoop

            io_loop = IOLoop.current()
            monkeypatch.setattr(
                IPython, "get_ipython", lambda: SimpleNamespace(kernel=SimpleNamespace(io_loop=io_loop))
            )
        else:
            monkeypatch.setattr(IPython, "get_ipython", lambda: None)
        widget = make_widget()
        owner = get_ident()
        completed = asyncio.Event()
        called, workers, failures = [], [], []

        def answer():
            called.append(get_ident())
            completed.set()

        def comm_worker():
            async def private_worker_loop():
                workers.append(get_ident())
                try:
                    widget._schedule_callback(0.001, answer)
                except BaseException as error:
                    failures.append(error)

            asyncio.run(private_worker_loop())

        try:
            worker = Thread(target=comm_worker)
            worker.start()
            worker.join(timeout=1)
            assert not worker.is_alive()
            assert not failures
            assert workers[0] != owner
            await asyncio.wait_for(completed.wait(), timeout=1)
            assert called == [owner]
            assert not widget._scheduled_callbacks
        finally:
            widget.close()

    asyncio.run(receive())


@pytest.mark.parametrize("host", ["asyncio", "tornado"])
@pytest.mark.parametrize("termination", ["cancel", "close"])
def test_comm_worker_cancellation_before_loop_registration_prevents_late_callback(
    monkeypatch, host, termination, make_widget
):
    async def receive():
        if host == "tornado":
            from tornado.ioloop import IOLoop

            io_loop = IOLoop.current()
            monkeypatch.setattr(
                IPython, "get_ipython", lambda: SimpleNamespace(kernel=SimpleNamespace(io_loop=io_loop))
            )
        else:
            monkeypatch.setattr(IPython, "get_ipython", lambda: None)
        widget = make_widget()
        called, failures = [], []

        def comm_worker():
            try:
                handle = widget._schedule_callback(0, lambda: called.append(get_ident()))
                if termination == "cancel":
                    handle.cancel()
                    handle.cancel()
                else:
                    widget.close()
            except BaseException as error:
                failures.append(error)

        try:
            # Join deliberately holds the actual host loop until the worker has
            # cancelled. Its queued registration cannot run before cancellation.
            worker = Thread(target=comm_worker)
            worker.start()
            worker.join(timeout=1)
            assert not worker.is_alive()
            assert not failures
            assert not widget._scheduled_callbacks
            await asyncio.sleep(0.03)
            assert called == []
        finally:
            widget.close()

    asyncio.run(receive())


@pytest.mark.parametrize("host", ["asyncio", "tornado"])
def test_comm_worker_cancel_during_actual_timer_registration_remains_terminal(monkeypatch, host, make_widget):
    async def receive():
        if host == "tornado":
            from tornado.ioloop import IOLoop

            io_loop = IOLoop.current()
            monkeypatch.setattr(
                IPython, "get_ipython", lambda: SimpleNamespace(kernel=SimpleNamespace(io_loop=io_loop))
            )
        else:
            monkeypatch.setattr(IPython, "get_ipython", lambda: None)
        widget = make_widget()
        timer_created, cancelled = Event(), Event()
        called, failures = [], []
        original_registration = widget_module._ScheduledCallback._set_cancel

        def observe_registration(handle, cancel):
            # The host has created a real TimerHandle, but its cancellation hook
            # is not yet installed. Pause only this private registration seam.
            timer_created.set()
            assert cancelled.wait(timeout=1)
            original_registration(handle, cancel)

        monkeypatch.setattr(widget_module._ScheduledCallback, "_set_cancel", observe_registration)

        def comm_worker():
            try:
                handle = widget._schedule_callback(0.005, lambda: called.append(get_ident()))
                assert timer_created.wait(timeout=1)
                handle.cancel()
            except BaseException as error:
                failures.append(error)
            finally:
                cancelled.set()

        worker = Thread(target=comm_worker)
        try:
            worker.start()
            await asyncio.sleep(0.03)
            worker.join(timeout=1)
            assert not worker.is_alive()
            assert timer_created.is_set() and not failures
            assert called == []
            assert not widget._scheduled_callbacks
        finally:
            cancelled.set()
            worker.join(timeout=1)
            widget.close()

    asyncio.run(receive())


def test_stopped_bound_host_is_not_replaced_by_the_callers_new_loop(monkeypatch, make_widget):
    monkeypatch.setattr(IPython, "get_ipython", lambda: None)

    async def create():
        return make_widget()

    widget = asyncio.run(create())

    async def receive():
        with pytest.raises(RuntimeError, match="no running notebook or asyncio event loop"):
            widget._schedule_callback(0, lambda: None)
        assert not widget._scheduled_callbacks

    try:
        asyncio.run(receive())
    finally:
        widget.close()


@pytest.mark.parametrize("delay", [-1, True, "1", float("nan"), float("inf")])
def test_widget_refuses_invalid_deadlines_without_retaining_callbacks(delay, make_widget):
    widget = make_widget()
    try:
        with pytest.raises(ValueError, match="finite and nonnegative"):
            widget._schedule_callback(delay, lambda: None)
        assert not widget._scheduled_callbacks
    finally:
        widget.close()


def test_qt_deadlines_use_real_gui_thread_timers_and_release_on_cancel_close_or_owner_loss():
    """Qt Core only: this is scheduler evidence, not visible-window/GPU evidence."""
    pytest.importorskip("PySide6.QtCore")
    script = r"""
import json
from threading import Thread, get_ident
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QTimer
from molsysviewer.standalone_qt.utils import QtMessageBridge
from molsysviewer.standalone_qt.view_channel import QtViewChannel

app = QCoreApplication([])
parent = QObject()
channel = QtViewChannel(QtMessageBridge(parent, QTimer))
owner = get_ident()
callbacks = []
failures = []
channel._schedule_callback(0.005, lambda: callbacks.append(get_ident()))
cancelled = channel._schedule_callback(0.01, lambda: callbacks.append("cancelled"))
cancelled.cancel()
cancelled.cancel()

def foreign_thread():
    try:
        channel._schedule_callback(0, lambda: callbacks.append("foreign"))
    except RuntimeError as error:
        failures.append(str(error))

worker = Thread(target=foreign_thread)
worker.start()
worker.join(timeout=1)
assert not worker.is_alive()
assert failures == ["Qt callbacks must be scheduled on their owning GUI thread."]

closed = QtViewChannel(QtMessageBridge(parent, QTimer))
closed._schedule_callback(0.01, lambda: callbacks.append("closed"))
closed.close()
closed.close()
assert not closed._scheduled_callbacks
try:
    closed._schedule_callback(0, lambda: None)
except RuntimeError:
    pass
else:
    raise AssertionError("Closed Qt channel accepted a timer")

retired_parent = QObject()
retired = QtViewChannel(QtMessageBridge(retired_parent, QTimer))
retired._schedule_callback(0.01, lambda: callbacks.append("retired"))
retired_parent.deleteLater()
QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
assert not retired._scheduled_callbacks
retired.close()

def finished():
    assert callbacks == [owner], callbacks
    assert not channel._scheduled_callbacks
    channel.close()
    print("DEADLINES_JSON " + json.dumps({"owner": owner, "callbacks": callbacks,
        "cancelled": True, "closed": True, "owner_retired": True}), flush=True)
    app.quit()

QTimer.singleShot(50, finished)
QTimer.singleShot(2000, app.quit)
app.exec()
"""
    root = str(Path(__file__).resolve().parents[1])
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [root, os.environ.get("PYTHONPATH")]))}
    result = subprocess.run([sys.executable, "-c", script], env=environment, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    records = [
        line.removeprefix("DEADLINES_JSON ")
        for line in result.stdout.splitlines()
        if line.startswith("DEADLINES_JSON ")
    ]
    assert len(records) == 1, result.stdout + result.stderr
    report = json.loads(records[0])
    assert report["callbacks"] == [report["owner"]]
    assert report["cancelled"] and report["closed"] and report["owner_retired"]
