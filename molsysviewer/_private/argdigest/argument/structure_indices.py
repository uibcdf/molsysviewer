import numpy as np

from ...exceptions import ArgumentError
from ...variables import is_all


def digest_structure_indices(structure_indices, caller=None):
    """Checks if atom_indices has the expected type and value.

    Parameters
    ----------
    structure_indices : str or int or list or tuple or range.
        The structure indices.

    caller: str, optional
        Name of the function or method that is being digested.
        For debugging purposes.

    Returns
    -------
    str or ndarray or None
        Either None, 'all' or an numpy array of integers with the indices.

    Raises
    -------
    WrongIndicesError
        If the given structure_indices has not of the correct type.
    """

    from ..helpers import normalize_viewer_caller

    if normalize_viewer_caller(caller) == "molsysviewer.viewer.load":
        from molsysviewer.loaders._composition import _index_selector

        if isinstance(structure_indices, (list, tuple, np.ndarray)) and any(
            isinstance(item, (str, list, tuple, np.ndarray, range)) for item in structure_indices
        ):
            return [digest_structure_indices(item, caller=caller) for item in structure_indices]
        return _index_selector(structure_indices, "structure_indices")

    if caller and caller.startswith("molsysviewer.interactions."):
        if isinstance(structure_indices, str) and structure_indices == "current":
            return structure_indices
        if structure_indices is not None and not is_all(structure_indices):
            # Validate before the common digester can coerce bool indices to int.
            from molsysviewer.interactions import _indices

            return _indices(
                structure_indices, np.iinfo(np.int64).max, "structure_indices", unique=not caller.endswith(".load")
            )

    if caller and caller.endswith((".partial_coordinates_update", ".set_coordinates", ".set_box")):
        if structure_indices is not None and not is_all(structure_indices):
            from molsysviewer.interactions import _indices

            return _indices(structure_indices, np.iinfo(np.int64).max, "structure_indices", unique=False)

    if structure_indices is None:
        return None
    elif is_all(structure_indices):
        return "all"
    elif isinstance(structure_indices, (int, np.int64, np.int32)):
        return np.array([structure_indices], dtype="int64")
    elif isinstance(structure_indices, (np.ndarray, list, tuple, range)):
        if all(isinstance(ii, (int, np.int64, np.int32)) for ii in structure_indices):
            return np.array(structure_indices, dtype="int64")
        else:
            return [digest_structure_indices(ii) for ii in structure_indices]

    raise ArgumentError("structure_indices", caller=caller, message=None)
