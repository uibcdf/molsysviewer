"""`names` is the var-positional list of colour names for `mark_cvd_safe`.

It binds as one tuple and is digested once, under the parameter's own name, so this is a
rule about the group as well as its members: at least one name, and every member a string.

Marking nothing as colour-vision-deficiency safe is the shape of a mistake — a caller
splatted an empty list — and it succeeds silently today, which is the worst outcome for a
claim about accessibility.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_names(names, caller=None):
    if not isinstance(names, tuple):
        raise ArgumentError("names", value=names, caller=caller, message=None)
    if not names:
        raise ArgumentError("names", value=names, caller=caller,
                            message="marking nothing as CVD-safe is not a claim")
    for name in names:
        if not isinstance(name, str):
            raise ArgumentError("names", value=name, caller=caller,
                                message="a colour name is a string")
    return names
