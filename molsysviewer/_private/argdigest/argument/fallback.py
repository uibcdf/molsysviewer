"""`fallback` is the colour used for a category the scheme does not cover.

It is a colour, so it is held to the same rule every other colour is, by delegating to
`digest_color` rather than restating it — a second colour parser is a second place for the
accepted forms to drift, and `normalize_color` is what the registry itself calls.

`None` is valid and means "use the scheme's own fallback", which is what the generated
schemes supply.
"""

from .color import digest_color


def digest_fallback(fallback, caller=None):
    if fallback is None:
        return None
    return digest_color(fallback, caller=caller)
