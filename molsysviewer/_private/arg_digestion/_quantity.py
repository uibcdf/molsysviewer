"""Shared helper to digest physical-length arguments.

The validation/standardization logic lives upstream in PyUnitWizard
(``puw.ensure_quantity``): parse strings, accept any recognized quantity form,
reject bare numbers, require ``[L]`` dimensionality, and standardize to the
suite unit (nm). Here we only re-raise as MolSysViewer's own ``ArgumentError``
(a ``ValueError``) so the viewer keeps a single, consistent error contract and
argument-named messages — the same way molsysmt raises its own error.
"""

from molsysviewer._pyunitwizard import puw
from ..exceptions import ArgumentError


def digest_length_quantity(value, argument, caller=None):
    """Return ``value`` as a standardized ``[L]`` quantity, or raise ``ArgumentError``."""
    try:
        return puw.ensure_quantity(value, dimensionality={"[L]": 1}, caller=caller)
    except Exception as exc:
        raise ArgumentError(
            argument, value=value, caller=caller,
            message=(" A length requires explicit units (e.g. \"3.5 angstroms\" or "
                     "puw.quantity(3.5, 'angstroms')); bare numbers are not accepted, "
                     "to avoid silent nm/angstrom scale errors."),
        ) from exc
