from .._quantity import digest_length_quantity


def digest_min_radius(min_radius, caller=None):
    """An optional camera padding radius, as a length.

    Rewritten under uibcdf/molsysviewer#69. It used to accept a quantity of any
    dimensionality (seconds were standardized to picoseconds), read a bare number as
    angstroms while the callers that consume it treat the same argument as nanometres,
    turn the string "4.0" into four **radians** -- PyUnitWizard reads a bare numeric
    string as dimensionless -- and return a non-numeric string unchanged.

    A padding radius is a length. Requiring the unit is what stops the factor of ten
    between the two readings of this same argument from being applied silently.
    """
    if min_radius is None:
        return None
    return digest_length_quantity(min_radius, "min_radius", caller=caller)
