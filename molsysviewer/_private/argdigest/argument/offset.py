from ...exceptions import ArgumentError


def digest_offset(offset, offset_mode="camera", caller=None):
    if caller and caller.startswith("molsysviewer.interactions."):
        if isinstance(offset, int) and not isinstance(offset, bool) and offset >= 0:
            return offset
        raise ArgumentError("offset", value=offset, caller=caller)
    if caller and caller.startswith("molsysviewer.annotations."):
        from ...annotation_vectors import annotation_vector
        annotation_vector(offset, "offset", physical=offset_mode == "world", caller=caller)
        return offset
    if isinstance(offset, (list, tuple)) and len(offset) == 3:
        try:
            return [float(x) for x in offset]
        except (TypeError, ValueError):
            pass
    raise ArgumentError("offset", value=offset, caller=caller, message=None)
