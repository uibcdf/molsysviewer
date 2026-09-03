import numpy as np
from molsysviewer._pyunitwizard import puw
from ...exceptions import ArgumentError

common_functions_with_distance_threshold = [
    'molsysmt.hbonds.get_buch_hbonds.get_buch_hbonds',
    'molsysmt.hbonds.get_luzard_chandler_hbonds.get_luzard_chandler_hbonds',
]

common_functions_with_distance_threshold_and_None = [
]

def digest_distance_threshold(distance_threshold, caller=None):

    if isinstance(distance_threshold, str):
        # MolSysMT lets pint's UndefinedUnitError escape here. This package's contract is
        # that a bad argument raises its own ArgumentError, so the parse is contained.
        try:
            distance_threshold = puw.parse.parse(distance_threshold)
        except Exception as exc:
            raise ArgumentError(
                'distance_threshold', value=distance_threshold, caller=caller, message=None,
            ) from exc

    if caller in common_functions_with_distance_threshold:

        if puw.is_quantity(distance_threshold):
            if puw.check(distance_threshold, dimensionality={'[L]':1}):
                return puw.standardize(distance_threshold)

    elif caller in common_functions_with_distance_threshold_and_None:

        if distance_threshold is None:
            return None

        if puw.is_quantity(distance_threshold):
            if puw.check(distance_threshold, dimensionality={'[L]':1}):
                return puw.standardize(distance_threshold)

    raise ArgumentError('distance_threshold', value=distance_threshold, caller=caller, message=None)

