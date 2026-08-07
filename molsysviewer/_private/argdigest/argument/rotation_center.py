import numpy as np
from molsysviewer._pyunitwizard import puw
from ...exceptions import ArgumentError

def digest_rotation_center(rotation_center, caller=None):

    from .coordinates import digest_coordinates

    try:
        return digest_coordinates(rotation_center, caller=caller)
    except:
        raise ArgumentError('rotation_center', value=rotation_center, caller=caller, message=None)

