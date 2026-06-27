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
    """Test that viewer_mode presets and explicit parameters are resolved correctly."""
    from molsysviewer.viewer.core import MolSysView

    # 1. Default (classic)
    v = MolSysView()
    assert v.widget.viewer_mode == "classic"
    assert v.widget.controls_mode == "classic"
    assert v.widget.panel_mode_style == "drawer"

    # 2. Zen mode preset
    v_zen = MolSysView(viewer_mode="zen")
    assert v_zen.widget.viewer_mode == "zen"
    assert v_zen.widget.controls_mode == "minimal"
    assert v_zen.widget.panel_mode_style == "floating"

    # 3. Integrated mode preset
    v_int = MolSysView(viewer_mode="integrated")
    assert v_int.widget.viewer_mode == "integrated"
    assert v_int.widget.controls_mode == "minimal"
    assert v_int.widget.panel_mode_style == "integrated"

    # 4. Classic-floating mode preset
    v_cf = MolSysView(viewer_mode="classic-floating")
    assert v_cf.widget.viewer_mode == "classic-floating"
    assert v_cf.widget.controls_mode == "classic"
    assert v_cf.widget.panel_mode_style == "floating"

    # 5. Explicit overrides
    v_override = MolSysView(viewer_mode="zen", controls_mode="classic")
    assert v_override.widget.viewer_mode == "zen"
    assert v_override.widget.controls_mode == "classic"
    assert v_override.widget.panel_mode_style == "floating"

    # 6. Ambient mode preset
    v_amb = MolSysView(viewer_mode="ambient")
    assert v_amb.widget.viewer_mode == "ambient"
    assert v_amb.widget.controls_mode == "minimal"
    assert v_amb.widget.panel_mode_style == "ambient"

    # 7. Focus mode preset (legacy mapping)
    v_foc = MolSysView(viewer_mode="focus")
    assert v_foc.widget.viewer_mode == "focus"
    assert v_foc.widget.controls_mode == "cinema"
    assert v_foc.widget.panel_mode_style == "integrated"

    # 7b. Cinema mode preset
    v_cin = MolSysView(viewer_mode="cinema")
    assert v_cin.widget.viewer_mode == "cinema"
    assert v_cin.widget.controls_mode == "cinema"
    assert v_cin.widget.panel_mode_style == "integrated"

    # 8. Split mode preset
    v_spl = MolSysView(viewer_mode="split")
    assert v_spl.widget.viewer_mode == "split"
    assert v_spl.widget.controls_mode == "minimal"
    assert v_spl.widget.panel_mode_style == "split"
