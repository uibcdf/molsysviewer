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
controls_position_fullscreen = ["bottom", "right"]

from .user_presets import user_presets, load_user_presets

__all__ = [
    "show_controls",
    "autohide_controls",
    "controls_position",
    "controls_position_fullscreen",
    "user_presets",
    "load_user_presets",
]

# PyUnitWizard configuration for quantities with units.

def set_default_quantities_form(form='pint'):

    from molsysviewer import pyunitwizard as puw
    puw.configure.set_default_form(form)

def set_default_quantities_parser(form='pint'):

    from molsysviewer import pyunitwizard as puw
    puw.configure.set_default_parser(form)

def set_default_standard_units(standards=['nm', 'ps', 'K', 'mole', 'amu', 'e',
    'kJ/mol', 'kJ/(mol*nm**2)', 'N', 'degrees']):

    from molsysviewer import pyunitwizard as puw
    puw.configure.set_standard_units(standards)

__all__.extend([
    "set_default_quantities_form",
    "set_default_quantities_parser",
    "set_default_standard_units",
])



