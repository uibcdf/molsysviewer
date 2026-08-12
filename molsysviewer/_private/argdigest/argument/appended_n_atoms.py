"""`appended_n_atoms` is how many atoms a system edit added.

`None` is valid and means "not an addition" — every `load_blocks` policy other than
`append` leaves it unset. When it is given it must be a positive integer count: zero
appended atoms is not an append, and a float is a miscount rather than a rounding.

Whether it is *required* depends on `load_blocks="append"`, which is a rule about another
argument's value and stays in the body until ArgDigest can express one.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_appended_n_atoms(appended_n_atoms, caller=None):
    if appended_n_atoms is None:
        return None
    if isinstance(appended_n_atoms, bool) or not isinstance(appended_n_atoms, int):
        raise ArgumentError("appended_n_atoms", value=appended_n_atoms, caller=caller,
                            message="expected a whole number of atoms")
    if appended_n_atoms <= 0:
        raise ArgumentError(
            "appended_n_atoms",
            value=appended_n_atoms,
            caller=caller,
            message="an append that added no atoms is not an append",
        )
    return appended_n_atoms
