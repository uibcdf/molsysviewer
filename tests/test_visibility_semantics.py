"""What is drawn is decided by the whole and by regions. `show()` only displays.

Before `uibcdf/molsysviewer#71` phase E, the view carried a second, cross-cutting mechanism:
`atom_mask`, written by `view.hide(selection)`, `view.isolate(selection)` and the
`selection` half of `view.show()`. It subtracted atoms from *every* representation at once.

It was removed because it never reached the scene document — `export_state` did not carry
it, so hiding atoms, saving and reloading brought them back with no warning — while it did
reach the frontend, the popup and the HTML export. A feature whose effect vanishes on save
is half a feature.

What this file guards now is the property that replaced it: **`show()` is the notebook
trigger and nothing else**, so what the whole and the regions decided survives it.
"""

from __future__ import annotations

import pytest

pytest.importorskip("molsysmt")

from molsysviewer.demo import demo


@pytest.fixture
def view():
    v = demo["dialanine"]
    v.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return v


@pytest.fixture
def sent(view, monkeypatch):
    log: list[str] = []
    original = view._send  # noqa: SLF001
    monkeypatch.setattr(
        view, "_send", lambda msg, *a, **k: (log.append(msg.get("op")), original(msg, *a, **k))[1]
    )
    return log


def test_show_does_not_disturb_what_the_whole_and_the_regions_decided(view, sent):
    """The regression phase E could have introduced, and the reason `show` was split.

    `show()` used to reset every visibility decision on its way to displaying the widget,
    because displaying and deciding shared one method.
    """
    region = view.regions.add(
        atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True
    )
    view.whole.hide(skip_digestion=True)
    region.hide(skip_digestion=True)

    sent.clear()
    view.show(skip_digestion=True)

    assert view._global_hidden is True, "show() un-hid the whole"  # noqa: SLF001
    assert region.visible is False, "show() un-hid a region"
    assert sent == [], f"show() is a display trigger and must emit nothing: {sent}"


def test_show_returns_the_widget_once_and_then_on_demand(view):
    """`pyplot.show()` semantics: re-showing in a loop must not stack widgets."""
    assert view.show(skip_digestion=True) is not None
    assert view.show(skip_digestion=True) is None
    assert view.show(force=True, skip_digestion=True) is not None


def test_the_cross_cutting_mask_is_gone(view):
    """Named so the removal is a decision on the record rather than a gap.

    The equivalent is a region: make one for the atoms you want gone and hide it, with the
    whole hidden so nothing else paints them.
    """
    for removed in ("hide", "isolate", "atom_mask", "visible_atom_indices"):
        assert not hasattr(view, removed), f"view.{removed} came back without a decision"


def test_show_no_longer_takes_a_selection(view):
    """Loudly, so a call written for the old meaning cannot silently display everything."""
    with pytest.raises(Exception) as raised:
        view.show(selection=[0, 1], skip_digestion=True)
    assert "does not accept" in str(raised.value) or "unexpected keyword" in str(raised.value)
