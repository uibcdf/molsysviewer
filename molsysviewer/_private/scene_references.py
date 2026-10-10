"""Validate live scene references at their owning view boundary."""


def require_current_in_view(obj, view):
    """Reject a foreign or retired handle before indices or membership are used."""
    if getattr(obj, "_view", None) is not view:
        raise ValueError("Scene objects must belong to the same view.")
    obj._assert_current()
    return obj
