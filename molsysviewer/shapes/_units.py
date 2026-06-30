"""Length-unit helpers for the shape wire format.

Internally MolSysViewer works in nanometers (the suite-native length unit, like
MolSysMT). The Mol* wire format is angstroms, so length values are converted to
angstroms only at this boundary. Bare numeric values are interpreted as
nanometers (e.g. already-digested internal values); PyUnitWizard quantities keep
their own unit and are converted from it.
"""

import numpy as np

from molsysviewer import pyunitwizard as puw


_NM_TO_ANGSTROM = puw.conversion_factor("nm", "angstroms")


def to_wire_angstroms(value):
    """Return ``value`` as angstrom magnitudes for the Mol* wire.

    Bare numeric values (lists, tuples, ndarrays) are treated as nanometers;
    PyUnitWizard quantities are converted from their own unit.
    """
    if value is None:
        return None
    if not puw.is_quantity(value):
        converted = np.asarray(value, dtype=float) * _NM_TO_ANGSTROM
        return float(converted) if converted.ndim == 0 else converted
    return puw.get_value(value, to_unit="angstroms")
