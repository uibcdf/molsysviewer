from __future__ import annotations

import pytest

pytest.importorskip("molsysmt")

from molsysviewer.demo import demo


def test_focus_with_fade_emits_set_focus_fade_for_atom_list():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.show(skip_digestion=True)

    view.focus_with_fade([0, 1, 2], fade=0.8, skip_digestion=True)

    last = view._test_message_log[-1]  # noqa: SLF001
    assert last["op"] == "set_focus_fade"
    assert last["options"]["focus_atom_indices"] == [0, 1, 2]
    assert last["options"]["fade"] == 0.8


def test_focus_with_fade_all_clears():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.show(skip_digestion=True)

    view.focus_with_fade("all", skip_digestion=True)

    last = view._test_message_log[-1]  # noqa: SLF001
    assert last["op"] == "set_focus_fade"
    assert last["options"]["focus_atom_indices"] is None
    assert last["options"]["fade"] == 0.0


def test_focus_with_fade_zero_fade_clears():
    view = demo["dialanine"]
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    view.show(skip_digestion=True)

    view.focus_with_fade([0, 1], fade=0.0, skip_digestion=True)

    last = view._test_message_log[-1]  # noqa: SLF001
    assert last["op"] == "set_focus_fade"
    assert last["options"]["focus_atom_indices"] is None
