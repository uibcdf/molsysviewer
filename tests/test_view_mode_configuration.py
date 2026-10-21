"""Public modern presets, configuration precedence and retired-mode rejection."""

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


@pytest.mark.parametrize("style", ["drawer", "floating", "floating-unified", "integrated", "ambient", "split"])
def test_every_panel_style_can_be_configured(style):
    """Including `drawer`, which was unrequestable while it was the sentinel."""
    config.panel_mode_style = style

    assert _view().widget.panel_mode_style == style


@pytest.mark.parametrize("mode", ["compact", "cinema"])
def test_every_controls_mode_can_be_configured(mode):
    config.controls_mode = mode

    assert _view().widget.controls_mode == mode


def test_unset_configuration_follows_the_viewer_mode_preset():
    """The default path, which is what the sentinel was protecting."""
    config.controls_mode = None
    config.panel_mode_style = None
    config.viewer_mode = "standard"

    view = _view()

    assert view.widget.controls_mode == "compact"
    assert view.widget.panel_mode_style == "integrated"


def test_an_explicit_argument_still_beats_configuration():
    config.panel_mode_style = "ambient"

    assert _view(panel_mode_style="drawer").widget.panel_mode_style == "drawer"


@pytest.mark.parametrize("argument", ["viewer_mode", "controls_mode"])
@pytest.mark.parametrize("entrypoint", ["constructor", "show", "show_without_digest"])
def test_classic_is_rejected_for_new_calls(argument, entrypoint):
    from molsysviewer._private.exceptions import ArgumentError

    if entrypoint == "constructor":
        with pytest.raises(ArgumentError):
            _view(**{argument: "classic"})
        return
    view = _view()
    try:
        before = (view.widget.viewer_mode, view.widget.controls_mode)
        with pytest.raises(ArgumentError):
            view.show(**{argument: "classic"}, skip_digestion=entrypoint == "show_without_digest")
        assert (view.widget.viewer_mode, view.widget.controls_mode) == before
    finally:
        view.close()


def test_stale_configuration_cannot_restore_classic_controls():
    config.viewer_mode = "classic"
    config.controls_mode = "classic"
    view = _view()
    try:
        assert (view.widget.viewer_mode, view.widget.controls_mode) == ("standard", "compact")
    finally:
        view.close()


@pytest.mark.parametrize("argument, retired", [("viewer_mode", "integrated"), ("controls_mode", "minimal")])
@pytest.mark.parametrize("entrypoint", ["constructor", "show", "show_without_digest"])
def test_renamed_modes_are_rejected_for_new_calls(argument, retired, entrypoint):
    from molsysviewer._private.exceptions import ArgumentError

    if entrypoint == "constructor":
        with pytest.raises(ArgumentError):
            _view(**{argument: retired})
        return
    view = _view()
    try:
        before = (view.widget.viewer_mode, view.widget.controls_mode)
        with pytest.raises(ArgumentError):
            view.show(**{argument: retired}, skip_digestion=entrypoint == "show_without_digest")
        assert (view.widget.viewer_mode, view.widget.controls_mode) == before
    finally:
        view.close()


def test_existing_configuration_is_canonicalized_without_changing_panel_layout():
    config.viewer_mode = "integrated"
    config.controls_mode = "minimal"
    config.panel_mode_style = "integrated"
    view = _view()
    try:
        assert (view.widget.viewer_mode, view.widget.controls_mode) == ("standard", "compact")
        assert view.widget.panel_mode_style == "integrated"
    finally:
        view.close()
