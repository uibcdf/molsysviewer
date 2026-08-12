from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysviewer._pyunitwizard import puw
from .._quantity import digest_length_quantity

def digest_center(center, syntax="MolSysMT", caller=None):
    """ Checks if a given center has the correct type and syntax

        Parameters
        ----------
        item : str or list of int
            An instance of one of the forms supported by MolSysMT.
        syntax : str, default="MolSysMT"
            Name of the syntax used in the center.
        caller: str, optional
            Name of the function or method that is being digested.

        Raises
        ------
        WrongSelectionError or WrongSelectionSyntaxError or WrongSyntaxError
            A WrongSelectionError is raised if the center object is not in deed a center.
            A WrongSelectionSyntaxError is raised if the center is not using the expected
            syntax.
            A WrongSyntaxError is raised if the syntax given is not in deed a syntax.

    """

    if caller=='molsysmt.basic.convert.convert':

        if syntax=='MolSysMT':
            if isinstance(center, str):
                return center
            elif isinstance(center, (int, np.int64, np.int32)):
                return np.array([center], dtype='int64')
            elif isinstance(center, (np.ndarray, list, tuple, range)):
                return np.array(center, dtype='int64')
            elif center is None:
                return None
        else:
            if isinstance(center, str):
                return center
            elif isinstance(center, (int, np.int64, np.int32)):
                return np.array([center], dtype='int64')
            elif isinstance(center, (np.ndarray, list, tuple, range)):
                return np.array(center, dtype='int64')
            elif center is None:
                return None

    elif caller=='molsysmt.structure.align_principal_axes.align_principal_axes':
        if isinstance(center, bool):
            return center

    elif caller is not None and caller.startswith("molsysviewer."):
        # In the viewer, a shape "center" is a physical position (single point or
        # a batch of points), so it must carry explicit length units — like
        # molsysmt's coordinates. Bare numbers are rejected.
        #
        # `None` is not a position: every viewer caller that takes one defaults to it,
        # meaning "the current camera target" or "the centroid of what is selected". The
        # branch had no case for it, so `movie.add_camera_orbit()` — called with no
        # arguments at all — was refused for its own default.
        if center is None:
            return None
        return digest_length_quantity(center, "center", caller=caller)

    raise ArgumentError('center', value=center, caller=caller, message=None)
