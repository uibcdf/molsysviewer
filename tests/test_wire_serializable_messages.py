"""Every message the public API sends must survive the wire.

The widget transport is JSON. Python builds the messages, and until this file
existed **nothing forced the two to agree** — the same shape as the digester
callers, the Qt action manifest and the popup summaries: where two things must
match and no mechanism enforces it, they drift in silence.

The drift this caught, found by a human at a real browser on 2026-07-31:
`measurements.add_distance(selection_a=[434], selection_b=[975])` produced an
`add_distance_measurement` whose `picks_atom_indices` held `np.int64` values,
because digestion hands the resolver a numpy array and it did `list(arg)`
instead of `[int(i) for i in arg]`. `np.int64` is not JSON-serializable, so the
message could not cross the wire at all. The measurement was created, stored,
queryable and correct in Python — and simply never rendered.

That failure mode is the worst kind this codebase has: no exception, no warning,
a green suite, and a public API that silently does nothing. It also disguised
itself well — measurements made from the Studio subpanel rendered fine, because
their indices arrive from JS as plain numbers, so it looked like a Mol* problem.

numpy scalars are the recurring culprit: anything that has passed through
digestion, `msm.select`, or an ndarray index is a candidate.
"""

import json

import molsysmt as msm
import numpy as np
import pyunitwizard as puw
import pytest

from molsysviewer import MolSysView


def _view() -> MolSysView:
    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view._ready = True  # noqa: SLF001 — otherwise messages queue instead of sending
    return view


def _capture(view) -> list[dict]:
    sent: list[dict] = []
    view.widget.send = lambda msg, *a, **k: sent.append(msg)  # type: ignore[assignment]
    return sent


def _assert_wire_safe(sent, label: str) -> None:
    for message in sent:
        if not isinstance(message, dict):
            continue
        try:
            json.dumps(message)
        except TypeError as exc:
            op = message.get("op") or message.get("action") or "<no op>"
            pytest.fail(
                f"{label}: message {op!r} cannot cross the JSON wire: {exc}. "
                f"It will be created in Python and never reach the frontend. "
                f"Coerce numpy scalars to plain int/float before sending."
            )


def test_measurements_emit_wire_safe_messages():
    """The regression proper: numpy indices in the measurement picks."""
    view = _view()
    sent = _capture(view)

    view.measurements.add_distance(selection_a=[0], selection_b=[10], tag="d1")
    view.measurements.add_angle(selection_a=[0], selection_b=[10], selection_c=[20], tag="a1")
    view.measurements.add_dihedral(
        selection_a=[0], selection_b=[10], selection_c=[20], selection_d=[30], tag="t1"
    )

    assert [m for m in sent if m.get("op") == "add_distance_measurement"], (
        "the distance message must actually be emitted"
    )
    _assert_wire_safe(sent, "measurements")


def test_measurements_from_numpy_indices_stay_wire_safe():
    """The user does not have to pass lists; numpy is an ordinary input here."""
    view = _view()
    sent = _capture(view)

    view.measurements.add_distance(
        selection_a=np.array([0]), selection_b=np.array([10]), tag="np1"
    )
    _assert_wire_safe(sent, "measurements from ndarray")

    picks = [
        m["options"]["picks_atom_indices"]
        for m in sent
        if m.get("op") == "add_distance_measurement"
    ][0]
    for endpoint in picks:
        for index in endpoint:
            assert type(index) is int, (
                f"pick index is {type(index).__name__}, not a plain int; "
                f"numpy scalars do not survive json.dumps"
            )


def test_a_broad_sweep_of_the_public_api_stays_wire_safe():
    """A sweep, so the next numpy scalar is caught wherever it appears.

    Deliberately exercises the domains that build messages from indices, since
    that is where digestion and `msm.select` introduce numpy scalars.
    """
    view = _view()
    sent = _capture(view)

    view.regions.add("atom_index < 6", tag="reg")
    view.regions["reg"].set_representation("cartoon")
    view.regions["reg"].set_color("red")
    view.layers.add("lay")
    view.selections.add("sel", atom_indices=[0, 1, 2])
    view.selections.activate("sel")
    view.active_selection.set([3, 4])
    view.annotations.add_annotation("note", atom_indices=[0], tag="ann", skip_digestion=True)
    view.shapes.add_sphere(
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        radius=puw.quantity(0.2, "nm"),
        tag="shp",
        atom_indices=[0],
    )
    view.measurements.add_distance(selection_a=[0], selection_b=[10], tag="d1")
    view.whole.set_representation("cartoon")
    view.regions.add(selection="atom_index < 20", tag="sweep", representation="line")
    view.show()

    assert sent, "the sweep must actually emit messages"
    _assert_wire_safe(sent, "public API sweep")


def test_the_popup_snapshot_is_wire_safe():
    """The snapshot is sent to a popup, so it faces the same constraint."""
    view = _view()
    view.regions.add("atom_index < 6", tag="reg")
    view.selections.add("sel", atom_indices=[0, 1])
    view.measurements.add_distance(selection_a=[0], selection_b=[10], tag="d1")
    view.annotations.add_annotation("note", atom_indices=[0], tag="ann", skip_digestion=True)

    for mode in ("canvas", "panel"):
        _assert_wire_safe(view.build_popup_scene_snapshot(mode), f"popup snapshot ({mode})")


def test_optional_box_and_time_quantities_cross_the_snapshot_wire():
    source = _view().molsys.copy()
    n_structures = source.structures.n_structures
    source.structures.box = puw.quantity(
        np.broadcast_to(np.eye(3) * 3.0, (n_structures, 3, 3)).copy(),
        "nm",
    )
    source.structures.time = puw.quantity(
        np.arange(n_structures, dtype=np.float64) * 0.5,
        "ps",
    )
    view = MolSysView()
    view.load(source)

    snapshot = view.build_popup_scene_snapshot("canvas")
    _assert_wire_safe(snapshot, "popup snapshot with box/time quantities")
    molecular = next(message for message in snapshot if message.get("op") == "load_molsys_payload")
    first = molecular["payload"]["structures"][0]
    assert isinstance(first["time"], float)
    assert type(first["box"][0][0]) is float
