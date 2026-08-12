"""`on_conflict` decides what happens when an imported tag already exists.

Three values, and the difference between them is not cosmetic: `raise` refuses the whole
import, `skip` keeps what is already there, `rename` keeps both. A typo silently becoming
one of the other two would change which scene the user ends up with, which is why this is
a closed set rather than a truthy check.

The rule used to live in `import_state` as a bare `ValueError` raised after the document
had been parsed and the other arguments accepted. Here it is refused at the seam, with a
catalogued diagnostic that names the caller.
"""

from molsysviewer._private.exceptions import ArgumentError

#: The complete set. `import_state` and `load_state` are the only callers.
ON_CONFLICT_POLICIES = ("raise", "skip", "rename")


def digest_on_conflict(on_conflict, caller=None):
    if on_conflict in ON_CONFLICT_POLICIES:
        return on_conflict
    raise ArgumentError(
        "on_conflict",
        value=on_conflict,
        caller=caller,
        message=f"expected one of {', '.join(ON_CONFLICT_POLICIES)}",
    )
