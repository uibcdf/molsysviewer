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

# Controls surface style: "classic" (text buttons), "minimal" (3-icon cluster) or
# "cinema". `None` means "whatever `viewer_mode` implies", which is the default.
#
# `None` and not `"classic"`, deliberately. These were once their own defaults,
# and the resolver read "equal to the default" as "the user has not chosen" — so
# setting `controls_mode = "classic"` here asked for the classic surface and got
# the preset's instead, silently. A sentinel has to be a value nobody can want.
controls_mode: str | None = None

# Panel container architecture: "drawer" (side drawers), "floating", "integrated",
# "floating-unified", "ambient" or "split". `None` follows `viewer_mode`.
panel_mode_style: str | None = None

# High-level viewer mode preset: "classic", "integrated", or "cinema".
viewer_mode: str = "integrated"

from .user_presets import user_presets, load_user_presets
from .project_config import load_project_config
from .._private.argdigest import digest
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

# Scale budget for materialized structures.

@signal(tags=["config", "performance"])
@digest()
def set_structure_scale_budget(budget_bytes: int, skip_digestion: bool = False):
    """Set the coordinate budget above which a large load warns.

    MolSysViewer materializes every selected structure, so this is an honest
    ceiling rather than a limit: raise it when the machine can hold more, lower
    it to be told sooner, or pass 0 to silence the warning. The budget is
    measured in coordinate bytes (atoms x structures x 3 x float32).
    """
    from .._private import scale_budget

    scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES = int(budget_bytes)


@signal(tags=["config", "query"])
@digest()
def get_structure_scale_budget() -> int:
    """Current coordinate budget in bytes; 0 means the warning is silenced."""
    from .._private import scale_budget

    return int(scale_budget.DEFAULT_COORDINATE_BUDGET_BYTES)


__all__.extend([
    "set_structure_scale_budget",
    "get_structure_scale_budget",
    "set_default_quantities_form",
    "set_default_quantities_parser",
    "set_default_standard_units",
])
