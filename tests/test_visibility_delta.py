import numpy as np

from molsysviewer import MolSysView


def _ready_view_with_capture(n_atoms: int = 10):
    view = MolSysView()
    sent: list = []
    view.widget.send = lambda msg: sent.append(msg)  # type: ignore[attr-defined]
    view._ready = True  # noqa: SLF001
    view._atom_mask = np.ones(n_atoms, dtype=bool)
    return view, sent


def test_first_visibility_send_is_full_and_versioned():
    view, sent = _ready_view_with_capture()
    view._update_visibility_in_frontend()  # noqa: SLF001

    assert sent[-1]["op"] == "update_visibility"
    assert sent[-1]["options"]["version"] == 1
    assert sent[-1]["options"]["visible_atom_indices"] == list(range(10))
    recorded = [m for m in view._test_message_log if m.get("op") == "update_visibility"]  # noqa: SLF001
    assert recorded and recorded[-1]["options"]["version"] == 1


def test_small_change_sends_delta_but_projects_full_current_state():
    view, sent = _ready_view_with_capture()
    view._update_visibility_in_frontend()  # noqa: SLF001  (full, v1)

    view._atom_mask[3] = False
    sent.clear()
    view._update_visibility_in_frontend()  # noqa: SLF001

    # Live wire carries only the delta.
    assert sent[-1]["op"] == "update_visibility_delta"
    assert sent[-1]["options"]["base_version"] == 1
    assert sent[-1]["options"]["version"] == 2
    assert sent[-1]["options"]["hidden"] == [3]
    assert sent[-1]["options"]["shown"] == []

    projected = next(
        message
        for message in view._build_canvas_snapshot(include_molecular=False)  # noqa: SLF001
        if message.get("op") == "update_visibility"
    )
    assert projected["options"]["version"] == 2
    assert 3 not in projected["options"]["visible_atom_indices"]


def test_no_change_sends_nothing():
    view, sent = _ready_view_with_capture()
    view._update_visibility_in_frontend()  # noqa: SLF001
    sent.clear()
    view._update_visibility_in_frontend()  # noqa: SLF001
    assert sent == []


def test_resync_request_resends_full_state_at_current_version():
    view, sent = _ready_view_with_capture()
    view._update_visibility_in_frontend()  # noqa: SLF001  (v1)
    view._atom_mask[3] = False
    view._update_visibility_in_frontend()  # noqa: SLF001  (delta -> v2)

    sent.clear()
    view._handle_frontend_event({"event": "request_visibility_resync"})  # noqa: SLF001

    assert sent[-1]["op"] == "update_visibility"
    assert sent[-1]["options"]["version"] == 2
    assert 3 not in sent[-1]["options"]["visible_atom_indices"]


def test_large_change_sends_full_not_delta():
    view, sent = _ready_view_with_capture(n_atoms=10)
    view._update_visibility_in_frontend()  # noqa: SLF001  (v1, all visible)

    # Hide almost everything: the change set is not smaller than the visible list,
    # so a full state is sent instead of a delta.
    view._atom_mask[:] = False
    view._atom_mask[0] = True
    sent.clear()
    view._update_visibility_in_frontend()  # noqa: SLF001

    assert sent[-1]["op"] == "update_visibility"
    assert sent[-1]["options"]["visible_atom_indices"] == [0]
