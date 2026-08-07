from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_meta(meta, caller=None):
    """Digest free-form metadata attached to a scene object.

    Accepts ``None`` (no metadata) or any mapping, which is copied into a plain
    ``dict`` so later mutation of the caller's object cannot alter stored state.
    The contents are deliberately not constrained: metadata is user/add-on data.
    """
    if meta is None:
        return None

    if isinstance(meta, Mapping):
        return dict(meta)

    raise ArgumentError("meta", value=meta, caller=caller, message=None)
