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
