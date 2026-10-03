from ...exceptions import ArgumentError


def digest_media_type(media_type, caller=None):
    if isinstance(media_type, str) and media_type.strip():
        return media_type
    raise ArgumentError("media_type", value=media_type, caller=caller)
