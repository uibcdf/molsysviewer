from molsysviewer._private.exceptions import ArgumentError


def digest_controls_mode(controls_mode, caller=None):
    if controls_mode is None:
        return None
    if isinstance(controls_mode, str):
        val = controls_mode.strip().lower()
        if val in {"classic", "minimal", "cinema"}:
            return val
    raise ArgumentError("controls_mode", value=controls_mode, caller=caller, message="Invalid controls_mode preset")
