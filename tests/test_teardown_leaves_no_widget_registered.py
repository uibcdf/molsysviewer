"""Teardown must not stop at the first widget that refuses to close.

`uibcdf/molsysviewer#76`. A bare cleanup loop ends at the first exception and leaves every
widget after it registered in `ipywidgets`' `_instances` **for the rest of the session**.
That is not cosmetic: a registered widget finalised later while still holding a live comm
raises inside `Widget.__del__` — `close()` → `comm.close()` → `unregister_comm`, which does
`self.comms.pop(comm.comm_id)` and is documented to raise `KeyError`. Python reports that
as an ignored exception, pytest turns it into `PytestUnraisableExceptionWarning`, and xdist
was twice observed aborting the whole session while shipping such a warning to the
controller, discarding the results of 954 tests.

The chain past the first link is not established (see the record), which is why the guard
is on the link that is: **one failing close must not strand the others.**
"""

from __future__ import annotations

import pytest
from ipywidgets.widgets.widget import _instances

import molsysviewer as msv
from conftest import _close_registered_molsysviewer_widgets  # noqa: E402 - pytest puts tests/ on the path


@pytest.fixture
def two_views():
    return msv.demo["1TCD"], msv.demo["1TCD"]


def test_a_refusing_widget_does_not_strand_the_others(two_views, capsys):
    first, _second = two_views
    original_close = type(first).close

    def refuse(self, *args, **kwargs):
        if self is first:
            raise AttributeError("simulated failure inside close")
        return original_close(self, *args, **kwargs)

    type(first).close = refuse
    try:
        assert len(_instances) >= 2, "the fixture built nothing to clean up"
        _close_registered_molsysviewer_widgets()
    finally:
        type(first).close = original_close

    assert _instances == {}, (
        "widgets were left registered after a failing close; they can be finalised later "
        f"holding a live comm: {sorted(type(w).__name__ for w in _instances.values())}"
    )


def test_the_failure_is_reported_rather_than_swallowed(two_views, capsys):
    """Silent recovery would hide a real teardown fault behind a clean-looking run."""
    first, _second = two_views
    original_close = type(first).close
    type(first).close = lambda self, *a, **k: (_ for _ in ()).throw(AttributeError("boom"))
    try:
        _close_registered_molsysviewer_widgets()
    finally:
        type(first).close = original_close

    assert "failed to close during teardown" in capsys.readouterr().err
