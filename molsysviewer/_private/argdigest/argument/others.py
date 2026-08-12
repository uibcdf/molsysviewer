"""`others` is the operand group of a region boolean: ``A - (B | C | ...)``.

**It arrives as one tuple, not one operand.** ArgDigest binds a `*args` parameter once,
under the parameter's own name, and digests it a single time — so this receives
`(region_b, region_c)`, never `region_b` and then `region_c`. That is deliberate upstream
(`SPEC.md` §4.4): it is what lets a rule be stated about the *group* rather than about
each member, which is exactly what is needed here.

The group rule is "at least one operand", which is a statement about the tuple and could
not be expressed per-operand at all. Stating it here upgrades a bare `TypeError` into a
catalogued diagnostic that names the caller.

The three `if not others: raise TypeError(...)` in `regions.py` **stay**. They are
unreachable for a digested call and are not redundant: `skip_digestion=True` bypasses this
digester entirely, and an empty operand group on that path would otherwise return a wrong
region rather than an error. Deleting them would trade three lines for a silent wrong
answer on the one path that has no other guard.

What an individual operand may *be* — a `Region`, a tag, an index sequence — stays with
`Region._coerce_region_operand`, which is the only place that knows the accepted forms and
raises with the caller's own wording. Restating it here would put one decision in two
places, and the copy would be the one that ages.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_others(others, caller=None):
    if not isinstance(others, tuple):
        raise ArgumentError("others", value=others, caller=caller, message=None)
    if not others:
        raise ArgumentError(
            "others",
            value=others,
            caller=caller,
            message="a region boolean needs at least one operand",
        )
    return others
