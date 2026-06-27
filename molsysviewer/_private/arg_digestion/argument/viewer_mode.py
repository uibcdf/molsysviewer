from molsysviewer._private.exceptions import ArgumentError


def digest_viewer_mode(viewer_mode, caller=None):
    if viewer_mode is None:
        return None
    if isinstance(viewer_mode, str):
        val = viewer_mode.strip().lower()
        if val in {"classic", "classic-floating", "zen", "integrated", "ambient", "cinema", "focus", "split"}:
            return val
    raise ArgumentError("viewer_mode", value=viewer_mode, caller=caller, message="Invalid viewer_mode preset")
