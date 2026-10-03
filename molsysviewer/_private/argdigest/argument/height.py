from molsysviewer._private.exceptions import ArgumentError


def digest_height(height, caller=None):
    if caller in {"molsysviewer.standalone_qt.application.create_standalone_qt0_window",
                  "molsysviewer.standalone_qt.application.launch_standalone_qt0"}:
        if isinstance(height, int) and not isinstance(height, bool) and height > 0:
            return height
        raise ArgumentError("height", value=height, caller=caller, message="expected a positive number of pixels")
    if height is None:
        return None
    if isinstance(height, str):
        return height.strip()
    if isinstance(height, (int, float)) and not isinstance(height, bool):
        return f"{int(height)}px" if isinstance(height, int) else f"{height}px"
    raise ArgumentError(
        "height",
        value=height,
        caller=caller,
        message="Invalid height format. Expected string (e.g. '500px', '80%') or number.",
    )
