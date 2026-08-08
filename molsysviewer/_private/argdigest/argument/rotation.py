import numpy as np
from molsysviewer._pyunitwizard import puw
from ...exceptions import ArgumentError

def digest_rotation(rotation, caller=None):

    if isinstance(rotation, (list, tuple)):
        rotation = np.array(rotation)

    if isinstance(rotation, np.ndarray):
        if rotation.shape == (3,3):
            return rotation[np.newaxis,np.newaxis,:,:]
        elif len(rotation.shape)==3 and rotation.shape[1:]==(3,3):
            return rotation[np.newaxis,:,:,:]
        elif len(rotation.shape)==4 and rotation.shape[2:]==(3,3):
            return rotation

    # Imported here, not at module level: ArgDigest loads every digester in this
    # package when it initializes, so a top-level import made any digested call pay
    # for a heavy library that most calls never need. SciPy is also not a declared
    # dependency of MolSysViewer, and it is reached only at this point, where the
    # argument is neither a sequence nor an array. An argument that is a SciPy
    # rotation implies SciPy is installed, so its absence can only mean this
    # argument is invalid, which is what the line below already says.
    try:
        from scipy.spatial.transform import Rotation
    except ImportError:
        pass
    else:
        if isinstance(rotation, Rotation):
            return rotation

    raise ArgumentError('rotation', value=rotation, caller=caller, message=None)


