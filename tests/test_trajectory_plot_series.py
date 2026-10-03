"""Series accepted by the trajectory plot.

NumPy arrays are not `collections.abc.Sequence`, so `show()` rejected them even
though per-frame data in this ecosystem (RMSD, radius of gyration, an energy
term, coordinates out of MolSysMT) arrives exactly like that. Users had to call
`.tolist()` by hand.
"""

from __future__ import annotations

import numpy as np
import pytest
from molsysviewer.demo import demo

from molsysviewer import new_view


@pytest.fixture()
def view(request):
    v = new_view(demo["dialanine"].molsys, structure_indices=[0] * getattr(request, "param", 3))
    v._handle_frontend_event({"event": "ready"})  # noqa: SLF001
    v.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return v


def _sent_options(v):
    sent = []
    v.widget.send = lambda msg: sent.append(msg)  # type: ignore[attr-defined]
    return sent


@pytest.mark.parametrize("view", [4], indirect=True)
def test_numpy_array_is_accepted_as_a_single_series(view):
    sent = _sent_options(view)
    view.trajectory_plot.show(np.array([0.1, 0.2, 0.3, 0.4]))

    options = sent[0]["options"]["cards"][0]
    assert options["n_frames"] == 4
    assert len(options["series"]) == 1


@pytest.mark.parametrize("view", [2], indirect=True)
def test_mapping_of_numpy_arrays_is_accepted(view):
    sent = _sent_options(view)
    view.trajectory_plot.show({"rmsd": np.array([1.0, 2.0]), "rg": np.array([3.0, 4.0])})

    options = sent[0]["options"]["cards"][0]
    assert options["n_frames"] == 2
    assert len(options["series"]) == 2


def test_two_dimensional_array_is_read_as_several_series(view):
    sent = _sent_options(view)
    view.trajectory_plot.show(np.vstack([np.array([1.0, 2.0, 3.0]), np.array([4.0, 5.0, 6.0])]))

    options = sent[0]["options"]["cards"][0]
    assert len(options["series"]) == 2
    assert options["n_frames"] == 3


def test_plain_lists_still_work(view):
    sent = _sent_options(view)
    view.trajectory_plot.show([0.5, 0.6, 0.7])
    assert sent[0]["options"]["cards"][0]["n_frames"] == 3


def test_non_numeric_input_is_still_rejected(view):
    with pytest.raises(ValueError):
        view.trajectory_plot.show("not data")
