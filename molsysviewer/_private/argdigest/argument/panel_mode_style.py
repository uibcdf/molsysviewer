from molsysviewer._private.exceptions import ArgumentError


def digest_panel_mode_style(panel_mode_style, caller=None):
    if panel_mode_style is None:
        return None
    if isinstance(panel_mode_style, str):
        val = panel_mode_style.strip().lower()
        if val in {"drawer", "floating", "floating-unified", "integrated", "ambient", "split"}:
            return val
    raise ArgumentError("panel_mode_style", value=panel_mode_style, caller=caller, message="Invalid panel_mode_style preset")
