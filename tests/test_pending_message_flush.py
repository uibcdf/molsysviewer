from __future__ import annotations

from molsysviewer import MolSysView
from molsysviewer import pyunitwizard as puw
from molsysviewer.demo import demo


def test_ready_replays_history_in_order_without_trait_reserialization():
    view = MolSysView()
    sent = []
    view.widget.send = lambda message: sent.append(dict(message))  # type: ignore[method-assign]
    initial_before = list(view.widget.initial_messages)

    view._send({"op": "first"})  # noqa: SLF001
    view._send_replay({"op": "second"})  # noqa: SLF001

    assert view.widget.initial_messages == initial_before
    assert sent == []

    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001

    expected_flush = list(view._message_history)  # noqa: SLF001
    assert sent[:len(expected_flush)] == expected_flush

    sent.clear()
    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001
    assert sent[:len(expected_flush)] == expected_flush


def test_a_remounted_frontend_receives_the_whole_scene():
    view = demo["dialanine"]
    view.shapes.add(
        "sphere",
        center=puw.quantity([0.0, 0.0, 0.0], "nm"),
        tag="site",
        skip_digestion=True,
    )
    sent = []
    view.widget.send = lambda message: sent.append(dict(message))  # type: ignore[method-assign]

    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001
    sent.clear()
    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001

    ops = [message["op"] for message in sent]
    assert "load_molsys_payload" in ops
    assert "add_sphere" in ops
