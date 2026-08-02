from __future__ import annotations

from molsysviewer import MolSysView
from molsysviewer import pyunitwizard as puw
from molsysviewer.demo import demo


def test_ready_projects_current_state_without_trait_reserialization():
    view = demo["dialanine"]
    assert "_message_history" not in view.__dict__
    sent = []
    view.widget.send = lambda message: sent.append(dict(message))  # type: ignore[method-assign]
    initial_before = list(view.widget.initial_messages)

    view.regions.add("group_index==0", tag="current")
    expected = view._build_embedded_runtime_snapshot()  # noqa: SLF001
    # Test-only traffic capture may grow; reconnect output must not.
    view._test_message_log.extend(  # noqa: SLF001
        {"op": "irrelevant_interaction", "index": index}
        for index in range(10_000)
    )

    assert view.widget.initial_messages == initial_before
    assert sent == []

    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001

    assert sent == expected

    sent.clear()
    view._handle_frontend_event({"event": "ready"})  # noqa: SLF001
    assert sent == expected


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
