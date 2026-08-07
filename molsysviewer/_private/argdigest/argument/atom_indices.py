from ...exceptions import ArgumentError
from ...variables import is_all
from ..helpers import normalize_viewer_caller
import numpy as np

def digest_atom_indices(atom_indices, caller=None):
    """ Checks if atom_indices has the expected type and value.

    Parameters
    ----------
    indices : str or int or list or tuple or range.
        The indices

    caller: str, optional
        Name of the function or method that is being digested.
        For debugging purposes.

    Returns
    -------
    str or ndarray or None
        Either None, 'all' or an numpy array of integers with the indices.

    Raises
    -------
    ArgumentError
        If the given indices are not of the correct type.
    """

    caller = normalize_viewer_caller(caller)

    if atom_indices is None:
        return None
    elif is_all(atom_indices):
        if caller in {"molsysviewer.viewer.MolSysView.new_region", "molsysviewer.viewer.new_region"}:
            return None
        return 'all'
    elif isinstance(atom_indices, (int, np.int64, np.int32)):
        return np.array([atom_indices], dtype='int64')
    elif isinstance(atom_indices, (np.ndarray, list, tuple, range)):
        if all(isinstance(ii, (int, np.int64, np.int32)) for ii in atom_indices):
            return np.array(atom_indices, dtype='int64')
        else:
            return [digest_atom_indices(ii) for ii in atom_indices]

    raise ArgumentError('atom_indices', caller=caller, message=None)
