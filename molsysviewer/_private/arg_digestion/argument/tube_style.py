from ...exceptions import ArgumentError


def digest_tube_style(tube_style, caller=None):
    if tube_style is None:
        return None
    if tube_style in {'smooth', 'segments', 'surface'}:
        return tube_style
    raise ArgumentError('tube_style', value=tube_style, caller=caller, message=None)
