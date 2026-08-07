from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysviewer._pyunitwizard import puw

def digest_standard(standard, caller=None):

    if caller=='molsysmt.basic.view.view':
        if isinstance(standard, bool):
            return standard

    raise ArgumentError('standard', value=standard, caller=caller, message=None)

