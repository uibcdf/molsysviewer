"""Digest the outer correspondence container; Movie owns its target schema."""

from ...exceptions import ArgumentError


def digest_target_map(target_map, caller=None):
    if target_map is None or isinstance(target_map, (list, tuple)):
        return target_map
    raise ArgumentError(
        "target_map", value=target_map, caller=caller, message="expected source/target records in a list"
    )
