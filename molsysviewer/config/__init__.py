"""
User-facing configuration for MolSysViewer.

Adjust the values here to control default viewer behavior without editing code.
"""

# Show overlay controls (Reset, Full, Bg, Spin, Swing, trajectory bar) by default.
show_controls: bool = True

# If True, controls auto-hide when the mouse leaves the canvas and show on hover.
autohide_controls: bool = True

# Overlay position: list containing any combination of "top"/"bottom" and "left"/"right".
controls_position = ["top", "right"]

# Overlay position when fullscreen is active.
controls_position_fullscreen = ["top", "right"]

# Controls surface style: "classic" (text buttons) or "minimal" (3-icon cluster).
controls_mode: str = "classic"

# Panel container architecture: "drawer" (side drawers) or "floating" (centered overlay).
panel_mode_style: str = "drawer"

# High-level viewer mode preset: "classic", "classic-floating", "zen", or "integrated".
viewer_mode: str = "integrated"

from .user_presets import user_presets, load_user_presets
from .project_config import load_project_config
from .._private.arg_digestion import digest
from smonitor import signal

__all__ = [
    "show_controls",
    "autohide_controls",
    "controls_position",
    "controls_position_fullscreen",
    "controls_mode",
    "panel_mode_style",
    "viewer_mode",
    "user_presets",
    "load_user_presets",
    "load_project_config",
]

# PyUnitWizard configuration for quantities with units.

@signal(tags=["config", "pyunitwizard"])
@digest()
def set_default_quantities_form(form='pint', skip_digestion: bool = False):

    from molsysviewer._pyunitwizard import puw
    puw.configure.set_default_form(form)

@signal(tags=["config", "pyunitwizard"])
@digest()
def set_default_quantities_parser(form='pint', skip_digestion: bool = False):

    from molsysviewer._pyunitwizard import puw
    puw.configure.set_default_parser(form)

@signal(tags=["config", "pyunitwizard"])
@digest()
def set_default_standard_units(standards: list[str] | None = None, skip_digestion: bool = False):
    if standards is None:
        standards = ['nm', 'ps', 'K', 'mole', 'amu', 'e',
            'kJ/mol', 'kJ/(mol*nm)', 'kJ/(mol*nm**2)', 'radians']

    from molsysviewer._pyunitwizard import puw
    puw.configure.set_standard_units(standards)

__all__.extend([
    "set_default_quantities_form",
    "set_default_quantities_parser",
    "set_default_standard_units",
])
