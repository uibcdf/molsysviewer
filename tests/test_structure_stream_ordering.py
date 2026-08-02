"""A scene message must never overtake the structure it describes.

On the JSON path this was free: the frontend's message queue awaits
`load_molsys_payload` to completion before taking the next message, so a scene
op could not arrive before there was something to draw it on. The array-native
data plane removed that guarantee without replacing it. `structure_data_begin`
goes out, Python returns immediately, and the structure is only built in the
browser several ack round-trips later, when the last chunk lands. Everything
sent in between reaches a frontend with no structure — and `addMeasurement`,
like the annotation and region handlers, returns silently instead of failing.

Found by a human at a real browser on 2026-07-31: a measurement created from
Python before the widget was displayed was correct, stored and queryable, and
simply never drawn. The same measurement made from the Studio subpanel appeared
immediately, because it is created long after the structure exists — which is
what made it look like a Mol* problem for two rounds of smoke testing.

The same defect had a second instance: `_answer_popup_scene_snapshot` streams the
generation to the popup endpoint and then sent the whole projected scene at once,
so a popped-out canvas showed the molecule and nothing else.

This is the codebase's recurring shape once more — two things that must agree
(send order and apply order) with nothing mechanically forcing them to.
"""

from __future__ import annotations

import time

import molsysmt as msm

from molsysviewer import MolSysView

BINARY_CAPABILITIES = {
    "binary_structure_data": [1],
    "max_buffer_bytes": 16 * 1024 * 1024,
}


def _view_with_a_pending_measurement() -> MolSysView:
    """The notebook order that broke: build the scene, then display the view."""
    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view.measurements.add_distance(selection_a=[0], selection_b=[10], tag="d1")
    view.annotations.add_annotation("note", atom_indices=[0], tag="ann", skip_digestion=True)
    return view


def _ops(sent) -> list[str]:
    return [m.get("op") for m in sent if isinstance(m, dict)]


def _capture(view) -> list[dict]:
    sent: list[dict] = []
    view.widget.send = lambda msg, buffers=None: sent.append(msg)  # type: ignore[assignment]
    return sent


def test_a_replayed_scene_waits_for_the_streamed_structure(complete_structure_stream):
    view = _view_with_a_pending_measurement()
    sent = _capture(view)

    view._handle_frontend_event({"event": "ready", "capabilities": BINARY_CAPABILITIES})  # noqa: SLF001

    assert "structure_data_begin" in _ops(sent), "the generation must be streamed"
    assert "add_distance_measurement" not in _ops(sent), (
        "the measurement reached the frontend before its structure did; the "
        "handler drops it silently and the user sees nothing"
    )
    assert "add_label" not in _ops(sent)

    complete_structure_stream(view)

    ops = _ops(sent)
    last_chunk = max(i for i, op in enumerate(ops) if op == "structure_data_chunk")
    assert "add_distance_measurement" in ops, "the measurement must arrive eventually"
    assert ops.index("add_distance_measurement") > last_chunk
    assert "add_label" in ops
    assert not view._deferred_widget_messages, "nothing may be stranded"  # noqa: SLF001


def test_the_deferred_scene_keeps_the_order_python_produced_it_in(complete_structure_stream):
    """Held messages are a queue, not a set: replay order is part of the scene.

    Regions layer by arrival and colours resolve after their components, so a
    flush that reordered would produce a different picture from the same state.
    """
    view = MolSysView()
    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view.regions.add("atom_index < 6", tag="low")
    view.regions.add("atom_index < 12", tag="high")
    view.measurements.add_distance(selection_a=[0], selection_b=[10], tag="d1")
    expected = view._build_embedded_runtime_snapshot(  # noqa: SLF001
        include_molecular=False
    )

    sent = _capture(view)
    view._handle_frontend_event({"event": "ready", "capabilities": BINARY_CAPABILITIES})  # noqa: SLF001
    complete_structure_stream(view)

    delivered = [
        message
        for message in sent
        if not str(message.get("op", "")).startswith("structure_data_")
    ]
    assert delivered == expected


def test_a_live_scene_op_waits_for_a_load_that_is_still_streaming(complete_structure_stream):
    """The race is not only at bootstrap: any load starts an async generation."""
    view = MolSysView()
    view._ready = True  # noqa: SLF001
    view._frontend_capabilities = dict(BINARY_CAPABILITIES)  # noqa: SLF001
    sent = _capture(view)

    view.load(msm.systems["pentalanine"]["traj_pentalanine.h5msm"])
    view.measurements.add_distance(selection_a=[0], selection_b=[10], tag="d1")

    assert "add_distance_measurement" not in _ops(sent)
    complete_structure_stream(view)
    assert "add_distance_measurement" in _ops(sent)


def test_a_stream_that_falls_back_to_json_still_delivers_the_scene_behind_it():
    """The fallback must not strand the backlog, nor let it overtake the load.

    A frontend that never acknowledges is released by the deadline; the JSON
    `load_molsys_payload` is then sent, and the scene has to follow it — not
    precede it, and not vanish with the stream.
    """
    view = _view_with_a_pending_measurement()
    sent = _capture(view)

    view._handle_frontend_event({"event": "ready", "capabilities": BINARY_CAPABILITIES})  # noqa: SLF001
    assert "add_distance_measurement" not in _ops(sent), (
        "the stream must really be in flight, or this tests the wrong thing"
    )

    # Push the clock past the ack deadline rather than shortening the timeout:
    # the deadline was already computed when the stream began.
    view._monotonic = lambda: time.monotonic() + 3600.0  # noqa: SLF001
    # Any main-thread entry point evaluates the deadline; the frontend touching
    # the view for an unrelated reason is the realistic one.
    view._handle_inbound_message({"event": "widget_resize", "height": 400})  # noqa: SLF001

    ops = _ops(sent)
    assert "load_molsys_payload" in ops, "the stream must have fallen back to JSON"
    assert "add_distance_measurement" in ops, "the backlog must not be stranded"
    assert ops.index("add_distance_measurement") > ops.index("load_molsys_payload")
    assert not view._deferred_widget_messages  # noqa: SLF001


def test_the_handshake_and_blocking_requests_are_never_held(complete_structure_stream):
    """Deferring transport traffic would deadlock the thing it waits on.

    The chunks carry the generation whose completion releases the queue, and the
    bootstrap source reply is what the frontend is blocking on to exist at all.
    Both bypass the gate by using a different method, so no op-name allowlist has
    to be kept in step with them.
    """
    view = _view_with_a_pending_measurement()
    sent = _capture(view)
    view._handle_frontend_event({"event": "ready", "capabilities": BINARY_CAPABILITIES})  # noqa: SLF001

    view._handle_frontend_event({"event": "request_widget_runtime_source"})  # noqa: SLF001
    assert "widget_runtime_source" in _ops(sent), (
        "the bootstrap reply must not wait for a structure that cannot arrive "
        "until the frontend runtime it carries is running"
    )

    complete_structure_stream(view)
    assert "add_distance_measurement" in _ops(sent)


def test_a_json_only_frontend_is_unaffected():
    """Without the data plane there is no stream, so nothing is ever held."""
    view = _view_with_a_pending_measurement()
    sent = _capture(view)

    view._handle_frontend_event({"event": "ready", "capabilities": {}})  # noqa: SLF001

    ops = _ops(sent)
    assert "load_molsys_payload" in ops
    assert "add_distance_measurement" in ops
    assert ops.index("add_distance_measurement") > ops.index("load_molsys_payload")
    assert not view._deferred_widget_messages  # noqa: SLF001
