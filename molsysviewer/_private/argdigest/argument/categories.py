"""`categories` are the keys a categorical colour scheme assigns colours to.

A sequence, and it must be non-empty when given: a scheme over zero categories colours
nothing, and `resolve_scheme` would build an empty mapping that then silently paints every
element with the fallback. `None` stays valid and means "the scheme already knows its
categories".

The members are deliberately not constrained. `resolve_scheme` stringifies them
(`str(category)`), so integers, enum members and tuples are all usable keys, and rejecting
anything here would refuse working code for tidiness.
"""

from collections.abc import Sequence

from molsysviewer._private.exceptions import ArgumentError


def digest_categories(categories, caller=None):
    if categories is None:
        return None
    if isinstance(categories, str) or not isinstance(categories, Sequence):
        raise ArgumentError("categories", value=categories, caller=caller,
                            message="expected a sequence of category keys")
    if not categories:
        raise ArgumentError(
            "categories",
            value=categories,
            caller=caller,
            message="a scheme over zero categories colours nothing",
        )
    return list(categories)
