"""The viewer's attribute-request boundary, derived from public MolSysMT metadata.

Attribute values remain MolSysMT's concern. Here a request flag must be a bool;
the scientific provider still validates and executes the resulting query.
"""

from molsysmt.attribute import attributes

from ..exceptions import ArgumentError
from .argument.element import digest_element
from .argument.get_missing_bonds import digest_get_missing_bonds
from .argument.mask import digest_mask
from .argument.output_type import digest_output_type
from .argument.selection import digest_selection
from .argument.skip_digestion import digest_skip_digestion
from .argument.structure_indices import digest_structure_indices
from .argument.syntax import digest_syntax


def _flag_validator(attribute):
    def validate(flag, caller=None):
        if isinstance(flag, bool):
            return flag
        raise ArgumentError(attribute, value=flag, caller=caller)

    return validate


def _chemical_state(chemical_state, caller=None):
    if chemical_state is None or isinstance(chemical_state, (str, int)) and not isinstance(chemical_state, bool):
        return chemical_state
    raise ArgumentError("chemical_state", value=chemical_state, caller=caller)


ARGUMENT_DIGESTERS = {name: _flag_validator(name) for name in attributes}
ARGUMENT_DIGESTERS.update(
    {
        "element": digest_element,
        "selection": digest_selection,
        "structure_indices": digest_structure_indices,
        "mask": digest_mask,
        "syntax": digest_syntax,
        "get_missing_bonds": digest_get_missing_bonds,
        "output_type": digest_output_type,
        "chemical_state": _chemical_state,
        "skip_digestion": digest_skip_digestion,
    }
)
