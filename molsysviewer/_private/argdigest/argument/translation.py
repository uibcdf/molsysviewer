from ...exceptions import ArgumentError


def digest_translation(translation, caller=None):

    from .coordinates import digest_coordinates

    try:
        return digest_coordinates(translation, caller=caller)
    except:  # noqa: E722
        raise ArgumentError("translation", value=translation, caller=caller, message=None)
