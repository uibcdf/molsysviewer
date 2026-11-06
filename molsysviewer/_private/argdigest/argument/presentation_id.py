from ...exceptions import ArgumentError


def digest_presentation_id(presentation_id, caller=None):
    if not isinstance(presentation_id, str) or not presentation_id or len(presentation_id) > 200:
        raise ArgumentError(
            "presentation_id", value=presentation_id, caller=caller, message="Expected a result View handle."
        )
    return presentation_id
