"""`cutoff_distance` is a physical length, so it is digested where every length is.

The branched copy this replaces accepted exactly the same values -- `puw.is_quantity`
parses a string, so `"3.5 angstroms"` already worked -- and differed only in reaching
`caller.startswith` before testing it, which raised `AttributeError` when no caller was
given.

`None` is **not** unconditionally accepted, unlike `switch_distance`: it means "unset"
only for the form converters, which is where the original allowed it. Keeping that
narrower rule is deliberate -- widening it was measured to change five caller/None pairs
from a refusal to a silent None.
"""

from .._quantity import digest_length_quantity


def digest_cutoff_distance(cutoff_distance, caller=None):
    if cutoff_distance is None:
        if caller is not None and caller.startswith("molsysmt.form.") and caller.count(".to_") == 2:
            return cutoff_distance
    return digest_length_quantity(cutoff_distance, "cutoff_distance", caller=caller)
