"""The shared boundary for physical-magnitude arguments.

The validation and standardization live upstream in PyUnitWizard
(``puw.ensure_quantity``): parse strings, accept any recognized quantity form, reject bare
numbers, require a dimensionality, and standardize to the suite unit. What is done here is
re-raise as MolSysViewer's own ``ArgumentError`` (a ``ValueError``) so the viewer keeps one
error contract with argument-named messages, the same way MolSysMT raises its own.

That translation is the whole point, and it is not decoration. Left to itself
``ensure_quantity`` lets pint out: ``"banana"`` escapes as ``UndefinedUnitError`` and a
boolean as ``NotImplementedMethodError``, neither naming the argument, the caller, or this
package. `uibcdf/molsysviewer#86` is what that costs when an argument skips this boundary.

``digest_length_quantity`` is the ``[L]`` case of ``digest_quantity``, not a separate
mechanism -- 24 digesters call it. A new magnitude states its dimensionality and its own
message here rather than hand-rolling
``parse -> is_quantity -> check -> standardize -> raise`` again, which is the duplication
`uibcdf/molsysviewer#33` set out to stop.
"""

from molsysviewer._pyunitwizard import puw

from ..exceptions import ArgumentError

#: `[L][M][T]^-2[mol]^-1` — a force per mole, as MolSysMT and OpenMM report it.
FORCE_DIMENSIONALITY = {"[L]": 1, "[M]": 1, "[T]": -2, "[mol]": -1}

LENGTH_MESSAGE = (" A length requires explicit units (e.g. \"3.5 angstroms\" or "
                  "puw.quantity(3.5, 'angstroms')); bare numbers are not accepted, "
                  "to avoid silent nm/angstrom scale errors.")


def digest_quantity(value, argument, dimensionality, caller=None, message=None):
    """Return ``value`` as a standardized quantity of *dimensionality*, or raise.

    The raise is always ``ArgumentError``: whatever PyUnitWizard or pint throws underneath
    is the cause, never what reaches the caller.
    """
    try:
        return puw.ensure_quantity(value, dimensionality=dimensionality, caller=caller)
    except Exception as exc:
        raise ArgumentError(
            argument, value=value, caller=caller, message=message,
        ) from exc


def digest_length_quantity(value, argument, caller=None):
    """Return ``value`` as a standardized ``[L]`` quantity, or raise ``ArgumentError``."""
    return digest_quantity(value, argument, {"[L]": 1}, caller=caller,
                           message=LENGTH_MESSAGE)
