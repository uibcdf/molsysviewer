"""`switch_distance` is a physical length, so it is digested where every length is.

The branched copy this replaces accepted exactly the same values -- `puw.is_quantity`
parses a string, so `"3.5 angstroms"` already worked -- and differed only in reaching
`caller.startswith` before testing it, which raised `AttributeError` when no caller was
given. `None` is kept: it means "unset" here, not "a length of zero".
"""

from .._quantity import digest_length_quantity


def digest_switch_distance(switch_distance, caller=None):
    if switch_distance is None:
        return switch_distance
    return digest_length_quantity(switch_distance, "switch_distance", caller=caller)
