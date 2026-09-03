"""`max_bond_length` is a physical length, so it is digested where every length is.

The branched copy this replaces accepted exactly the same values -- `puw.is_quantity`
parses a string, so `"3.5 angstroms"` already worked -- and differed only in reaching
`caller.startswith` before testing it, which raised `AttributeError` when no caller was
given. `None` is kept: it means "unset" here, not "a length of zero".
"""

from .._quantity import digest_length_quantity


def digest_max_bond_length(max_bond_length, caller=None):
    if max_bond_length is None:
        return max_bond_length
    return digest_length_quantity(max_bond_length, "max_bond_length", caller=caller)
