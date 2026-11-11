from molsysviewer._private.exceptions import ArgumentError


def digest_fps(fps, caller=None):
    from argdigest.core.caller import caller_matches

    if caller_matches(caller, "molsysviewer.viewer.movie.export_async"):
        from molsysviewer.viewer._movie_sampling import frame_rate

        return frame_rate(fps)
    if fps is None:
        return None
    try:
        v = int(fps)
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    raise ArgumentError("fps", value=fps, caller=caller, message=None)
