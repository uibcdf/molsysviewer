import numpy as np
from molsysviewer._pyunitwizard import puw
from ...exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

def digest_force(force, caller=None):

    caller = normalize_viewer_caller(caller)

    if caller in {"molsysviewer.viewer.MolSysView.show", "molsysviewer.viewer.show"}:
        if isinstance(force, bool):
            return force

    if puw.is_quantity(force):
        if puw.check(force, dimensionality={'[L]':1, '[M]':1, '[T]':-2, '[mol]':-1}):
            return puw.standardize(force)

    raise ArgumentError('force', value=force, caller=caller, message=None)
