"""`visible_atom_indices` is the visibility state of the system *before* an edit.

`None` means "capture it yourself", which is what almost every caller wants; passing a
list is for the case where the caller already computed it against the pre-edit system.

The indices are checked to be non-negative integers because they are read against the old
system and written against the new one. A malformed entry does not raise downstream — it
hides or reveals the wrong atoms, and nothing says so.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_visible_atom_indices(visible_atom_indices, caller=None):
    if visible_atom_indices is None:
        return None
    try:
        indices = list(visible_atom_indices)
    except TypeError:
        raise ArgumentError("visible_atom_indices", value=visible_atom_indices,
                            caller=caller, message="expected a sequence of atom indices") from None
    for index in indices:
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise ArgumentError(
                "visible_atom_indices",
                value=index,
                caller=caller,
                message="atom indices are non-negative integers",
            )
    return indices
