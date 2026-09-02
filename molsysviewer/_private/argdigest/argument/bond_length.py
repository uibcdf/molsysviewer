from molsysviewer._private.variables import is_iterable
from molsysviewer._pyunitwizard import puw

from ...exceptions import ArgumentError

# Synchronized with MolSysMT's digester of the same name on 2026-09-02. This directory is
# a copy of theirs, and this file had diverged into a broken version: `output = []` sat
# *inside* the loop, so only the last element survived, and the element check asked
# `puw.check(bond_length, ...)` about the whole list, which is always False. The branch
# could therefore never return successfully -- it rejected every list of quantities.
#
# It is unreachable from MolSysViewer, whose callers never end in `add_harmonic_bond_force`.
# Repaired rather than deleted so the copy stays faithful: today already cost this project
# the same defect twice in two places for the same reason, duplicated infrastructure
# drifting apart (uibcdf/molsysviewer#33).

functions_with_boolean = (
        )

functions_with_list_as_output = (
    'add_harmonic_bond_force',
        )

def digest_bond_length(bond_length, caller=None):

    if isinstance(bond_length, str):
        bond_length = puw.parse.parse(bond_length)

    if caller is not None:
        if caller.endswith(functions_with_list_as_output):
            if puw.is_quantity(bond_length):
                if puw.check(bond_length, dimensionality={'[L]':1}):
                    value, unit = puw.get_value_and_unit(bond_length)
                    if is_iterable(value):
                        return [puw.quantity(ii, unit, standardized=True) for ii in value]
                    else:
                        return puw.standardize(puw.quantity(value, unit))
            elif is_iterable(bond_length):
                output = []
                for aux in bond_length:
                    if puw.check(aux, dimensionality={'[L]':1}):
                        output.append(puw.standardize(aux))
                    else:
                        raise ArgumentError('bond_length', value=aux, caller=caller, message=None)
                return output

    if puw.is_quantity(bond_length):
        if puw.check(bond_length, dimensionality={'[L]':1}):
            return puw.standardize(bond_length)

    raise ArgumentError('bond_length', value=bond_length, caller=caller, message=None)
