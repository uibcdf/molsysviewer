"""A focus overlay survives a save, and comes back as a focus.

Slice 3 of issue #38. `styles.focus()` is not a camera move -- `camera.focus_selection`
is, and slice 2's `view.camera` already carries it. A style focus puts a *visible
representation* on the scene and leaves it there, realised as a region (Contract V) and
remembered in the styles manager's focus registry.

Until this, whether that survived a save depended on whether the user had named it: the
pattern that excluded "transient" regions from the document matched auto-generated tags
alone, so `focus1` was dropped and `tag="mine"` was kept. Neither branch was right --
the first lost the overlay, the second returned it as an ordinary region that
`clear_focus` could no longer remove.
"""

from __future__ import annotations

import pytest
from molsysviewer.demo import demo


def _mute(view):
    view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
    return view


@pytest.mark.parametrize("tag", [None, "mine"])
def test_a_focus_overlay_survives_whether_or_not_the_user_named_it(tag):
    """The asymmetry this slice exists to remove."""
    source = _mute(demo["181L"])
    created = source.styles.focus(
        representation="ball_and_stick", selection="group_index==87", tag=tag,
    )
    document = source.export_state()

    target = _mute(demo["181L"])
    target.import_state(document)

    assert target.styles.focus_tags() == [created]
    assert created in target.regions.tags()


def test_a_restored_focus_is_still_a_focus_not_an_ordinary_region():
    """The registry is what makes the overlay manageable; the region alone is not enough."""
    source = _mute(demo["181L"])
    created = source.styles.focus(representation="ball_and_stick", selection="group_index==87")
    document = source.export_state()

    target = _mute(demo["181L"])
    target.import_state(document)
    target.styles.clear_focus(created)

    assert target.styles.focus_tags() == []
    assert created not in target.regions.tags(), "clear_focus left the region behind"


def test_scaffolding_regions_still_do_not_reach_the_document():
    """Splitting the predicate must not turn the genuinely transient into state.

    Orientation and plane regions are built by an operation and gone with it. They stay
    excluded; only focus moved.
    """
    view = _mute(demo["181L"])
    view.regions.add(selection="group_index==87", tag="plane-region1")
    view.regions.add(selection="group_index==88", tag="orientation-region1")
    view.styles.focus(representation="ball_and_stick", selection="group_index==89")

    saved = [record.get("tag") for record in view.export_state()["regions"]]

    assert "plane-region1" not in saved
    assert "orientation-region1" not in saved
    assert "focus1" in saved


def test_a_focus_overlay_stays_out_of_the_regions_the_user_manages():
    """Persisting it does not promote it to a region the user is asked to manage:
    it is managed through styles.clear_focus, which is the other half of the split."""
    view = _mute(demo["181L"])
    view.styles.focus(representation="ball_and_stick", selection="group_index==87")

    summarised = [record.get("tag") for record in view._region_summary_records()]  # noqa: SLF001

    assert "focus1" not in summarised
