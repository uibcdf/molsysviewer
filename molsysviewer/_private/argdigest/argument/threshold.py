import numpy as np
from molsysviewer._pyunitwizard import puw
from ...exceptions import ArgumentError

common_functions_with_threshold = [
    'molsysmt.structure.get_contacts.get_contacts',
    'molsysmt.build.remove_overlapping_molecules.remove_overlapping_molecules',
]

common_functions_with_threshold_and_None = [
    'molsysmt.structure.get_neighbors.get_neighbors',
    'molsysmt.third_party.nglview.add_contacts.add_contacts',
]

def digest_threshold(threshold, caller=None):

    if isinstance(threshold, str):
        # MolSysMT lets pint's UndefinedUnitError escape here. This package's contract is
        # that a bad argument raises its own ArgumentError, so the parse is contained.
        try:
            threshold = puw.parse.parse(threshold)
        except Exception as exc:
            raise ArgumentError(
                'threshold', value=threshold, caller=caller, message=None,
            ) from exc

    if caller in common_functions_with_threshold:

        if puw.is_quantity(threshold):
            if puw.check(threshold, dimensionality={'[L]':1}):
                return puw.standardize(threshold)

    elif caller in common_functions_with_threshold_and_None:

        if threshold is None:
            return None

        if puw.is_quantity(threshold):
            if puw.check(threshold, dimensionality={'[L]':1}):
                return puw.standardize(threshold)

    raise ArgumentError('threshold', value=threshold, caller=caller, message=None)

