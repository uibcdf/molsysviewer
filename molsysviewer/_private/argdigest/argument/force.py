"""`force` is a force per mole, except where a caller uses the name to mean "do it anyway".

`show(force=True)` is a boolean: same name, unrelated question, decided by the caller.
Everywhere else it is `[L][M][T]^-2[mol]^-1` and goes through the shared boundary, which
is the same instrument every length uses rather than a second hand-rolled
`is_quantity -> check -> standardize` sequence (uibcdf/molsysviewer#86).
"""

from .._quantity import FORCE_DIMENSIONALITY, digest_quantity
from ..helpers import normalize_viewer_caller

_MESSAGE = (" A force requires explicit units (e.g. \"5 kilojoule/(mol*nanometer)\"); "
            "bare numbers are not accepted.")


def digest_force(force, caller=None):
    caller = normalize_viewer_caller(caller)

    if caller in {"molsysviewer.viewer.MolSysView.show", "molsysviewer.viewer.show"}:
        if isinstance(force, bool):
            return force

    return digest_quantity(force, "force", FORCE_DIMENSIONALITY, caller=caller,
                           message=_MESSAGE)
