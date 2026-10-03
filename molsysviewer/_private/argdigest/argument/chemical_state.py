"""Accept a chemical-state selector; the provider resolves its meaning."""

import numpy as np

from ...exceptions import ArgumentError


def digest_chemical_state(chemical_state, caller=None):
    if chemical_state is None:
        return None
    if isinstance(chemical_state, str) and chemical_state.strip():
        return chemical_state.strip()
    if (
        isinstance(chemical_state, (int, np.integer))
        and not isinstance(chemical_state, (bool, np.bool_))
        and chemical_state >= 0
    ):
        return int(chemical_state)
    raise ArgumentError("chemical_state", value=chemical_state, caller=caller)
