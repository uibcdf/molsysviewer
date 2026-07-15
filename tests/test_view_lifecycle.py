from __future__ import annotations

import gc
import weakref

import pytest
from ipywidgets.widgets.widget import _instances

import conftest
from molsysviewer import MolSysView
from molsysviewer.demo import demo
from molsysviewer.standalone_qt.view_channel import QtViewChannel


def test_close_releases_a_loaded_view_and_its_registered_widgets():
    baseline_ids = set(_instances)
    view = demo["dialanine"]
    view_ref = weakref.ref(view)
    widget = view.widget
    layout = view.widget.layout
    widget_ref = weakref.ref(widget)
    layout_ref = weakref.ref(layout)

    assert len(set(_instances) - baseline_ids) == 2

    view.close()
    view.close()
    del view
    gc.collect()

    assert view_ref() is None
    assert set(_instances) == baseline_ids

    del widget
    del layout
    gc.collect()

    assert widget_ref() is None
    assert layout_ref() is None


def test_context_manager_closes_the_view_when_the_block_exits():
    baseline_ids = set(_instances)

    with MolSysView() as view:
        view_ref = weakref.ref(view)
        assert len(set(_instances) - baseline_ids) == 2

    del view
    gc.collect()

    assert view_ref() is None
    assert set(_instances) == baseline_ids


def test_autouse_teardown_releases_a_view_left_open_by_a_test():
    baseline_ids = set(_instances)
    fixture = conftest._close_molsysviewer_widgets_after_each_test.__wrapped__
    teardown = fixture()
    next(teardown)

    view = MolSysView()
    view_ref = weakref.ref(view)
    del view

    with pytest.raises(StopIteration):
        next(teardown)

    gc.collect()
    assert view_ref() is None
    assert set(_instances) == baseline_ids


class _Bridge:
    def __init__(self):
        self.event_sink = None

    def send(self, message):
        pass


def test_close_detaches_a_qt_channel_from_its_bridge_and_view():
    bridge = _Bridge()
    channel = QtViewChannel(bridge)
    view = MolSysView(transport=channel)
    view_ref = weakref.ref(view)

    assert bridge.event_sink is not None
    assert channel._msg_callbacks  # noqa: SLF001

    view.close()
    del view
    gc.collect()

    assert bridge.event_sink is None
    assert channel._msg_callbacks == []  # noqa: SLF001
    assert view_ref() is None
