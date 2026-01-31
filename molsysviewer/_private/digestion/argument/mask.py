from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._private.variables import is_all
import numpy as np

def digest_mask(mask, caller=None):

    if caller in [
        'molsysmt.basic.select.select',
        'molsysmt.basic.get.get',
        'molsysviewer.viewer.MolSysView.select',
        'molsysviewer.viewer.MolSysView.get',
        'molsysviewer.viewer.MolSysView.info',
        'molsysviewer.regions.Region.select',
        'molsysviewer.regions.Region.get',
        'molsysviewer.regions.Region.info',
    ]:

        if mask is None:
            return mask
        elif isinstance(mask, (str, list, tuple, np.ndarray)):
            return mask
        elif is_all(mask):
            return 'all'

    else:

        if mask is None:
            return mask
        elif isinstance(mask, (list, tuple, np.ndarray)):
            return mask
        elif is_all(mask):
            return 'all'

    raise ArgumentError('mask', value=mask, caller=caller, message=None)
