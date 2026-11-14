from molsysviewer._private.exceptions import ArgumentError


def digest_codec(codec, caller=None):
    if isinstance(codec, str) and codec.strip().lower() in {"auto", "h264", "vp9", "av1"}:
        return codec.strip().lower()
    raise ArgumentError("codec", value=codec, caller=caller, message="expected auto, h264, vp9 or av1")
