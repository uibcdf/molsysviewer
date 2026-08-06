"""Configuring a view mode must be able to ask for the default one.

`_apply_view_modes` resolves three knobs — `viewer_mode`, `controls_mode`,
`panel_mode_style` — from an explicit argument, then the user's configuration,
then the preset implied by `viewer_mode`. Until 2026-08-06 the middle step used
`"classic"` and `"drawer"` as sentinels for "not chosen", and those are also
legitimate answers: a user who configured either got the preset's value instead,
with nothing to say so. A sentinel has to be a value nobody can want.
"""

import pytest

pytest.importorskip("anywidget")

from molsysviewer import MolSysView, config


@pytest.fixture(autouse=True)
def _restore_config():
    before = (config.controls_mode, config.panel_mode_style, config.viewer_mode)
    yield
    config.controls_mode, config.panel_mode_style, config.viewer_mode = before


def _view(**kwargs):
    view = MolSysView(debug_js=True, **kwargs)
    view.widget.send = lambda *_a, **_k: None  # type: ignore[attr-defined]
    return view


@pytest.mark.parametrize(
    "style", ["drawer", "floating", "floating-unified", "integrated", "ambient", "split"]
)
def test_every_panel_style_can_be_configured(style):
    """Including `drawer`, which was unrequestable while it was the sentinel."""
    config.panel_mode_style = style

    assert _view().widget.panel_mode_style == style


@pytest.mark.parametrize("mode", ["classic", "minimal", "cinema"])
def test_every_controls_mode_can_be_configured(mode):
    config.controls_mode = mode

    assert _view().widget.controls_mode == mode


def test_unset_configuration_follows_the_viewer_mode_preset():
    """The default path, which is what the sentinel was protecting."""
    config.controls_mode = None
    config.panel_mode_style = None
    config.viewer_mode = "integrated"

    view = _view()

    assert view.widget.controls_mode == "minimal"
    assert view.widget.panel_mode_style == "integrated"


def test_an_explicit_argument_still_beats_configuration():
    config.panel_mode_style = "ambient"

    assert _view(panel_mode_style="drawer").widget.panel_mode_style == "drawer"


def test_the_classic_viewer_mode_still_implies_its_own_pair():
    config.controls_mode = None
    config.panel_mode_style = None

    view = _view(viewer_mode="classic")

    assert (view.widget.controls_mode, view.widget.panel_mode_style) == ("classic", "drawer")
