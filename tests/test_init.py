import re

import molsysviewer


def test_print_version_outputs_version(capsys):
    """Import works and __print_version__ emits the expected string."""
    version = molsysviewer.__version__
    assert isinstance(version, str) and version.strip()

    molsysviewer.__print_version__()

    captured = capsys.readouterr().out
    assert re.search(rf"MolSysViewer version {re.escape(version)}", captured)


def test_viewer_modes_and_parameters_resolution():
    """Test that viewer_mode presets and explicit parameters are resolved correctly.

    viewer_mode is intentionally limited to the two high-level presets
    ``standard`` and ``cinema``. The ambient/split layouts are
    reachable through ``panel_mode_style`` and the floating panel lock/dock
    buttons, not as separate viewer modes.
    """
    import pytest
    from molsysviewer._private.exceptions import ArgumentError
    from molsysviewer.viewer.core import MolSysView

    # 1. Default (standard)
    v = MolSysView()
    assert v.widget.viewer_mode == "standard"
    assert v.widget.controls_mode == "compact"
    assert v.widget.panel_mode_style == "integrated"

    # 3. Standard mode preset
    v_int = MolSysView(viewer_mode="standard")
    assert v_int.widget.viewer_mode == "standard"
    assert v_int.widget.controls_mode == "compact"
    assert v_int.widget.panel_mode_style == "integrated"

    # 4. Cinema mode preset
    v_cin = MolSysView(viewer_mode="cinema")
    assert v_cin.widget.viewer_mode == "cinema"
    assert v_cin.widget.controls_mode == "cinema"
    assert v_cin.widget.panel_mode_style == "integrated"

    # 5. Explicit overrides on top of a preset
    v_override = MolSysView(viewer_mode="standard", controls_mode="cinema")
    assert v_override.widget.viewer_mode == "standard"
    assert v_override.widget.controls_mode == "cinema"
    assert v_override.widget.panel_mode_style == "integrated"

    # 6. The integrated "split" layout is still reachable via panel_mode_style,
    #    independently of any viewer_mode preset.
    v_split = MolSysView(panel_mode_style="split")
    assert v_split.widget.panel_mode_style == "split"

    # 7. Removed presets are rejected strictly (no silent coercion).
    for removed in ("classic", "classic-floating", "zen", "ambient", "focus", "split"):
        with pytest.raises(ArgumentError):
            MolSysView(viewer_mode=removed)
