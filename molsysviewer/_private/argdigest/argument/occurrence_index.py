import numpy as np

from ...exceptions import ArgumentError


def digest_occurrence_index(occurrence_index, caller=None):
    if (
        not isinstance(occurrence_index, (bool, np.bool_))
        and isinstance(occurrence_index, (int, np.integer))
        and occurrence_index >= 0
    ):
        return int(occurrence_index)
    raise ArgumentError("occurrence_index", value=occurrence_index, caller=caller)
