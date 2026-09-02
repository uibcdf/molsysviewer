from .._quantity import digest_length_quantity


def digest_z0(z0, caller=None):
    """A scalar length, standardized through the shared PyUnitWizard boundary.

    Was a hand-rolled `is_quantity -> check -> standardize -> raise`, identical in every
    line to two other digesters and to the helper. Consolidated under
    uibcdf/molsysviewer#33, which the units policy already required: what a caller gets
    for a bare number is now a message naming the unit to add and the mistake it avoids,
    instead of one that only says the argument was wrong.
    """
    return digest_length_quantity(z0, "z0", caller=caller)
