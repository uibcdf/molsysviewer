from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_color_table(color_table, caller=None):
    if color_table is None:
        return None
    if isinstance(color_table, Mapping):
        return dict(color_table)
    raise ArgumentError("color_table", value=color_table, caller=caller, message=None)
