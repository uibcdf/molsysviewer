import numpy as np
from molsysviewer._private.exceptions import ArgumentError

def digest_chunk(chunk, caller=None):

    if isinstance(chunk, (int, np.int64, np.int32)):
        return chunk

    raise ArgumentError('chunk', value=chunk, caller=caller, message=None)

